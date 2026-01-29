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

__all__ = [
    "LogFileMatch",
    "LogFileMatches",
    "AppLogFailureReason",
    "Job",
    "PreAnalysisResult",
    "LFNDebugInfo",
    "AggregatedLFNDebugInfo",
]

import ast
import re
from enum import auto, StrEnum
from typing import Self
from functools import partial, cached_property
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, field_validator

from .classes import JobArtifacts, JobArtifactConsistencyError
from .base_reasons import (
    LogFileMatches,
    LogFileMatch,
    AppLogFailureReason,
    WorkerNodeIssue,
)

# We need to import the reasons submodule so the subclasses of AppLogFailureReason
# are defined. It's not pretty but it gives us a fairly simple way of being able
# to define new problems that are automatically integrated into the analyzer.
from . import reasons  # noqa

RE_FIND_JOB_ID = re.compile(rb"JobID: (\d{6,})\n")


class LbCondaJobsUnsupported(NotImplementedError):
    pass


class PreAnalysisResult(StrEnum):
    NO_LOG_FILE = auto()
    NO_XML_SUMMARY = auto()
    UNKNOWN_ERROR_ON_JOB_SUCCESS = auto()
    NO_EVENTS_SELECTED = auto()
    PROBABLY_OK = auto()
    NOT_IN_SUMMARY_XML = auto()
    NEEDS_GROUP_SIZE_REDUCTION = auto()
    NEEDS_LOG_ANALYSIS = auto()
    MAYBE_POST_APPLICATION_FAILURE = auto()
    NO_LOGSE_JOB_PARAMETER = auto()
    STALLED = auto()
    FAILED_INPUT_DATA_RESOLUTION = auto()
    INPUT_DATA_ALREADY_PROCESSED = auto()


class PostAnalysisResult(StrEnum):
    NEEDS_DOWNLOAD_INPUT_DATA = auto()
    KNOWN_CORRUPTION = auto()
    HIGH_MEMORY_USAGE = auto()
    EXTREMELY_HIGH_MEMORY_USAGE = auto()
    NEEDS_GROUP_SIZE_REDUCTION = auto()
    TOO_MANY_ATTEMPTS = auto()
    TOO_MUCH_MEMORY_FOR_CGROUPS = auto()


# TODO Make an dynamic enum for type


class ReasonInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    match: str
    explanation: str | None


class LFNDebugInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lfn: str
    job_id: int
    transform_id: int
    site: str | None = None
    log_url: str | None = None
    pre_analysis: PreAnalysisResult
    peak_memory: int | None = None
    maybe_reason: ReasonInfo | None = None
    post_analysis: PostAnalysisResult | None = None
    n_input_files: int | None = None

    @field_validator("maybe_reason", mode="before")
    @classmethod
    def maybe_reason_validator(cls, v):
        if isinstance(v, AppLogFailureReason):
            return ReasonInfo(
                type=v.__class__.__name__,
                match=v.match_string,
                explanation=v.explanation,
            )
        return v


class AggregatedLFNDebugInfo(LFNDebugInfo):
    occurrences: int = 1
    attempts: int = 1
    sites: dict[str, int] = {}
    log_urls: list[str] = []


class Job:
    @classmethod
    async def from_logse_lfn(cls, logse_lfn: str) -> Self:
        raise NotImplementedError()

    def __init__(
        self,
        transform_id: int,
        task_id: int,
        files: dict[str, bytes],
        *,
        job_id: int | None = None,
        url: str | None = None,
    ) -> None:
        """Describes the logs of a job which has been processed by the LHCbDIRAC Production System.

        Args:
            transform_id: The transform ID of the job.
            task_id: The task ID of the job with the transformation system.
            files: The list of LFNs of the files which have been processed by the job.
            job_id: The job ID of the job. If not given tries to guess based on the files.
        """
        self.job_id = job_id
        self.transform_id = transform_id
        self.task_id = task_id
        self.url = url
        self.files = JobArtifacts.from_files(files, transform_id=transform_id, task_id=task_id)
        self._guess_or_check_job_id()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"job_id={self.job_id}, "
            f"transform_id={self.transform_id}, "
            f"task_id={self.task_id}, "
            f"url={self.url})"
        )

    def __hash__(self) -> int:
        return hash((self.transform_id, self.task_id, self.job_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.transform_id == other.transform_id and self.task_id == other.task_id and self.job_id == other.job_id

    def _guess_or_check_job_id(self):
        if match := RE_FIND_JOB_ID.search(self.files.dirac_log):
            guessed_job_id = int(match.group(1))
            if self.job_id is None:
                self.job_id = guessed_job_id
            elif self.job_id != guessed_job_id:
                raise JobArtifactConsistencyError(f"Job ID mismatch: {self.job_id} != {guessed_job_id}")

    @property
    def site(self):
        site_parameter = self.files.workflow.find(".//Parameter[@name='Site']/value")
        if site_parameter is None:
            print(f"ERROR: Failed to find site parameter for {self.job_id}")
        else:
            possible_sites = site_parameter.text
            found_sites = set()
            for site in possible_sites.split(";"):
                if f"is running at site {site}\n".encode() in self.files.dirac_log:
                    found_sites.add(site)
            if len(found_sites) == 1:
                return found_sites.pop()
            print("ERROR: Failed to find site, likely ran at the wrong site!")
        if match := re.search(rb"running at site ([^\s]*)\n", self.files.dirac_log):
            found_site = match.group(1)
            print("ERROR: Guessing the site from log:", found_site)
            return found_site.decode()
        else:
            raise NotImplementedError(self, found_sites)

    @cached_property
    def pre_analysis(self) -> dict[str, PreAnalysisResult]:
        """Find input data to the job and determine what action should be taken."""
        # If we don't even have the prodrun config, we can't do anything
        if self.files.steps[0].prodrun_config is None:
            raise NotImplementedError("_process_job_jdl")
        input_lfns = self.files.steps[0].prodrun_config["input"]["files"]
        # We should always have a log file
        if self.files.steps[-1].application_log is None:
            return {lfn: PreAnalysisResult.NO_LOG_FILE for lfn in input_lfns}
        # We should always have a summary XML file
        if self.files.steps[-1].summary_xml is None:
            return {lfn: PreAnalysisResult.NO_XML_SUMMARY for lfn in input_lfns}
        # Check the file statuses from the first job
        files_by_status = {}
        for file in self.files.steps[0].summary_xml.findall(".//input/file"):
            # Entries that don't start with LFN: correspond to file access errors
            # Gaudi can potentially fallback to another replica in this case
            if not file.attrib["name"].startswith("LFN:"):
                continue
            files_by_status.setdefault(file.attrib["status"], []).append(file.attrib["name"])
        if set(files_by_status.keys()) - {"part", "full", "fail"}:
            raise NotImplementedError(self, files_by_status.keys())

        # If the summary XML says the job was successful do some sanity checks
        if ast.literal_eval(self.files.steps[-1].summary_xml.find(".//success").text):
            file_success = all(lfn in files_by_status.get("full", []) for lfn in input_lfns)
            for step in self.files.steps[1:]:
                if step.summary_xml is None:
                    file_success = False
                    break
                if not ast.literal_eval(step.summary_xml.find(".//success").text):
                    file_success = False
                    break
                if len(step.summary_xml.findall(".//input/file")) != 1:
                    raise NotImplementedError("Expected exactly one intermediate input file in the summary XML")
                if step.summary_xml.find(".//input/file").attrib["status"] != "full":
                    file_success = False
                    break

            if file_success:
                if self.files.steps[-1].summary_xml.findall(".//output/file"):
                    # Something probably went wrong in the LHCbDIRAC machinery
                    return {lfn: PreAnalysisResult.UNKNOWN_ERROR_ON_JOB_SUCCESS for lfn in input_lfns}
                if b"LHCbApplicationError" not in self.files.dirac_log:
                    # Ntuples are not considered output files by Gaudi so do some extra sanity checks
                    if b"NTuples saved successfully" in self.files.steps[-1].application_log:
                        return {lfn: PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE for lfn in input_lfns}
                    if self.files.steps[-1].bk_xml is not None:
                        # This can happen if the job fails to contact the TransformationManager
                        # You MUST check the stdout in the output sandbox (i.e. more than logSE)
                        # e.g. 1214907348
                        raise NotImplementedError("Bookkeeping report but no events selected?", self)
                    # TODO: Eventually we should make this impossible by ensuring files always have an FSR
                    # TODO: Once this is done we can make this check depend on the application version
                    return {lfn: PreAnalysisResult.NO_EVENTS_SELECTED for lfn in input_lfns}

        # Try to figure out which input files are bad
        result = {}
        if len(input_lfns) == 1:
            bad_lfns = [input_lfns[0]]
        elif len(self.files.steps) > 1 and len(input_lfns) > 1:
            # If it's the second step that failed we need to reduce the group size to isolate the bad file
            return {lfn: PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION for lfn in input_lfns}
        else:
            result |= {lfn: PreAnalysisResult.PROBABLY_OK for lfn in files_by_status.get("full", [])}
            bad_lfns = files_by_status.get("part", [])[:]
            bad_lfns += files_by_status.get("fail", [])
            # If a file is not in the summary XML, we don't know what happened to it
            result |= {
                lfn: PreAnalysisResult.NOT_IN_SUMMARY_XML
                for lfn in input_lfns
                if lfn not in result and lfn not in bad_lfns
            }

        # Bad files need to be analyse more carefully
        return result | {lfn: PreAnalysisResult.NEEDS_LOG_ANALYSIS for lfn in bad_lfns}

    @cached_property
    def log_analysis(self) -> LogFileMatches:
        return AppLogFailureReason.scan_job_log(self)

    @cached_property
    def peak_memory(self) -> int | None:
        if prmon_data := self.files.steps[-1].prmon_data:
            return max(prmon_data["rss+swap"]) * 1024
        return None

    @cached_property
    def problems_by_lfn(self) -> dict[str, LFNDebugInfo]:
        problems_by_lfn = defaultdict(list)
        if len(self.files.steps) == 1 and not set(self.log_analysis.by_lfn).issubset(set(self.pre_analysis)):
            raise NotImplementedError("Found an LFN in log which wasn't expected!?", self)

        if self.files.steps[0].prodrun_config["application"]["name"].startswith("lb-conda"):
            raise LbCondaJobsUnsupported("Debugging lb-conda jobs is not supported", self)

        unique_diagnoses = set(self.pre_analysis.values())

        override_diagnosis = None
        # If all files are successfully processed and we found an error during
        # finalization we need to reduce the group size
        if (
            len(self.log_analysis.by_lfn) > 1
            and unique_diagnoses == {PreAnalysisResult.PROBABLY_OK}
            and self.log_analysis.finalize
        ):
            override_diagnosis = PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION

        info_cls = partial(
            LFNDebugInfo,
            log_url=self.url,
            job_id=self.job_id,
            site=self.site,
            peak_memory=self.peak_memory,
            transform_id=self.transform_id,
        )
        found_reason_from_log_analysis = False
        for lfn, diagnosis in reversed(self.pre_analysis.items()):
            diagnosis = override_diagnosis or diagnosis
            if diagnosis == PreAnalysisResult.NOT_IN_SUMMARY_XML and self.log_analysis.by_lfn.get(lfn):
                # The summary XML has lied to us about the file having not been
                # processed, trust the log analysis instead
                diagnosis = PreAnalysisResult.NEEDS_LOG_ANALYSIS
            info_cls = partial(info_cls, lfn=lfn, pre_analysis=diagnosis)
            match diagnosis:
                case PreAnalysisResult.NO_LOG_FILE:
                    problems_by_lfn[lfn] = info_cls()
                case PreAnalysisResult.NO_XML_SUMMARY:
                    if self.log_analysis.init:
                        problems_by_lfn[lfn] = info_cls(maybe_reason=self.log_analysis.init[0])
                    else:
                        problems_by_lfn[lfn] = info_cls()
                case PreAnalysisResult.NEEDS_LOG_ANALYSIS:
                    if self.log_analysis.init:
                        for reason in self.log_analysis.init:
                            if isinstance(reason, WorkerNodeIssue):
                                maybe_reason = [reason]
                                break
                        else:
                            # See if the file is in status part to guess the bad LFN
                            input_files = self.files.steps[-1].summary_xml.findall(".//input/file")
                            if input_files:
                                bad_lfns = [f.attrib["name"] for f in input_files if f.attrib["status"] == "part"]
                            else:
                                bad_lfns = sorted(self.pre_analysis)
                            if len(bad_lfns) != 1:
                                raise NotImplementedError(self)
                            if bad_lfns[0] != lfn:
                                raise NotImplementedError(self)
                            maybe_reason = self.log_analysis.init
                    elif maybe_reason := self.log_analysis.by_lfn.get(lfn):
                        pass
                    elif len(self.files.steps[0].prodrun_config["input"]["files"]) == 1 and (
                        maybe_reason := next(iter(self.log_analysis.by_lfn.values()))
                    ):
                        pass
                    elif self.log_analysis.finalize:
                        if len(self.pre_analysis) == 1:
                            maybe_reason = self.log_analysis.finalize
                        elif diagnosis:
                            pass
                        else:
                            raise NotImplementedError(self)
                    elif not found_reason_from_log_analysis:
                        raise NotImplementedError(f"{self=} {len(self.files.steps[0].application_log)=}")
                    if maybe_reason:
                        found_reason_from_log_analysis = True
                        problems_by_lfn[lfn] = info_cls(maybe_reason=maybe_reason[0])
                    elif not found_reason_from_log_analysis:
                        raise NotImplementedError(self)
                    else:
                        problems_by_lfn[lfn] = info_cls(pre_analysis=PreAnalysisResult.PROBABLY_OK)
                case (
                    PreAnalysisResult.UNKNOWN_ERROR_ON_JOB_SUCCESS
                    | PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE
                    | PreAnalysisResult.NO_EVENTS_SELECTED
                ):
                    if len(unique_diagnoses) != 1:
                        raise NotImplementedError(self)
                    if self.log_analysis.init:
                        raise NotImplementedError(self)
                    if len(self.files.steps) == 1 and set(self.log_analysis.by_lfn) != set(self.pre_analysis):
                        raise NotImplementedError(self)
                    if self.log_analysis.finalize:
                        problems_by_lfn[lfn] = info_cls(maybe_reason=self.log_analysis.finalize[0])
                    else:
                        problems_by_lfn[lfn] = info_cls()

                case PreAnalysisResult.PROBABLY_OK:
                    if maybe_reason := self.log_analysis.by_lfn.get(lfn):
                        if not maybe_reason:
                            raise NotImplementedError(self)
                        problems_by_lfn[lfn] = info_cls(maybe_reason=maybe_reason[0])
                    else:
                        problems_by_lfn[lfn] = info_cls()

                case PreAnalysisResult.NOT_IN_SUMMARY_XML:
                    if self.log_analysis.by_lfn.get(lfn):
                        raise NotImplementedError(self)
                    problems_by_lfn[lfn] = info_cls()

                case PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION:
                    if len(unique_diagnoses) != 1:
                        raise NotImplementedError(self)
                    maybe_reason = None
                    if unique_diagnoses == {PreAnalysisResult.PROBABLY_OK} and self.log_analysis.finalize:
                        maybe_reason = self.log_analysis.finalize[0]
                    problems_by_lfn[lfn] = info_cls(maybe_reason=maybe_reason)
                case _:
                    raise NotImplementedError(diagnosis)

        return dict(problems_by_lfn)
