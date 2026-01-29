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

import fnmatch
import json
import tarfile
from pathlib import Path

import zstandard as zstd


EXAMPLE_LOGS_DIR = Path(__file__).parent / "examples" / "logs"


def load_example(job_id: int) -> tuple[int, int, dict[str, bytes]]:
    """Load an example log file for the given job ID."""
    archive_path = EXAMPLE_LOGS_DIR / f"{job_id}.tar.zst"

    # If compressed archive exists, extract files from it
    if archive_path.exists():
        files = {}
        # Decompress and read files directly from the archive without writing to disk
        with open(archive_path, "rb") as compressed:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(compressed) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as tar:
                    for member in tar:
                        if member.isfile():
                            # Extract just the filename from the path (removes job_id directory prefix)
                            filename = Path(member.name).name
                            file_obj = tar.extractfile(member)
                            if file_obj:
                                files[filename] = file_obj.read()
    else:
        # Fall back to reading from uncompressed directory
        files = {}
        for file in (EXAMPLE_LOGS_DIR / f"{job_id}").iterdir():
            files[file.name] = file.read_bytes()

    # Extract the transform and task IDs from the prodConf filename
    *_, transform_id, task_id, _ = fnmatch.filter(files, "prodConf*_1.*")[0].split("_")
    return int(transform_id), int(task_id), files


def deterministic_dump(adapter, obj) -> str:
    # Workaround for https://github.com/pydantic/pydantic/issues/7424
    return json.dumps(adapter.dump_python(obj, mode="json"), indent=2, sort_keys=True)


def generate_fixture_jobid(jobid: int | None = None):
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.job_analyzer import Job
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.test.Test_log_analysis import (
        PreAnalysisTypeAdapter,
    )

    if jobid is not None:
        print(f"Generating fixture for job ID {jobid}")
        jobid = int(jobid)

    # Generate reference results from examples
    for path in EXAMPLE_LOGS_DIR.glob("*.tar.zst"):
        job_id = int(path.name.removesuffix(".tar.zst"))
        if jobid is not None and job_id != jobid:
            continue
        transform_id, task_id, files = load_example(job_id)
        expected_path = EXAMPLE_LOGS_DIR / f"{job_id}.json"
        expected_path.write_text(
            deterministic_dump(PreAnalysisTypeAdapter, Job(transform_id, task_id, files).problems_by_lfn)
        )
        print(f"Wrote {expected_path}")
