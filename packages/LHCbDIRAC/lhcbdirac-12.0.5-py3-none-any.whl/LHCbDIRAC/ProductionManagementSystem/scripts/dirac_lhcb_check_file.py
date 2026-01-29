#!/usr/bin/env python
###############################################################################
# (c) Copyright 2025 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
"""Check and verify ROOT files from the LHCb grid"""
from __future__ import annotations

import asyncio
from functools import reduce
import importlib.resources
import json
import mmap
import re
import ssl
import sys
import tempfile
import traceback
import zlib
from contextlib import ExitStack, AsyncExitStack
from pathlib import Path

import httpx
import uproot
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from DIRAC import gLogger
from DIRAC.Core.Base.Script import Script
from DIRAC.Core.Utilities.ReturnValues import convertToReturnValue

STEP_SIZE = 1000


def parseArgs():
    outputDir = None
    noVerify = False
    fast = False
    excludeSeRegex = None

    @convertToReturnValue
    def setOutputDir(s: str):
        nonlocal outputDir
        outputDir = Path(s)

    @convertToReturnValue
    def setNoVerify(_):
        nonlocal noVerify
        noVerify = True

    @convertToReturnValue
    def setFast(_):
        nonlocal fast
        fast = True

    @convertToReturnValue
    def setExcludeSeRegex(s: str):
        nonlocal excludeSeRegex
        excludeSeRegex = re.compile(s)

    switches = [
        ("", "output-dir=", "Directory to save downloaded files", setOutputDir),
        ("", "no-verify", "Do not verify file contents", setNoVerify),
        ("", "fast", "Use all sources to download the file and don't validate SEs individually", setFast),
        ("", "exclude-se-regex=", "Regex to exclude SEs from download", setExcludeSeRegex),
    ]
    Script.registerSwitches(switches)
    Script.registerArgument("lfn: LFN of the file to check")
    Script.registerArgument("branch: Branch name to check (optional)", mandatory=False)
    Script.registerArgument("event: Event number to check (optional)", mandatory=False)
    Script.parseCommandLine(ignoreErrors=False)
    lfn, branch, event = Script.getPositionalArgs(group=True)

    if event is not None:
        event = int(event)

    return lfn, branch, event, outputDir, noVerify, fast, excludeSeRegex


@Script()
def main():
    lfn, branch, event, outputDir, noVerify, fast, excludeSeRegex = parseArgs()

    with ExitStack() as stack:
        if outputDir:
            destination = outputDir / Path(lfn).name
        else:
            tmp = Path(stack.enter_context(tempfile.TemporaryDirectory()))
            destination = tmp / Path(lfn).name
        asyncio.run(download_file(lfn, destination, validate_all_replicas=not fast, exclude=excludeSeRegex))

        gLogger.notice(f"Downloaded {lfn} to {destination}")
        if noVerify:
            gLogger.notice("Skipping verification")
            return
        f = stack.enter_context(uproot.open(destination))

        err_msg = None
        bad_streamers = len(f._file.streamers) == 0
        if bad_streamers:
            # example: /lhcb/LHCb/Collision24/RDLOW.DST/00276117/0003/00276117_00036205_1.rdlow.dst
            err_msg = "No streamers found"
            gLogger.warn(f"{lfn} has no streamers, probably corrupted")

        tree_names = f.keys(recursive=True, cycle=False, filter_classname="TTree")
        if "Event" in tree_names and branch:
            tree_names = ["Event"]
        try:
            for tree_name in tree_names:
                gLogger.info(f"{tree_name=}")
                check_file(f, tree_name, branch, event)
        except Exception as e:
            traceback.print_exc()
            err_msg = repr(e)
            if branch is not None:
                gLogger.error(f"Affected branch {branch}")
        else:
            if not bad_streamers:
                gLogger.notice(f"{lfn} appears to be valid")
                return

        gLogger.error(f"Error reading {lfn} {err_msg}")

        module_name = "LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis"
        with importlib.resources.files(module_name).joinpath("known_corruption.json").open("r") as known_file:
            metadata = json.load(known_file)

        gLogger.error(f"Found corruption in {lfn} {branch} {event}:\n{err_msg}")
        known_message = metadata.get(lfn, {}).get(branch, {}).get(str(event))
        if known_message:
            if err_msg == known_message:
                gLogger.notice("Message matches known corruption")
            else:
                gLogger.warn(f"Known corruption with different message: {known_message}")
        else:
            gLogger.error(f"Unknown corruption: {json.dumps(err_msg)}")
        sys.exit(1)


class Adler32:
    """Adler32 checksum calculator."""

    def __init__(self):
        self._checksum = 1
        # Need to track length for combining checksums
        self._length = 0

    def __repr__(self):
        return f"Adler32(checksum={self.checksum:#010x}, length={self.length})"

    def update(self, data):
        self._checksum = zlib.adler32(data, self._checksum)
        self._length += len(data)

    @property
    def checksum(self):
        return self._checksum & 0xFFFFFFFF

    @property
    def length(self):
        return self._length

    def __str__(self):
        return f"{self.checksum:#010x}"

    def __and__(self, other: Adler32) -> Adler32:
        if not isinstance(other, Adler32):
            return NotImplemented
        combined = Adler32()
        combined._checksum = self._combine_adler32(other.checksum, other.length)
        combined._length = self.length + other.length
        return combined

    def _combine_adler32(self, adler2: int, len2: int) -> int:
        """
        Combine two Adler-32 checksums.
        adler1: checksum of first block
        adler2: checksum of second block
        len2: length of second block
        """
        MOD = 65521

        # Extract A and B from checksums
        A1 = self.checksum & 0xFFFF
        B1 = (self.checksum >> 16) & 0xFFFF
        A2 = adler2 & 0xFFFF
        B2 = (adler2 >> 16) & 0xFFFF

        # Combine
        A = (A1 + A2 - 1) % MOD
        B = (B1 + B2 + len2 * A1 - len2) % MOD

        return (B << 16) | A


class MmapFile:
    """Context manager for memory-mapped file access."""

    def __init__(self, path: Path, size: int):
        self.path = path
        self.size = size
        self._fh = None
        self._mm = None

    def __enter__(self):
        self._fh = open(self.path, "w+b")
        self._fh.truncate(self.size)
        self._mm = mmap.mmap(self._fh.fileno(), 0)
        return self._mm

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._mm is not None:
            self._mm.flush()
            self._mm.close()
        if self._fh is not None:
            self._fh.close()
        return False


class DownloadWorkerCallback:
    def __init__(self, mm, start, progress_callback, cancel_callback=None, completion_callback=None):
        self.mm = mm
        self.current_pos = start
        self.progress_callback = progress_callback
        self.cancel_callback = cancel_callback
        self.completion_callback = completion_callback
        self.bytes_downloaded = 0

    def handle_chunk(self, chunk: bytes):
        self.mm[self.current_pos : self.current_pos + len(chunk)] = chunk
        self.current_pos += len(chunk)
        self.bytes_downloaded += len(chunk)
        self.progress_callback(len(chunk))

    def handle_cancel(self):
        if self.cancel_callback:
            self.cancel_callback(self.bytes_downloaded)

    def handle_completion(self):
        if self.completion_callback:
            self.completion_callback()


class ChunkedDownloaderWorker:
    def __init__(self, client: httpx.AsyncClient, se: str, pfn: str, queue: asyncio.Queue, task_id: int):
        self.client = client
        self.se = se
        self.pfn = pfn
        self.queue = queue
        self.task_id = task_id
        self.queue.put_nowait(self)

    def __repr__(self) -> str:
        return f"ChunkedDownloaderWorker(se={self.se}, pfn={self.pfn})"

    async def download(self, callback: DownloadWorkerCallback, *, byte_range: tuple[int, int] | None) -> Adler32:
        checksum = Adler32()
        headers = {}
        expected_length = None
        if byte_range is not None:
            self.current_start, self.current_end = byte_range
            headers["Range"] = f"bytes={self.current_start}-{self.current_end-1}"
            gLogger.debug(f"{self.se} downloading range {self.current_start}-{self.current_end-1}")
            expected_length = self.current_end - self.current_start
        try:
            async with AsyncExitStack() as stack:
                coro = self.client.stream("GET", self.pfn, headers=headers)
                response = await stack.enter_async_context(coro)
                content_length = int(response.headers.get("Content-Length", 0))
                if expected_length is not None and content_length != expected_length:
                    msg = f"Unexpected content length for range from {self!r}"
                    raise NotImplementedError(msg)
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=32_768):
                    checksum.update(chunk)
                    callback.handle_chunk(chunk)
        except asyncio.CancelledError:
            gLogger.debug(f"{self.se} download was cancelled")
            callback.handle_cancel()
            raise
        else:
            callback.handle_completion()
        finally:
            self.queue.put_nowait(self)
        return checksum


async def download_file(lfn, dest, *, validate_all_replicas: bool = False, exclude: re.Pattern | None = None):
    from DIRAC.Core.Utilities.ReturnValues import returnValueOrRaise
    from DIRAC.Core.Security.Locations import getCAsLocation, getProxyLocation
    from DIRAC.DataManagementSystem.Client.DataManager import DataManager
    from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

    replicas = returnValueOrRaise(DataManager().getReplicas(lfn, diskOnly=True, protocol="https"))
    if replicas["Failed"]:
        raise NotImplementedError(f"Failed to get replicas for {lfn}: {replicas['Failed']}")

    result = returnValueOrRaise(FileCatalog().getFileMetadata(lfn))
    if result["Failed"]:
        raise NotImplementedError(f"Failed to get metadata for {lfn}: {result['Failed']}")
    expected_checksum = int(result["Successful"][lfn]["Checksum"], base=16)
    expected_size = result["Successful"][lfn]["Size"]

    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, capath=getCAsLocation())
    ctx.load_cert_chain(getProxyLocation())

    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(httpx.AsyncClient(timeout=None, verify=ctx, follow_redirects=True))

        progress_columns = [
            TextColumn("[bold blue]{task.fields[url]}", justify="right"),
            BarColumn(),
            TransferSpeedColumn(),
        ]
        progress_columns.extend([DownloadColumn(), TimeElapsedColumn(), TimeRemainingColumn()])
        progress = Progress(*progress_columns, transient=False)

        progress = stack.enter_context(progress)

        if validate_all_replicas:
            tasks = []
            for se, pfn in replicas["Successful"][lfn].items():
                if exclude and exclude.fullmatch(se):
                    gLogger.info(f"Excluding {se} due to exclude regex")
                    continue
                task_id = progress.add_task("download", url=se, total=0)
                tasks.append(download_replica(client, se, pfn, dest, progress, task_id))
                # Later replicas should only compute the checksum
                dest = None
            checksums = await asyncio.gather(*tasks)
        else:
            gLogger.notice(f"Downloading file using all available replicas to {dest}")
            mm = stack.enter_context(MmapFile(dest, expected_size))

            def progress_callback(progress: Progress, summary_task_id: int, task_id: int):
                def callback(n: int):
                    progress.update(summary_task_id, advance=n)
                    progress.update(task_id, advance=n)

                return callback

            def cancel_callback(progress: Progress, summary_task_id: int, task_id: int):
                def callback(bytes_downloaded: int):
                    progress.update(summary_task_id, advance=-bytes_downloaded)
                    progress.update(task_id, advance=-bytes_downloaded)

                return callback

            current_pos = 0
            chunk_size = 16 * 1024 * 1024

            workers = []
            available_workers = asyncio.Queue()
            summary_task_id = progress.add_task("summary", url="Overall", total=expected_size)

            for se, pfn in replicas["Successful"][lfn].items():
                if exclude and exclude.fullmatch(se):
                    gLogger.info(f"Excluding {se} due to exclude regex")
                    continue
                task_id = progress.add_task("download", url=se, total=0)
                worker = ChunkedDownloaderWorker(client, se, pfn, available_workers, task_id)
                workers.append(worker)

            tasks = {}
            async with asyncio.TaskGroup() as tg:
                while current_pos < expected_size:
                    worker = await available_workers.get()
                    start = current_pos
                    end = min(current_pos + chunk_size, expected_size)

                    pcallback = progress_callback(progress, summary_task_id, worker.task_id)
                    ccallback = cancel_callback(progress, summary_task_id, worker.task_id)
                    byte_range = (start, end)
                    callback = DownloadWorkerCallback(mm, byte_range[0], pcallback, cancel_callback=ccallback)
                    task = tg.create_task(worker.download(callback, byte_range=byte_range))
                    tasks[byte_range] = [task]
                    current_pos = end

                # Add alternative sources for the data which is still being downloaded to prevent slow sources
                # from blocking the download
                while True:
                    worker = await available_workers.get()
                    gLogger.debug(f"Got available worker {worker.se}")
                    gLogger.debug(f"Currently have {len(tasks)} download tasks")
                    active_ranges = [k for k, ts in tasks.items() if not any(t.done() for t in ts)]
                    gLogger.debug(f"Currently have {len(active_ranges)} active download tasks")
                    for k, ts in tasks.items():
                        if k not in active_ranges:
                            continue
                        for t in ts:
                            if not t.done():
                                gLogger.debug(f"  {k} ({len(ts)=}): Task {t.get_name()} is active")
                            elif t.done():
                                gLogger.debug(f"  {k} ({len(ts)=}): Task {t.get_name()} is done")
                            elif t.cancelling():
                                gLogger.debug(f"  {k} ({len(ts)=}): Task {t.get_name()} is cancelling")
                            else:
                                raise NotImplementedError("Unknown task state")
                    if not active_ranges:
                        break
                    # As chunks are downloaded sequentially, the task with the slowest chunk will be the one
                    # with the lowest start position
                    byte_range = min(active_ranges)
                    gLogger.debug(f"Adding additional source ({worker.se}) for range {byte_range=}")
                    pcallback = progress_callback(progress, summary_task_id, worker.task_id)
                    ccallback = cancel_callback(progress, summary_task_id, worker.task_id)

                    async def completion_callback(tasks=tasks[byte_range]):
                        for t in tasks:
                            if not t.done():
                                gLogger.debug(f"Cancelling duplicate download task {t.get_name()}")
                                t.cancel()

                    callback = DownloadWorkerCallback(
                        mm,
                        byte_range[0],
                        pcallback,
                        cancel_callback=ccallback,
                        completion_callback=lambda: tg.create_task(completion_callback()),
                    )
                    task = tg.create_task(worker.download(callback, byte_range=byte_range))
                    tasks[byte_range].append(task)

            # Keep only the finished task for each byte range
            for byte_range, ts in tasks.items():
                tasks[byte_range] = [t for t in ts if not t.cancelled()][0]

            # Combine the checksums from all chunks
            full_checksum = reduce(lambda a, b: a & b, (t.result() for _, t in sorted(tasks.items())))
            checksums = [("Multi-source", full_checksum)]

    if len(checksums) == 0:
        raise NotImplementedError(f"No replicas found for {lfn}")

    for se, checksum in checksums:
        gLogger.info(f"Checksum for {lfn} at {se}: {checksum} == {expected_checksum:#010x}")
        if checksum.checksum != expected_checksum:
            raise NotImplementedError(f"Checksum mismatch for {se}: {checksum} != {expected_checksum:#010x}")
    gLogger.notice("All checksums match!")


async def download_replica(
    client: httpx.AsyncClient, se: str, url: str, dest_path: str | None, progress: Progress, task_id: int
) -> Adler32:
    """Download a single URL to disk, updating the given Rich task."""
    checksum = Adler32()

    async with AsyncExitStack() as stack:
        response = await stack.enter_async_context(client.stream("GET", url))
        response.raise_for_status()
        total = int(response.headers.get("Content-Length", 0))
        progress.update(task_id, total=total)

        out_file = stack.enter_context(open(dest_path, "wb")) if dest_path else None

        async for chunk in response.aiter_bytes(chunk_size=32_768):
            checksum.update(chunk)
            if out_file:
                out_file.write(chunk)
            progress.update(task_id, advance=len(chunk))

    return se, checksum


def check_file(f, tree_name, branch, event):
    interpretation = None
    if tree_name in ["Event", "FileRecords"]:
        interpretation = uproot.interpretation.jagged.AsJagged(uproot.interpretation.numerical.AsDtype("u1"))
    start = None
    if branch and event:
        f[tree_name][branch].array(interpretation, entry_start=event, entry_stop=event + 1, library="np")
    elif branch:
        for start in range(0, f[tree_name].num_entries, STEP_SIZE):
            f[tree_name][branch].array(interpretation, entry_start=start, entry_stop=start + STEP_SIZE, library="np")
    else:
        for branch in f[tree_name].keys():
            gLogger.info(f"Checking {tree_name}/{branch}")
            for start in range(0, f[tree_name].num_entries, STEP_SIZE):
                f[tree_name][branch].array(
                    interpretation, entry_start=start, entry_stop=start + STEP_SIZE, library="np"
                )


if __name__ == "__main__":
    main()
