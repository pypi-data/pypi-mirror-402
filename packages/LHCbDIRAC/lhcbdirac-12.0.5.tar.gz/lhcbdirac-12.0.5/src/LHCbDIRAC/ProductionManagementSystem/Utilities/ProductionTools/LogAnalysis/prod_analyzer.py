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
# from __future__ import annotations

__all__ = [
    "analyze_prod",
    "summarize_prod",
    "group_by_problem",
    "file_exists",
]

import asyncio
import importlib.resources
import json
import logging
import os
import re
import sys
from collections import defaultdict, Counter
from itertools import chain
from operator import attrgetter, itemgetter
from types import TracebackType
from urllib.parse import urlencode

import Levenshtein
from DIRAC.WorkloadManagementSystem.Client.JobMonitoringClient import JobMonitoringClient
from pathlib import Path
from pydantic import TypeAdapter
from rich import print

from LHCbDIRAC.TransformationSystem.Client.TransformationClient import TransformationClient
from .file_access import read_zip, file_exists
from .base_reasons import LogFileMatch, RecoverableFailure, KnownUnrecoverableFailure, EventTimeout, UnknownFailure
from .job_analyzer import (
    Job,
    LFNDebugInfo,
    PreAnalysisResult,
    PostAnalysisResult,
    LogFileMatches,
    LogFileMatch,
    AggregatedLFNDebugInfo,
    ReasonInfo,
    LbCondaJobsUnsupported,
)
from .lbconda import analyse_log as analyse_lbconda_log
from .utils import presorted_groupby, unsorted_groupby, ProgressUpdater, old_to_new_log_url, call_dirac


RE_LOG_SE = re.compile(r'href="(https://[^"/]+(?:/lhcb-dirac-logse/)?(/[^"]+)/)"')
LEVENSHTEIN_RATIO_THRESHOLD = 0.85
GroupedProblems = dict[str, dict[str, list[AggregatedLFNDebugInfo]]]
CacheType = dict[int, dict[str, LFNDebugInfo]]

logger = logging.getLogger(__name__)


def key_prioritize(reason: LFNDebugInfo) -> tuple[int, int, int, int, int, int]:
    """Key function to sort LFNDebugInfo such that the most important ones are first."""
    if reason.maybe_reason is None:
        key = reason.n_input_files, sys.maxsize, sys.maxsize, -reason.job_id, -sys.maxsize
    else:
        reason_type = LogFileMatch.name_to_reason[reason.maybe_reason.type]  # pylint: disable=unsubscriptable-object
        for i, base_type in enumerate([KnownUnrecoverableFailure, UnknownFailure, (RecoverableFailure, EventTimeout)]):
            if issubclass(reason_type, base_type):
                key = (
                    i,
                    LogFileMatch.name_to_id[reason.maybe_reason.type],  # pylint: disable=unsubscriptable-object
                    -reason.job_id,
                    -len(reason.maybe_reason.match),
                )
                break
        else:
            raise NotImplementedError(reason.maybe_reason.type)

    match reason.pre_analysis:
        case PreAnalysisResult.NO_EVENTS_SELECTED:
            return reason.n_input_files, -1, *key
        case PreAnalysisResult.MAYBE_POST_APPLICATION_FAILURE:
            return reason.n_input_files, 0, *key
        case PreAnalysisResult.PROBABLY_OK:
            return reason.n_input_files, 1, *key
        case PreAnalysisResult.INPUT_DATA_ALREADY_PROCESSED:
            return reason.n_input_files, 2, *key
        case PreAnalysisResult.NEEDS_LOG_ANALYSIS:
            return reason.n_input_files, 3, *key
        case PreAnalysisResult.UNKNOWN_ERROR_ON_JOB_SUCCESS:
            return reason.n_input_files, 4, *key
        case PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION:
            return reason.n_input_files, 5, *key
        case PreAnalysisResult.NOT_IN_SUMMARY_XML:
            return reason.n_input_files, 6, *key
        case PreAnalysisResult.NO_XML_SUMMARY:
            return reason.n_input_files, 7, *key
        case PreAnalysisResult.STALLED:
            return reason.n_input_files, 8, *key
        case PreAnalysisResult.FAILED_INPUT_DATA_RESOLUTION:
            return reason.n_input_files, 9, *key
        case PreAnalysisResult.NO_LOG_FILE:
            return reason.n_input_files, 10, *key
        case PreAnalysisResult.NO_LOGSE_JOB_PARAMETER:
            return reason.n_input_files, 11, *key
    raise NotImplementedError(reason)


async def analyze_prod(
    tid: int,
    *,
    progress: ProgressUpdater = ProgressUpdater(),
    lfns: list[str] | None = None,
    statuses: list[str] = ["MaxReset", "Problematic"],
) -> list[LFNDebugInfo]:
    print(f"{tid}: Getting files")
    files = await call_dirac(
        TransformationClient().getTransformationFiles,
        {"TransformationID": tid} | ({"LFN": lfns} if lfns else {"Status": statuses}),
        columns=["FileID", "LFN"],
    )
    file_ids = {f["FileID"]: f"LFN:{f['LFN']}" for f in files}
    if len(file_ids) == 0:
        print(f"{tid}: No files found, returning early")
        return []

    print(f"{tid}: Getting tasks for {len(file_ids)} files")
    res = await call_dirac(
        TransformationClient().getTableDistinctAttributeValues,
        "TransformationFileTasks",
        ["TaskID"],
        {"TransformationID": tid, "FileID": list(file_ids)},
    )
    tasks = await call_dirac(
        TransformationClient().getTransformationTasks,
        {"TransformationID": tid, "TaskID": res["TaskID"]},
        inputVector=True,
    )
    task_id_to_input_lfns = {
        k: [f"LFN:{x}" for x in next(v)["InputVector"].split(";")]
        for k, v in presorted_groupby(tasks, key=itemgetter("TaskID"))
    }
    job_id_to_task_info = {
        int(k): next(v) for k, v in presorted_groupby(tasks, key=itemgetter("ExternalID")) if int(k) != 0
    }
    with ProductionAnalysisCache(tid) as cache:
        results = await cache.get_results(tid, job_id_to_task_info, files, task_id_to_input_lfns, progress)
    return list(chain.from_iterable(results.values()))


class ProductionAnalysisCache:
    """Cache for production analysis results with automatic persistence."""

    def __init__(self, cache_key: str | int, *, cache_directory: Path | None = None) -> None:
        self._cache_key = str(cache_key)
        self._cache_directory = cache_directory or self._pick_cache_directory()
        self._path = self._cache_directory / f"{self._cache_key}.json"
        self._cache: CacheType = self._load_cache()
        self._modified = False

    @property
    def cache_key(self) -> str:
        """The cache key used for this cache instance."""
        return self._cache_key

    @property
    def path(self) -> Path:
        """The filesystem path where the cache is stored."""
        return self._path

    def _pick_cache_directory(self) -> Path:
        """Determine the appropriate cache directory following XDG standards."""
        cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        cache_dir = cache_home / "lhcbdirac/log-analysis-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _load_cache(self) -> CacheType:
        """Load cache from disk if it exists."""
        if not self._path.is_file():
            return {}

        try:
            return TypeAdapter(CacheType).validate_json(self._path.read_text())
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to load cache from {self._path}: {e}. Starting with empty cache.")
            return {}

    def save(self) -> None:
        """Persist the cache to disk."""
        if not self._modified:
            return

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_bytes(TypeAdapter(CacheType).dump_json(self._cache))
            self._modified = False
        except OSError as e:
            logger.error(f"Failed to save cache to {self._path}: {e}")

    def __enter__(self) -> "ProductionAnalysisCache":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - automatically save cache."""
        self.save()

    def __getitem__(self, job_id: int) -> dict[str, LFNDebugInfo]:
        return self._cache.setdefault(job_id, {})

    def __contains__(self, job_id: int) -> bool:
        return job_id in self._cache

    def __setitem__(self, job_id: int, value: dict[str, LFNDebugInfo]) -> None:
        self._cache[job_id] = value
        self._modified = True

    async def get_results(
        self,
        tid: int | str,
        job_id_to_task_info: dict[int, dict[str, str]],
        files: list[dict[str, str]],
        task_id_to_input_lfns: dict[int, list[str]],
        progress: ProgressUpdater,
    ) -> dict[str, list[LFNDebugInfo]]:
        """
        Get analysis results, using cache where available and analyzing new jobs.

        Args:
            tid: Transformation ID
            job_id_to_task_info: Mapping of job IDs to task information
            files: List of file information dictionaries
            task_id_to_input_lfns: Mapping of task IDs to input LFN lists
            progress: Progress updater for tracking analysis

        Returns:
            Dictionary mapping LFNs to lists of debug information
        """
        results = self.get_cached_results(files, job_id_to_task_info)
        if not job_id_to_task_info:
            return results

        new_debug_infos = await _analyze_jobs(tid, job_id_to_task_info, task_id_to_input_lfns, progress)
        for debug_info in new_debug_infos:
            self[debug_info.job_id][debug_info.lfn] = debug_info
            if debug_info.lfn in results:
                results[debug_info.lfn].append(debug_info)

        self.save()
        return results

    def get_cached_results(
        self,
        files: list[dict[str, str]],
        job_id_to_task_info: dict[int, dict[str, str]],
    ) -> dict[str, list[LFNDebugInfo]]:
        """
        Retrieve cached results and remove cached jobs from the work queue.

        Args:
            files: List of file information dictionaries
            job_id_to_task_info: Mapping of job IDs to task information (modified in-place)

        Returns:
            Dictionary mapping LFNs to lists of cached debug information
        """
        results: dict[str, list[LFNDebugInfo]] = {f"LFN:{x['LFN']}": [] for x in files}
        cached_job_ids = [job_id for job_id in job_id_to_task_info if job_id in self]

        for job_id in cached_job_ids:
            job_id_to_task_info.pop(job_id)
            for lfn, debug_info in self[job_id].items():
                if lfn in results:
                    results[lfn].append(debug_info)

        return results


async def guess_log_lfn_if_needed(job_id, parameters, job_id_to_task_info: dict[int, dict[str, str]]) -> None:
    if "Log URL" in parameters:
        return

    input_lfns = job_id_to_task_info[job_id]["InputVector"].split(";")
    if not all(x.startswith("/lhcb/") for x in input_lfns):
        raise NotImplementedError("Cannot guess log LFN", job_id, input_lfns)
    parts = input_lfns[0].split("/")[:4]
    parts.append("LOG")
    parts.append(str(job_id_to_task_info[job_id]["TransformationID"]).rjust(8, "0"))
    task_id = str(job_id_to_task_info[job_id]["TaskID"]).rjust(8, "0")
    parts.append(task_id[:4])
    parts.append(task_id)
    lfn = "/".join(parts)
    if await file_exists(f"{lfn}.zip"):
        print("Guessed log LFN for job", job_id, ":", lfn)
        parameters["Log URL"] = f'<a href="https://lhcb-dirac-logse.web.cern.ch{lfn}/">'


async def _analyze_jobs(tid, job_id_to_task_info, task_id_to_input_lfns, progress) -> list[LFNDebugInfo]:
    print(f"{tid}: Getting Job parameters for {len(job_id_to_task_info)} jobs")
    job_parameters = await call_dirac(JobMonitoringClient().getJobParameters, list(job_id_to_task_info), ["Log URL"])
    assert len(job_parameters) == len(job_id_to_task_info)
    job_id_to_status = await call_dirac(JobMonitoringClient().getJobsStates, list(job_id_to_task_info))

    async with asyncio.TaskGroup() as tg:
        for job_id, parameters in job_parameters.items():
            tg.create_task(guess_log_lfn_if_needed(job_id, parameters, job_id_to_task_info))

    results: list[LFNDebugInfo] = []
    log_urls = {}
    read_tasks = {}
    site_missing = defaultdict(list)
    for job_id, parameters in job_parameters.items():
        if not parameters:
            input_lfns = set(task_id_to_input_lfns[job_id_to_task_info[job_id]["TaskID"]])
            for lfn in input_lfns:
                if job_id_to_status[job_id]["MinorStatus"] == "Watchdog identified this job as stalled":
                    pre_analysis = PreAnalysisResult.STALLED
                elif "Failed Input Data Resolution" in job_id_to_status[job_id]["ApplicationStatus"]:
                    pre_analysis = PreAnalysisResult.FAILED_INPUT_DATA_RESOLUTION
                else:
                    pre_analysis = PreAnalysisResult.NO_LOGSE_JOB_PARAMETER
                debug_info = LFNDebugInfo(lfn=lfn, job_id=job_id, pre_analysis=pre_analysis, transform_id=tid)
                site_missing[job_id].append(debug_info)
                results.append(debug_info)
        elif match := RE_LOG_SE.search(parameters["Log URL"]):
            if "Input Data Already Processed" in job_id_to_status[job_id]["ApplicationStatus"]:
                pre_analysis = PreAnalysisResult.INPUT_DATA_ALREADY_PROCESSED
                input_lfns = set(task_id_to_input_lfns[job_id_to_task_info[job_id]["TaskID"]])
                for lfn in input_lfns:
                    debug_info = LFNDebugInfo(
                        lfn=lfn,
                        job_id=job_id,
                        pre_analysis=pre_analysis,
                        log_url=old_to_new_log_url(match.group(1)),
                        transform_id=tid,
                    )
                    site_missing[job_id].append(debug_info)
                    results.append(debug_info)
            else:
                log_urls[job_id] = old_to_new_log_url(match.group(1))
                # TODO: Add timeout for reading the zip file
                read_tasks[read_zip(job_id, f"{match.group(2)}.zip")] = job_id
        else:
            raise NotImplementedError(parameters)

    lb_conda_jobs = []
    progress.advance_total(len(read_tasks))
    for future in asyncio.as_completed(read_tasks):
        job_id, result = await future
        task_id = job_id_to_task_info[job_id]["TaskID"]
        # TODO: Use an excetion and log?
        if result:
            job = Job(tid, task_id, result, job_id=job_id, url=log_urls[job_id])
            try:
                for lfn, debug_info in job.problems_by_lfn.items():
                    results.append(debug_info)
            except LbCondaJobsUnsupported:
                lb_conda_jobs.append(job)
        progress.advance()

    for job in lb_conda_jobs:
        input_files = job.files.steps[0].prodrun_config["input"]["files"]
        if len(input_files) > 1:
            for input_file in input_files:
                results.append(
                    LFNDebugInfo(
                        lfn=input_file,
                        pre_analysis=PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION,
                        log_url=job.url,
                        job_id=job.job_id,
                        site=job.site,
                        peak_memory=job.peak_memory,
                        transform_id=job.transform_id,
                    )
                )
            continue
        matches = analyse_lbconda_log(job.files.steps[-1].application_log)
        if len(matches) == 0:
            raise NotImplementedError(job)
        else:
            results.append(
                LFNDebugInfo(
                    lfn=input_files[0],
                    pre_analysis=PreAnalysisResult.NEEDS_LOG_ANALYSIS,
                    log_url=job.url,
                    job_id=job.job_id,
                    site=job.site,
                    peak_memory=job.peak_memory,
                    transform_id=job.transform_id,
                    maybe_reason=matches[0],
                )
            )
        progress.advance()

    input_data = await call_dirac(JobMonitoringClient().getInputData, [r.job_id for r in results])
    for debug_info in results:
        debug_info.n_input_files = len(input_data[debug_info.job_id])

    if site_missing:
        print(f"{tid}: Getting missing site info for {len(site_missing)} jobs")
        for job_id, info in (await call_dirac(JobMonitoringClient().getJobsSites, list(site_missing))).items():
            for debug_info in site_missing[job_id]:
                debug_info.site = info["Site"]

    return results


def summarize_prod(debug_infos: list[LFNDebugInfo]) -> list[AggregatedLFNDebugInfo]:
    """Apply corrections that we can only infer by looking at the transformation as a whole"""
    results = []
    for _, debug_infos in unsorted_groupby(debug_infos, key=attrgetter("lfn")):
        debug_infos = sorted(debug_infos, key=key_prioritize)
        debug_info = debug_infos[0]
        info = {"attempts": len(debug_infos), "occurrences": 0, "sites": Counter(), "log_urls": []}

        if debug_info.maybe_reason is None:
            for past_debug_info in debug_infos:
                if debug_info.pre_analysis == past_debug_info.pre_analysis:
                    info["sites"][past_debug_info.site] += 1
                    info["occurrences"] += 1
                    if past_debug_info.log_url:
                        info["log_urls"].append(past_debug_info.log_url)
        else:
            if debug_info.pre_analysis == PreAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION:
                info["post_analysis"] = PostAnalysisResult.NEEDS_GROUP_SIZE_REDUCTION

            if debug_info.maybe_reason.type == "XRDOperationExpired":
                if debug_info.pre_analysis == PreAnalysisResult.STALLED:
                    info["post_analysis"] = PostAnalysisResult.NEEDS_DOWNLOAD_INPUT_DATA
                elif debug_info.maybe_reason and debug_info.maybe_reason.type in {
                    "XRDOperationExpired",
                    "EventWatchdog",
                }:
                    info["post_analysis"] = PostAnalysisResult.NEEDS_DOWNLOAD_INPUT_DATA

            if debug_info.maybe_reason.type == "MaybeCorruptedFile":
                module_name = "LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis"
                with importlib.resources.files(module_name).joinpath("known_corruption.json").open("r") as f:
                    known_corruption = json.load(f)
                if known_corruption.get(debug_info.lfn.split(":", 1)[1]):
                    explanation = (
                        "This file is known to contain some corrupt events. It "
                        "likely cannot be recovered for this production however "
                        "we typically don't delete these files as other analyses "
                        "might not depend on the bad branches."
                    )
                    debug_info.maybe_reason = ReasonInfo(
                        type="KnownCorruptedFile", match=debug_info.maybe_reason.match, explanation=explanation
                    )

            for past_debug_info in debug_infos:
                past_reason = past_debug_info.maybe_reason
                if past_reason is None or past_reason.type != debug_info.maybe_reason.type:
                    continue
                if Levenshtein.ratio(past_reason.match, debug_info.maybe_reason.match) > LEVENSHTEIN_RATIO_THRESHOLD:
                    info["occurrences"] += 1
                    info["sites"][past_debug_info.site] += 1
                    info["log_urls"].append(past_debug_info.log_url)

        if debug_info.pre_analysis != PreAnalysisResult.NOT_IN_SUMMARY_XML and debug_info.peak_memory:
            # Reading corrupt data can trigger excessive memory consumption and shouldn't be considered
            if not (
                debug_info.maybe_reason
                and debug_info.maybe_reason.type
                in {"XRDOperationExpired", "MaybeCorruptedFile", "KnownCorruptedFile", "XRDIssue"}
            ):
                if debug_info.peak_memory > 10 * 1024**3:
                    info["post_analysis"] = PostAnalysisResult.EXTREMELY_HIGH_MEMORY_USAGE
                elif debug_info.peak_memory > 5 * 1024**3 and debug_info.maybe_reason is None:
                    info["post_analysis"] = PostAnalysisResult.HIGH_MEMORY_USAGE

        if (
            debug_info.peak_memory
            and debug_info.site in {"LCG.IN2P3.fr"}
            and getattr(debug_info.maybe_reason, "type", None) in {"MaybeOOMKiller", "FunctorCompilationFailure"}
        ):
            # Some sites have started enforcing memory limits via cgroups and will need to be sent to the hospital
            if debug_info.peak_memory > 2.8 * 1024**3:
                info["post_analysis"] = PostAnalysisResult.TOO_MUCH_MEMORY_FOR_CGROUPS

        if len(debug_infos) > 20:
            info["post_analysis"] = PostAnalysisResult.TOO_MANY_ATTEMPTS

        results.append(AggregatedLFNDebugInfo.model_validate(debug_info.model_dump(mode="json") | info))

    return results


def group_by_problem(all_problems: list[LogFileMatches]) -> GroupedProblems:
    def key_func(x: LogFileMatch) -> tuple[str, str, str]:
        if x.post_analysis:
            return (x.post_analysis, "", "")
        if x.maybe_reason:
            return ("", x.maybe_reason.type, "")
        return ("", "", x.pre_analysis)

    summarized = {}
    for (post_analysis, reason_type, pre_analysis), matches in unsorted_groupby(all_problems, key=key_func):
        if sum(map(bool, (post_analysis, reason_type, pre_analysis))) != 1:
            raise NotImplementedError("post_analysis/reason_type/pre_analysis are mutually exclusive when grouping")

        if reason_type:
            assert reason_type not in summarized
            summarized[reason_type] = {}
            for match_str, instances in unsorted_groupby(matches, key=attrgetter("maybe_reason.match")):
                for ref_match_str in summarized[reason_type]:
                    if len(match_str) > 100_000 or len(ref_match_str) > 100_000:
                        # Deduplicate lines in very large strings to avoid performance issues
                        a = "\n".join(sorted(set(match_str.splitlines())))
                        b = "\n".join(sorted(set(ref_match_str.splitlines())))
                        print(
                            f"Comparing large strings of lengths {len(match_str)} and {len(ref_match_str)} "
                            f"reduced to {len(a)} and {len(b)}"
                        )
                        ratio = Levenshtein.ratio(a, b)
                    else:
                        ratio = Levenshtein.ratio(match_str, ref_match_str)

                    if ratio > LEVENSHTEIN_RATIO_THRESHOLD:
                        summarized[reason_type][ref_match_str].extend(instances)
                        break
                else:
                    summarized[reason_type][match_str] = list(instances)
        else:
            summarized.setdefault("", {})[post_analysis or pre_analysis] = list(matches)
    return dict(summarized)
