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

import argparse
import asyncio
import json
from pathlib import Path

from pydantic import TypeAdapter
import pytest

if __name__ == "__main__":
    import DIRAC

    DIRAC.initialize()

from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.job_analyzer import (
    LFNDebugInfo,
    AggregatedLFNDebugInfo,
)
from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.prod_analyzer import (
    GroupedProblems,
)
from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis import (
    analyze_prod,
    summarize_prod,
    group_by_problem,
)
from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis import output
from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.test import deterministic_dump


ResultAdapter = TypeAdapter(list[LFNDebugInfo])
AggregatedResultAdapter = TypeAdapter(list[AggregatedLFNDebugInfo])
GroupedResultAdapter = TypeAdapter(GroupedProblems)
EXAMPLES_DIR = Path(__file__).parent / "examples" / "prods"
EXAMPLE_PROD_IDS = [int(x.name) for x in EXAMPLES_DIR.glob("*/")]


@pytest.mark.parametrize("prod_id", EXAMPLE_PROD_IDS)
def test_summarize_prod(prod_id: int):
    raw = ResultAdapter.validate_json((EXAMPLES_DIR / f"{prod_id}" / "raw.json").read_text())
    actual = AggregatedResultAdapter.dump_python(summarize_prod(raw), mode="json")
    # (EXAMPLES_DIR / f"{prod_id}" / "summarized.json").write_text(deterministic_dump(AggregatedResultAdapter, actual))
    expected = json.loads((EXAMPLES_DIR / f"{prod_id}" / "summarized.json").read_text())
    assert actual == expected


@pytest.mark.parametrize("prod_id", EXAMPLE_PROD_IDS)
def test_group_results(prod_id: int):
    summarized = AggregatedResultAdapter.validate_json((EXAMPLES_DIR / f"{prod_id}" / "summarized.json").read_text())
    actual = GroupedResultAdapter.dump_python(group_by_problem(summarized), mode="json")
    # (EXAMPLES_DIR / f"{prod_id}" / "grouped.json").write_text(deterministic_dump(GroupedResultAdapter, actual))
    expected = json.loads((EXAMPLES_DIR / f"{prod_id}" / "grouped.json").read_text())
    assert actual == expected


@pytest.mark.parametrize("prod_id", EXAMPLE_PROD_IDS)
def test_summarized_markdown(prod_id: int):
    grouped = GroupedResultAdapter.validate_json((EXAMPLES_DIR / f"{prod_id}" / "grouped.json").read_text())
    actual_markdown = output.to_markdown(grouped, is_summary=True)
    # (EXAMPLES_DIR / f"{prod_id}" / "summarized.md").write_text(actual_markdown)
    expected_markdown = (EXAMPLES_DIR / f"{prod_id}" / "summarized.md").read_text()
    assert actual_markdown == expected_markdown


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate reference results of summarization")
    parser.add_argument("prod_id", type=int, help="Production ID")
    parser.add_argument("lfns", nargs="+", help="LFNs to analyze")
    args = parser.parse_args()

    prod_path = EXAMPLES_DIR / f"{args.prod_id}"
    raw_analysis = asyncio.run(analyze_prod(args.prod_id, lfns=args.lfns))
    summarized_analysis = summarize_prod(raw_analysis)
    grouped_analysis = group_by_problem(summarized_analysis)
    full_markdown = output.to_markdown(grouped_analysis, is_summary=False)
    summary_markdown = output.to_markdown(grouped_analysis, is_summary=True)

    prod_path.mkdir(exist_ok=False)
    (prod_path / "raw.json").write_text(deterministic_dump(ResultAdapter, raw_analysis))
    (prod_path / "summarized.json").write_text(deterministic_dump(AggregatedResultAdapter, summarized_analysis))
    (prod_path / "grouped.json").write_text(deterministic_dump(GroupedResultAdapter, grouped_analysis))
    (prod_path / "full.md").write_text(full_markdown)
    (prod_path / "summarized.md").write_text(summary_markdown)
    print(f"Wrote results to {prod_path}")
