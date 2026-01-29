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
from collections import defaultdict
from collections.abc import Collection, Iterable
from datetime import datetime, timedelta
from functools import cached_property
from itertools import chain
from time import perf_counter
from typing import Any

import pytz
from rich import print
from LHCbDIRAC.BookkeepingSystem.Client.BookkeepingClient import BookkeepingClient
from LHCbDIRAC.ProductionManagementSystem.Client.AnalysisProductionsClient import AnalysisProductionsClient
from LHCbDIRAC.ProductionManagementSystem.Client.ProductionRequestClient import ProductionRequestClient
from LHCbDIRAC.TransformationSystem.Client.TransformationClient import TransformationClient

from .constants import ACTIVE_TRANSFORMATION_STATES
from ..LogAnalysis.utils import call_dirac
from .models import APTransformDebugInfo, APRequestDebugInfo, APDebugInfo, APBaseDebugInfo


async def get_active_productions():
    print("Getting active productions")
    start = perf_counter()
    result = await call_dirac(
        ProductionRequestClient().getProductionRequestList,
        0,  # Parent
        "RequestID",  # Sortby
        "DESC",  # Sort order
        0,  # Offset
        0,  # Max results
        {
            "RequestType": "AnalysisProduction",
            "RequestState": ",".join(["New", "Accepted", "Active", "PPG OK", "Submitted", "Tech OK"]),
        },
    )
    print(f"Got {result['Total']} active productions in {perf_counter() - start:.2f} seconds")
    return {x["RequestID"]: x for x in result["Rows"]}


async def get_ap_requests():
    print("Getting analysis production requests")
    start = perf_counter()
    result = await call_dirac(AnalysisProductionsClient().listRequests)
    print(f"Got {len(result)} analysis production requests in {perf_counter() - start:.2f} seconds")
    return result


async def get_archived_ap_requests():
    print("Getting archived analysis production requests")
    start = perf_counter()
    result = await call_dirac(AnalysisProductionsClient().getArchivedRequests)
    print(f"Got {len(result)} archived analysis production requests in {perf_counter() - start:.2f} seconds")
    return result


class Transforms:
    @classmethod
    async def from_transform_ids(cls, request_ids: Iterable[int], progress):
        print(f"Getting transformation info for {len(request_ids)} production requests")
        start = perf_counter()
        result = await call_dirac(
            TransformationClient().getTransformations,
            {"TransformationFamily": list(request_ids)},
            columns=[
                "TransformationID",
                "TransformationFamily",
                "Type",
                "Status",
                "GroupSize",
            ],
        )
        print(
            f"Got info for {len(result)} transforms from {len(request_ids)} requests in {perf_counter() - start:.2f} seconds"
        )
        for transform in result:
            transform["TransformationFamily"] = int(transform["TransformationFamily"])
        self = cls(result)
        await self._find_input_info()
        return self

    def __init__(self, transforms):
        self._by_id = {x["TransformationID"]: x for x in transforms}

    @cached_property
    def by_id(self):
        result = {}
        for transform_id, dict_data in self._by_id.items():
            result[transform_id] = APTransformDebugInfo(
                transform_id=transform_id,
                state=dict_data["Status"],
                type=dict_data["Type"],
                group_size=dict_data["GroupSize"],
                # file_counts=self._file_counts[transform_id],
                active_inputs=self._active_inputs[transform_id],
            )
        return result

    @cached_property
    def id_to_family(self):
        result = {}
        for transform_id, dict_data in self._by_id.items():
            result[transform_id] = dict_data["TransformationFamily"]
        return result

    @cached_property
    def by_family(self):
        result = defaultdict(list)
        for transform_id, dict_data in self._by_id.items():
            result[dict_data["TransformationFamily"]].append(transform_id)
        return {k: sorted(v) for k, v in result.items()}

    async def _find_input_info(self) -> None:
        print(f"Getting input queries for {len(self._by_id)} active productions")
        start = perf_counter()
        input_queries = await call_dirac(
            TransformationClient().getBookkeepingQueries,
            sorted(self._by_id),
        )
        print(f"Got input queries in {perf_counter() - start:.2f} seconds")
        result: dict[int, set[int]] = {}
        to_check = {}
        for tid, query in input_queries.items():
            if in_prods := query.get("ProductionID", []):
                if isinstance(in_prods, int):
                    in_prods = [in_prods]
                active_in_prods = {
                    in_prod
                    for in_prod in in_prods
                    if in_prod in self._by_id and self._by_id[in_prod]["Status"] in ACTIVE_TRANSFORMATION_STATES
                }
                if active_in_prods:
                    # The input transformation is active, no need to check the bookkeeping
                    result[tid] = active_in_prods
                    continue
            to_check[hash_dict(query)] = query

        async def get_input_productions(input_query):
            if "ProductionID" in input_query:
                return [input_query["ProductionID"]]
            result = await call_dirac(BookkeepingClient().getProductions, input_query)
            return [x[0] for x in result["Records"]]

        print(f"Getting production IDs for {len(to_check)} unique queries")
        start = perf_counter()
        async with asyncio.TaskGroup() as tg:
            tasks = {k: tg.create_task(get_input_productions(v)) for k, v in to_check.items()}
            input_ids_by_hash = {k: await v for k, v in tasks.items()}
            end = perf_counter()
            print(f"Got production IDs from queries in {end - start:.2f} seconds")

        input_ids = list(chain(*input_ids_by_hash.values()))
        print(f"Getting transform info for {len(input_ids)} IDs")
        start = perf_counter()
        transforms_info = await call_dirac(
            TransformationClient().getTransformations,
            condDict={"TransformationID": sorted(set(input_ids))},
            limit=10000,
            columns=["TransformationID", "TransformationFamily", "Status", "Type"],
        )
        transforms_info = {x["TransformationID"]: x for x in transforms_info}
        end = perf_counter()
        print(f"Got transform info in {end - start:.2f} seconds")

        for tid, query in input_queries.items():
            if tid in result:
                # The input transformation is an AP and we already checked it
                continue
            input_ids = input_ids_by_hash[hash_dict(query)]
            result[tid] = {
                input_tid
                for input_tid in input_ids_by_hash[hash_dict(query)]
                if input_tid > 0
                and transforms_info[input_tid]["Status"] in ACTIVE_TRANSFORMATION_STATES
                and not query.get("EndDate")
            }
        self._active_inputs = result

    async def find_file_counts(self, transform_ids: Collection[int], progress) -> None:
        ptask = progress.add_task("Getting file counts", total=len(transform_ids))

        async def get_files_count(tid):
            """In Python 3.13 this can be replaced with `async for task in as_completed...`"""
            return tid, await call_dirac(TransformationClient().getTransformationFilesCount, tid, "Status")

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(get_files_count(tid)) for tid in transform_ids]
            for task in asyncio.as_completed(tasks):
                tid, file_counts = await task
                self.by_id[tid].file_counts = file_counts
                progress.update(ptask, advance=1)


def hash_dict(d: dict[str, Any]) -> int:
    items = []
    for k, v in d.items():
        if isinstance(v, dict):
            v = hash_dict(v)
        elif isinstance(v, list):
            v = frozenset(v)
        elif not isinstance(v, (int, str)):
            raise NotImplementedError(v, type(v))
        items.append((k, v))
    return hash(frozenset(items))


async def get_ap_info(wg, analysis, version) -> APDebugInfo:
    from LHCbDIRAC.ProductionManagementSystem.Client.AnalysisProductionsClient import (
        AnalysisProductionsClient,
    )

    aps = await call_dirac(
        AnalysisProductionsClient().getProductions,
        wg=wg,
        analysis=analysis,
        version=version,
        with_lfns=False,
        with_pfns=False,
        with_transformations=False,
    )
    urls = {ap.get("jira_task") for ap in aps}
    if len(urls) != 1:
        raise NotImplementedError(urls)
    validity_start = min(ap["validity_start"] for ap in aps)

    return APDebugInfo(
        wg=wg,
        analysis=analysis,
        version=version,
        created=validity_start.astimezone(pytz.timezone("Europe/Zurich")),
        issue_url=urls.pop(),
    )


async def get_raw_ap_infos(
    active_request_ids: Iterable[int], requests, progress
) -> dict[tuple[str, str, str] : APDebugInfo]:
    # Deduplicate the analyses
    keys = {
        (wg, analysis, request["version"])
        for request in requests
        for wg, analysis in request["analyses"]
        if request["request_id"] in active_request_ids
    }
    # Get the APDebugInfo objects in parallel
    result = {}
    ptask = progress.add_task("Getting AP info", total=len(keys))
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(get_ap_info(wg, analysis, version)) for wg, analysis, version in keys]
        for task in asyncio.as_completed(tasks):
            ap = await task
            result[(ap.wg, ap.analysis, ap.version)] = ap
            progress.update(ptask, advance=1)
    return result


class LiveAPInfo:
    @classmethod
    async def load(cls, progress):
        async with asyncio.TaskGroup() as tg:
            active_productions = tg.create_task(get_active_productions())
            requests = tg.create_task(get_ap_requests())
            archived_requests = tg.create_task(get_archived_ap_requests())
            # active_productions = await active_productions
            transforms = tg.create_task(Transforms.from_transform_ids(await active_productions, progress))
            # requests = await requests
            raw_ap_infos = get_raw_ap_infos(await active_productions, await requests, progress)
        return cls(
            active_productions=await active_productions,
            requests=await requests,
            archived_requests=await archived_requests,
            transforms=await transforms,
            raw_ap_infos=await raw_ap_infos,
        )

    def __init__(
        self,
        active_productions,
        requests,
        archived_requests,
        transforms: Transforms,
        raw_ap_infos: dict[tuple[str, str, str], APDebugInfo],
    ):
        self._active_productions = active_productions
        self._requests = requests
        self._archived_requests = archived_requests
        self.transforms = transforms
        self._raw_ap_infos = raw_ap_infos
        self._handle_pending()

    @cached_property
    def request_id_to_ap_keys(self) -> dict[int, set[tuple[str, str, str]]]:
        return {
            request["request_id"]: {(wg, analysis, request["version"]) for wg, analysis in request["analyses"]}
            for request in self._requests
        }

    @cached_property
    def missing(self) -> set[int]:
        """If requests are missing in the AnalysisProductionsDB then something is wrong"""
        result = set(self._active_productions)
        result -= set(self.request_id_to_ap_keys)
        result -= {r.request_id for a in self.archived_requests for r in a.requests}
        return result

    def _handle_pending(self):
        recent: dict[tuple[str, str, str], APDebugInfo] = {}
        stuck: dict[tuple[str, str, str], APDebugInfo] = {}

        timezone = pytz.timezone("Europe/Zurich")
        now = datetime.now(timezone)
        for prod in self._active_productions.values():
            if prod["RequestState"] == "Active":
                continue
            time_since_created = now - prod["crTime"].astimezone(timezone)
            result = recent if time_since_created < timedelta(hours=6) else stuck
            request_id = prod["RequestID"]
            if request_id in self.missing:
                continue
            for key in self.request_id_to_ap_keys[request_id]:
                if key not in result:
                    result[key] = self._raw_ap_infos[key].model_copy(deep=True)
                request_info = APRequestDebugInfo(
                    request_id=request_id,
                    transforms=[self.transforms.by_id[x] for x in self.transforms.by_family.get(request_id, [])],
                )
                result[key].requests.append(request_info)

        for transform in self.transforms.by_id.values():
            if transform.state in {"PPG_OK", "New"}:
                request_id = self.transforms.id_to_family[transform.transform_id]
                for key in self.request_id_to_ap_keys[request_id]:
                    if key not in stuck:
                        stuck[key] = self._raw_ap_infos[key].model_copy(deep=True)
                    request_info = APRequestDebugInfo(
                        request_id=request_id,
                        transforms=[self.transforms.by_id[x] for x in self.transforms.by_family.get(request_id, [])],
                    )
                    stuck[key].requests.append(request_info)

        self.recent = sorted(recent.values(), key=lambda x: x.created)
        self.stuck = sorted(stuck.values(), key=lambda x: x.created)

    @cached_property
    def archived_requests(self) -> list[APBaseDebugInfo]:
        by_version = {}
        for request in self._archived_requests:
            request_id = request["request_id"]
            if request_id not in self._active_productions:
                continue
            if request["version"] not in by_version:
                by_version[request["version"]] = APBaseDebugInfo(
                    version=request["version"], issue_url=request["jira_task"]
                )
            request_info = APRequestDebugInfo(
                request_id=request_id,
                transforms=[self.transforms.by_id[x] for x in self.transforms.by_family[request_id]],
            )
            by_version[request["version"]].requests.append(request_info)
        return sorted(by_version.values(), key=lambda x: x.version)

    @cached_property
    def active(self):
        by_ap_key = {}
        to_skip = self.missing | {r.request_id for a in self.archived_requests for r in a.requests}
        for prod in self._active_productions.values():
            if prod["RequestState"] != "Active":
                continue
            request_id = prod["RequestID"]
            if request_id in to_skip:
                continue
            for key in self.request_id_to_ap_keys[request_id]:
                if key not in by_ap_key:
                    by_ap_key[key] = self._raw_ap_infos[key].model_copy(deep=True)
                request = APRequestDebugInfo(
                    request_id=request_id,
                    transforms=[self.transforms.by_id[x] for x in self.transforms.by_family[request_id]],
                )
                by_ap_key[key].requests.append(request)
        return sorted(by_ap_key.values(), key=lambda x: x.created)
