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

import json
import os

import pytest
from pydantic import TypeAdapter

from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.job_analyzer import Job, LFNDebugInfo

from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.test import (
    deterministic_dump,
    generate_fixture_jobid,
    load_example,
    EXAMPLE_LOGS_DIR,
)

TEST_CASES = [int(x.name.removesuffix(".tar.zst")) for x in EXAMPLE_LOGS_DIR.glob("*.tar.zst")]
PreAnalysisTypeAdapter = TypeAdapter(dict[str, LFNDebugInfo])

UPDATE_REFERENCES_ENV_VAR = "LHCBDIRAC_TESTING_LOG_ANALYSIS_UPDATE_REFERENCES"
TEST_MODULE_NAME = __name__.rsplit(".", 1)[-1]  # "Test_log_analysis"


@pytest.mark.parametrize("job_id", TEST_CASES)
def test_log_analysis(job_id: int):
    expected_result_path = EXAMPLE_LOGS_DIR / f"{job_id}.json"

    transform_id, task_id, files = load_example(job_id)
    job = Job(transform_id, task_id, files)
    actual_result = PreAnalysisTypeAdapter.dump_python(job.problems_by_lfn)

    if os.environ.get(UPDATE_REFERENCES_ENV_VAR):
        expected_result_path.write_text(deterministic_dump(PreAnalysisTypeAdapter, job.problems_by_lfn))
        pytest.skip(f"Updated reference file {expected_result_path}")

    if not expected_result_path.is_file():
        pytest.fail(
            f"Reference file {expected_result_path} does not exist.\n"
            f"Set {UPDATE_REFERENCES_ENV_VAR}=1 to create it."
        )

    expected_result = json.loads(expected_result_path.read_text())

    if actual_result != expected_result:
        pytest.fail(
            f"Result mismatch for job {job_id}.\n" f"Set {UPDATE_REFERENCES_ENV_VAR}=1 to update the reference file."
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--jobid", type=int, help="Only generate reference results for this job ID")
    args = parser.parse_args()

    generate_fixture_jobid(args.jobid)
