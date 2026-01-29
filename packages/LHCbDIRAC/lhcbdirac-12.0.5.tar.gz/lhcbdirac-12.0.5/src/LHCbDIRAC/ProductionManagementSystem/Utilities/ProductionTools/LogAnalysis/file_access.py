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
    "read_zip",
    "file_exists",
]

import asyncio
import io
from zipfile import ZipFile

import pyxrootd.client

from DIRAC.Core.Utilities.ReturnValues import returnValueOrRaise


async def _get_xrd_file(log_lfn: str) -> pyxrootd.client.File | None:
    """Get a pyxrootd file object for the given LFN.

    This function will first try to open the file directly from CERN, and if that fails
    it will try to get the PFN from DIRAC and open that. This might happen if the file
    is not yet available on CERN's EOS and is still in FAILOVER.
    """
    loop = asyncio.get_running_loop()

    f = pyxrootd.client.File()
    status, _ = await loop.run_in_executor(
        None, f.open, f"root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/{log_lfn}"
    )
    if status["ok"]:
        return f

    from DIRAC.DataManagementSystem.Client.DataManager import DataManager

    result = await loop.run_in_executor(None, DataManager().getReplicas, log_lfn)
    if result["OK"] and (log_pfns := result["Value"]["Successful"].get(log_lfn)):
        for log_pfn in log_pfns.values():
            print("Did not find log file at CERN, trying FAILOVER:", log_pfn)
            f = pyxrootd.client.File()
            status, _ = await loop.run_in_executor(None, f.open, log_pfn)
            if status["ok"]:
                return f


async def read_zip(job_id: int, log_lfn: str) -> dict[str, bytes]:
    loop = asyncio.get_running_loop()
    cancelled = False

    def handle_read(status, data: bytes, host_list):
        if not cancelled:
            loop.call_soon_threadsafe(queue.put_nowait, (status, data))

    queue = asyncio.Queue()
    f = await _get_xrd_file(log_lfn)
    if f is None:
        print("Failed to open log file:", log_lfn)
        return job_id, {}

    status = f.read(callback=handle_read)
    if not status["ok"]:
        raise NotImplementedError(log_lfn, status)

    status, data = await asyncio.wait_for(queue.get(), 30)
    if not status["ok"]:
        raise NotImplementedError(log_lfn, status)

    status, _ = await loop.run_in_executor(None, f.close)
    if not status["ok"]:
        raise NotImplementedError(log_lfn, status)

    zf = ZipFile(io.BytesIO(data))
    files = {}
    for zi in zf.infolist():
        with zf.open(zi) as f:
            # Only read the first 100 MiB to avoid large files taking too long
            if zi.file_size > 100 * 1024**2:
                print(
                    f"Warning file for {job_id} is {zi.file_size / 1024**2:.1f} MiB, "
                    f"only reading first and last 10 MiB from {log_lfn}:{zi.filename}"
                )
                files[zi.filename.split("/", 1)[1]] = f.read(10 * 1024**2)
                files[zi.filename.split("/", 1)[1]] += b"\nTRUNCATED\n"
                f.seek(zi.file_size - 10 * 1024**2)
                files[zi.filename.split("/", 1)[1]] += f.read()
            else:
                files[zi.filename.split("/", 1)[1]] = f.read()

    return job_id, files


async def file_exists(log_lfn: str) -> bool:
    """Check if the file exists on the XRootD server."""
    f = await _get_xrd_file(log_lfn)
    if f is not None:
        await asyncio.get_running_loop().run_in_executor(None, f.close)
        return True
    return False
