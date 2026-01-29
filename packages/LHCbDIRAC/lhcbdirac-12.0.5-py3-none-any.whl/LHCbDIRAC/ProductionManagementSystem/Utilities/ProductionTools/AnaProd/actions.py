###############################################################################
# (c) Copyright 2024 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
from __future__ import annotations

import asyncio
import base64
import os
import ssl
import tempfile
from collections import defaultdict
from contextlib import asynccontextmanager
from itertools import chain
from typing import Annotated, Union, Literal

import httpx
import zstandard
from pydantic import RootModel, BaseModel, Field, ValidationError, ConfigDict
from rich.prompt import Prompt, Confirm
from rich import print

from DIRAC import gConfig
from DIRAC.Core.Utilities.ReturnValues import returnValueOrRaise
from LHCbDIRAC.DataManagementSystem.Client.ConsistencyChecks import ConsistencyChecks
from LHCbDIRAC.DataManagementSystem.Client.ScriptExecutors import removeReplicas
from LHCbDIRAC.TransformationSystem.Client.TransformationClient import TransformationClient
from LHCbDIRAC.TransformationSystem.Utilities.PluginUtilities import addFilesToTransformation

from .gitlab import APRepoIssue
from ..LogAnalysis.prod_analyzer import GroupedProblems, AggregatedLFNDebugInfo
from ..LogAnalysis.utils import call_dirac
from ..LogAnalysis.output import make_problems_table


def clean_lfns(lfns: list[str]) -> list[str]:
    return [lfn[4:] if lfn.startswith("LFN:") else lfn for lfn in lfns]


def get_all_subclasses(cls):
    subclasses = set()
    work = [cls]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return tuple(subclasses)


def build_action_union():
    subclasses = get_all_subclasses(BaseAction)
    return Union[tuple(subclasses)]


class BaseAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_name: str
    _log_lines: list[str] = []

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__annotations__["action_name"] = f"{Literal.__name__}[{cls.__name__!r}]"
        cls.action_name = cls.__name__
        cls.model_rebuild()

    async def run(self, overview):
        raise NotImplementedError()

    def log(self, message):
        self._log_lines.append(message)
        print(f"{self.__class__.__name__}:{message}")


class BaseTransformAction(BaseAction):
    transform_id: int

    def log(self, message):
        self._log_lines.append(message)
        print(f"{self.transform_id}:{self.__class__.__name__}:{message}")


class ReduceGroupSizeAction(BaseTransformAction):

    async def run(self, overview):
        self.log(f"Reducing group size for {self.transform_id}")
        await call_dirac(TransformationClient().setTransformationParameter, self.transform_id, "GroupSize", 1)


class SetDownloadInputDataAction(BaseTransformAction):

    async def run(self, overview):
        by_protocol_plugin_name = "DIRAC.WorkloadManagementSystem.Client.InputDataByProtocol"
        download_plugin_name = "DIRAC.WorkloadManagementSystem.Client.DownloadInputData"

        self.log(f"Setting download input data for {self.transform_id}")
        body = await call_dirac(TransformationClient().getTransformationParameters, self.transform_id, "Body")
        if download_plugin_name not in body:
            if body.count(by_protocol_plugin_name) != 1:
                raise NotImplementedError(self)
            body = body.replace(by_protocol_plugin_name, download_plugin_name)
            await call_dirac(TransformationClient().setTransformationParameter, self.transform_id, "Body", body)


class ResetFileStatusAction(BaseTransformAction):
    transform_id: int
    lfns_to_reset: Annotated[set[str], Field(min_length=1)]
    new_status: str = "Unused"

    async def run(self, overview):
        lfns = sorted(set(clean_lfns(self.lfns_to_reset)))
        self.log(f"Resetting {len(lfns)} in {self.transform_id}")
        query = {
            "TransformationID": self.transform_id,
            "LFN": lfns,
        }
        result = await call_dirac(
            TransformationClient().getTransformationFiles, condDict=query, columns=["TransformationID", "LFN", "Status"]
        )
        if {x["LFN"] for x in result} != set(lfns):
            raise NotImplementedError(self, result)
        if not all(x["Status"] in {"MaxReset", "Problematic"} for x in result):
            raise NotImplementedError(self, result)
        result = await call_dirac(
            TransformationClient().setFileStatusForTransformation, self.transform_id, self.new_status, lfns, force=True
        )
        for lfn, lfn_new_status in result.items():
            self.log(f"Set status for {lfn} to {lfn_new_status}")
        if not_updated := set(lfns) - set(result):
            raise NotImplementedError(self, not_updated)


class PostAPIssueDiscussion(BaseAction):
    ap_key: tuple[str, str, str]
    body: Annotated[str, Field(max_length=900_000)]
    attachments: dict[str, str] = {}

    async def run(self, overview):
        ap = overview.key_to_ap[self.ap_key]
        issue = APRepoIssue(overview.repo.get_issue(ap.issue_url))
        format_kwargs = {}
        for name, content in self.attachments.items():
            uploaded_file = overview.repo.project.upload(name, filedata=content)
            format_kwargs[name.replace(".", "_")] = uploaded_file["url"]
        if format_kwargs:
            self.body = self.body.format(**format_kwargs)
        discussion = issue.discussions.create({"body": self.body})
        self.log(f"Posted discussion to {ap.issue_url} as {discussion.get_id()}")


class RequestFeedbackAction(BaseTransformAction):
    description: str
    instances: list[AggregatedLFNDebugInfo]
    reset_action: AnyAction
    abort_action: AnyAction

    async def run(self, overview):
        request_id = overview.transform_id_to_request_id[self.transform_id]
        aps = overview.request_id_to_aps[request_id]
        ap = sorted(aps, key=lambda x: x.created)[0]
        issue = APRepoIssue(overview.repo.get_issue(ap.issue_url))
        lfns = sorted([x.lfn for x in self.instances])

        for discussion_id, compressed_info in issue.metadata.open_discussions.items():
            info = RequestFeedbackAction.model_validate_json(zstandard.decompress(base64.b64decode(compressed_info)))
            if info.transform_id != self.transform_id:
                continue
            info_lfns = {x.lfn for x in info.instances}
            if not info_lfns.issubset(lfns):
                continue
            if info_lfns != set(lfns):
                raise NotImplementedError(self, issue, info_lfns, lfns)
            await self._prompt_for_action(overview, issue, discussion_id)
            break
        else:
            self._post_discussion(ap, issue, lfns)

    def _post_discussion(self, ap, issue, lfns):
        body = []
        body.append("Please investigate the following problems and decide if you")
        body.append("would like to skip processing these files.")
        body.append("")
        body.append(self.description)
        body.append("")
        body.append("<details><summary>Click to show details</summary>")
        body.append("")
        body.extend(make_problems_table(self.instances, is_summary=True))
        body.append("")
        body.append("</details>")
        body = "\n".join(body)
        discussion = issue.discussions.create({"body": body})
        self.log(f"Posted discussion to {ap.issue_url} as {discussion.get_id()}")

        issue.labels.append("Needs investigation")
        issue.metadata.open_discussions[discussion.get_id()] = base64.b64encode(
            zstandard.compress(self.model_dump_json().encode())
        ).decode()
        issue.update_metadata()

    async def _prompt_for_action(self, overview, issue, discussion_id):
        note_id = issue.discussions.get(discussion_id).attributes["notes"][0]["id"]
        print(f"Discussion at {issue.url}#note_{note_id}")
        match choice := Prompt.ask(
            "What would you like to do?", choices=["Reset", "Abort", "Nothing"], default="Nothing"
        ):
            case "Reset":
                print("Running reset action")
                await self.reset_action.run(overview)
            case "Abort":
                print("Running abort action")
                await self.abort_action.run(overview)
            case "Nothing":
                return
            case _:
                raise NotImplementedError(choice)

        issue.metadata.open_discussions.pop(discussion_id)
        if not issue.metadata.open_discussions:
            issue.labels.remove("Needs investigation")
        issue.update_metadata()


class SetTransformStateAction(BaseTransformAction):
    state: Literal["Stopped"] | Literal["Completed"] | Literal["Flush"]

    async def run(self, overview):
        self.log(f"Setting state to {self.state}")
        await call_dirac(
            TransformationClient().setTransformationParameter, self.transform_id, "Status", self.state, force=True
        )


class AddLFNsToReplicationTransform(BaseAction):
    lfns: list[str]
    se_name: str

    async def run(self, overview):
        self.log(f"Adding {len(self.lfns)} LFNs to {self.se_name}")
        transform_name = f"Replicate-to-{self.se_name}"
        replication_transform = returnValueOrRaise(TransformationClient().getTransformation(transform_name))
        replication_transform_id = replication_transform["TransformationID"]
        result = returnValueOrRaise(
            addFilesToTransformation(replication_transform_id, self.lfns, addRunInfo=True, resetPresentFiles=True)
        )
        if result["Failed"]:
            raise NotImplementedError(self, result["Failed"])
        self.log(f"Added {len(self.lfns)} LFNs to {transform_name} ({replication_transform_id}): {self.lfns}")


class HandleInputDataResolutionFailureAction(BaseAction):
    transform_id_to_lfns: dict[int, list[str]]

    async def run(self, overview):
        # Prompt for if this should be ran
        if not Confirm.ask(f"Do input data resolution checks for {len(self.transform_id_to_lfns)} transforms?"):
            self.log("Skipping handling input data resolution failure")
            return

        lfns = clean_lfns(sorted(set(chain(*self.transform_id_to_lfns.values()))))
        self.log(f"Handling input data resolution failure for {len(lfns)} LFNs in {sorted(self.transform_id_to_lfns)}")
        cc = ConsistencyChecks()
        cc.lfns = lfns
        cc.checkFC2SE(bkCheck=True)

        lost_lfns = set()
        post_logbook = False
        okay_lfns = set(lfns)

        if cc.notRegisteredAtSE:
            okay_lfns -= set(cc.notRegisteredAtSE)
            raise NotImplementedError(self)

        if cc.existLFNsBKRepNo:
            okay_lfns -= set(cc.existLFNsBKRepNo)
            raise NotImplementedError(self)

        if cc.existLFNsNotInBK:
            okay_lfns -= set(cc.existLFNsNotInBK)
            raise NotImplementedError(self)

        if cc.existLFNsBadFiles or cc.existLFNsNotExisting:
            okay_lfns -= set(cc.existLFNsBadFiles) | set(cc.existLFNsNotExisting)
            raise NotImplementedError(self)

        if cc.existLFNsBadReplicas:
            okay_lfns -= set(cc.existLFNsBadReplicas)
            raise NotImplementedError(self)

        if cc.existLFNsNoSE:
            okay_lfns -= set(cc.existLFNsNoSE)
            by_se = defaultdict(set)
            # Group them by SE
            for lfn, ses in cc.existLFNsNoSE.items():
                for se in ses:
                    if se == "All":
                        raise NotImplementedError(self)
                    by_se[se].add(lfn)
            # Remove the replicas
            for se, se_lfns in by_se.items():
                se_lfns = sorted(se_lfns)
                self.log(f"Removing {len(se_lfns)} LFNs from {se}: {se_lfns}")
                return_code, error_reasons = removeReplicas(se_lfns, [se])
                if return_code != 0:
                    raise NotImplementedError(self, return_code, error_reasons)
                if error_reasons:
                    raise NotImplementedError(self, return_code, error_reasons)
                await AddLFNsToReplicationTransform(se_name=se, lfns=se_lfns).run(overview)
            post_logbook = True

        # If we have some LFNs that seem to be okay, double-check by downloading
        # a small part of the file to make sure the server containing the file
        # is actually reachable and the file is readable.
        if okay_lfns:
            from DIRAC.Core.Utilities.ReturnValues import returnValueOrRaise
            from DIRAC.Core.Security.Locations import getCAsLocation, getProxyLocation
            from DIRAC.DataManagementSystem.Client.DataManager import DataManager

            replicas = returnValueOrRaise(DataManager().getReplicas(lfns, diskOnly=True, protocol="https"))
            if replicas["Failed"]:
                raise NotImplementedError(f"Failed to get some replicas {replicas['Failed']}")

            ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, capath=getCAsLocation())
            ctx.load_cert_chain(getProxyLocation())

            errored_lfns = dict()
            tasks = defaultdict(list)
            # When storage is misbehaving, checking replicas can be extremely
            # slow due to timeouts so do the checks in parallel.
            async with httpx.AsyncClient(timeout=90, verify=ctx, follow_redirects=True) as client:
                async with asyncio.TaskGroup() as tg:
                    for lfn, lfn_replicas in replicas["Successful"].items():
                        assert len(lfn_replicas) > 0
                        any_replica_okay = False
                        for se, pfn in lfn_replicas.items():
                            coro = check_replica_worker(self.log, client, lfn, pfn, se, errored_lfns)
                            tasks[lfn].append(tg.create_task(coro))

            # Gather the results and see if any replica was okay for each LFN
            for lfn, lfn_replicas in replicas["Successful"].items():
                any_replica_okay = any(t.result() for t in tasks[lfn])
                if not any_replica_okay:
                    okay_lfns.remove(lfn)
            if errored_lfns and Confirm.ask(
                f"Some LFNs had all replicas unreachable ({len(errored_lfns)} SEs). Make logbook entry?"
            ):
                subject = "Consistency checks okay but replicas unreachable"
                body = "The following LFNs had all replicas unreachable:\n\n"
                for se, se_lfns in errored_lfns.items():
                    body += f"### {se}\n\n"
                    for lfn, (code, reason) in se_lfns.items():
                        body += f"- {lfn}: {code} {reason[:200]!r}\n"
                    body += "\n"
                body += f"\n\n{self.model_dump_json(indent=2)}"
                overview.logbook.create_post(
                    "", list(self.transform_id_to_lfns), subject, body, {}, ["Data Management", "WGP"]
                )

        lfns_to_skip = {f"LFN:{lfn}" for lfn in sorted(chain(*errored_lfns.values()))}
        for transform_id, transform_lfns in self.transform_id_to_lfns.items():
            transform_lfns = sorted(set(transform_lfns) - lost_lfns - lfns_to_skip)
            if transform_lfns:
                self.log(f"Resetting {len(transform_lfns)} LFNs Unused in {transform_id}: {transform_lfns}")
                await ResetFileStatusAction(transform_id=transform_id, lfns_to_reset=transform_lfns).run(overview)

        if post_logbook:
            subject = "Handling InputDataResolutionFailure for AP"
            body = "\n".join(self._log_lines)
            body += f"\n\n{self.model_dump_json(indent=2)}"
            overview.logbook.create_post(
                "", list(self.transform_id_to_lfns), subject, body, {}, ["Data Management", "WGP"]
            )


async def check_replica_worker(log, client, lfn, pfn, se, errored_lfns):
    try:
        async with client.stream("GET", pfn, headers={"Range": "bytes=0-32"}) as response:
            if response.status_code >= 400:
                log(f"Error {response.status_code} from {pfn}: {await response.aread()}")
                errored_lfns.setdefault(se, {})[lfn] = (response.status_code, await response.aread())
                return False
            total = int(response.headers.get("Content-Length", 0))
            log(f"Got {total} bytes from {pfn}")
            data = await response.aread()
            assert data
            return True
    except Exception as e:
        log(f"Exception from {pfn}: {e!r}")
        errored_lfns.setdefault(se, {})[lfn] = (type(e).__name__, str(e))
        return False


@asynccontextmanager
async def get_admin_proxy_path():
    with tempfile.NamedTemporaryFile("w") as f:
        while True:
            if hasattr(get_admin_proxy_path, "__password"):
                password = get_admin_proxy_path.__password
            else:
                password = Prompt.ask("Enter certificate password", password=True)
            cmd = ["dirac-proxy-init", "-g", "lhcb_admin", "--pwstdin", "--out", f.name]
            print(f"Creating admin proxy using {cmd}")
            proc = await asyncio.create_subprocess_exec(*cmd, stdin=asyncio.subprocess.PIPE)
            await proc.communicate(password.encode())
            if proc.returncode == 0:
                break
            print("Failed to create proxy, try again")
            delattr(get_admin_proxy_path, "__password")
        yield f.name
    get_admin_proxy_path.__password = password


class SendToHospital(BaseAction):
    transform_ids: list[int]

    async def run(self, overview):
        await call_dirac(gConfig.forceRefresh)

        cs_section_name = "/Operations/Defaults/Hospital/Clinics/AP/Transformations"
        original_tids = set(map(int, returnValueOrRaise(gConfig.getOption(cs_section_name, []))))
        new_tids = sorted(original_tids | set(self.transform_ids))
        if set(new_tids) == original_tids:
            return
        async with get_admin_proxy_path() as proxy_path:
            proc = await asyncio.create_subprocess_exec(
                "lb-dirac",
                "dirac-configuration-cli",
                stdin=asyncio.subprocess.PIPE,
                env=os.environ | {"X509_USER_PROXY": proxy_path},
            )
            commands = [
                f"set {cs_section_name} {','.join(map(str, new_tids))}",
                "showDiffWithServer",
                "writeToServer",
                "yes",
            ]
            await proc.communicate("\n".join(commands).encode())
            if proc.returncode != 0:
                raise NotImplementedError(self, proc.returncode)


AnyAction = Annotated[build_action_union(), Field(discriminator="action_name")]


class ActionsList(RootModel):
    root: dict[str, list[AnyAction]]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)

    def items(self):
        return self.root.items()
