#!/usr/bin/env python
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
import argparse
import asyncio
from pathlib import Path
import re
import shutil


import DIRAC
from DIRAC.Core.Security.Properties import PRODUCTION_MANAGEMENT
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown


def main():
    parser = argparse.ArgumentParser(description="Manage LHCbDIRAC production requests")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparser = subparsers.add_parser("show-requests", help="Show the current status of the production requests")
    subparser.set_defaults(func=show_requests)
    subparser.add_argument("--execute-actions", action="store_true", help="Execute the actions")

    subparser = subparsers.add_parser("update-metadata", help="Update the metadata stored on GitLab")
    subparser.set_defaults(func=update_metadata)

    subparser = subparsers.add_parser("run-checks", help="Run checks on the production requests")
    subparser.set_defaults(func=run_checks)

    subparser = subparsers.add_parser("debug", help="Debug the production requests")
    subparser.set_defaults(
        func=lambda args: asyncio.run(debug(args.prod_id, summarize=not args.no_summarize, output_dir=args.output_dir))
    )
    subparser.add_argument("prod_id", type=int, nargs="+")
    subparser.add_argument("--no-summarize", action="store_true")
    subparser.add_argument("--output-dir", type=Path)

    subparser = subparsers.add_parser("add-test-case", help="Add a test case for the job ID specified")
    subparser.set_defaults(func=add_test_case)
    subparser.add_argument("job_id", type=int)

    args = parser.parse_args()
    args.func(args)


def show_requests(args):
    DIRAC.initialize()
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools import ProdRequestsGitlabRepo
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.monitoring import (
        analyse_active_productions,
        display_table,
        display_actions,
    )

    if args.execute_actions:
        DIRAC.initialize(security_expression=PRODUCTION_MANAGEMENT)
        match Prompt.ask("Update metadata?", choices=["yes", "no"], default="yes"):
            case "yes":
                update_metadata(args)

    repo = ProdRequestsGitlabRepo(with_auth=args.execute_actions)
    last_update, tables_data, actions = analyse_active_productions(repo)
    console = Console()
    console.rule()
    display_table(console, tables_data)
    console.print(f"Last update: {last_update}")
    console.rule()
    display_actions(console, actions, execute=args.execute_actions)


def update_metadata(args):
    DIRAC.initialize(security_expression=PRODUCTION_MANAGEMENT)
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools import ProdRequestsGitlabRepo
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.monitoring import ACTIVE_PRODUCTION_STATES

    repo = ProdRequestsGitlabRepo(with_auth=True)
    repo.poll(do_status_update=True, states=ACTIVE_PRODUCTION_STATES)


def run_checks(args):
    DIRAC.initialize(security_expression=PRODUCTION_MANAGEMENT)
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools import (
        ProdRequestsGitlabRepo,
        OperationsLogbook,
        do_checks,
    )
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.monitoring import (
        analyse_active_productions,
        display_table,
    )

    repo = ProdRequestsGitlabRepo(with_auth=True)
    logbook = OperationsLogbook()
    last_update, tables_data, _ = analyse_active_productions(repo, states=["checking"])

    console = Console()
    console.rule()
    display_table(console, tables_data)
    console.print(f"Last update: {last_update}")
    console.rule()

    request_ids = {
        str(x[1]): x[0]
        for v in tables_data.values()
        for vv in v.values()
        for vvv in vv.values()
        for vvvv in vvv.values()
        for x in vvvv
    }

    asyncio.run(do_checks(console, logbook, repo, request_ids))


async def debug(prod_ids: list[int], *, summarize: bool = True, output_dir: Path | None = None):
    DIRAC.initialize(security_expression=PRODUCTION_MANAGEMENT)

    from rich import print

    from ..Utilities.ProductionTools.LogAnalysis import analyze_prod, summarize_prod, group_by_problem, output
    from ..Utilities.ProductionTools.LogAnalysis.utils import Progress, ProgressUpdater
    from ..Utilities.ProductionTools.LogAnalysis.prod_analyzer import GroupedProblems

    async def show_production(
        transform_id: int, progress_updater, *, summarize: bool = True
    ) -> tuple[int, dict[str, int], GroupedProblems]:
        all_problems = await analyze_prod(transform_id, progress=progress_updater)
        if summarize:
            all_problems = summarize_prod(all_problems)
        return transform_id, group_by_problem(all_problems)

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=False)

    with Progress() as progress:
        task = progress.add_task("Reading logs", total=None)
        progress_updater = ProgressUpdater(progress, task)
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(show_production(prod_id, progress_updater, summarize=summarize)) for prod_id in prod_ids
            ]
            for coro in asyncio.as_completed(tasks):
                prod_id, grouped = await coro
                raw_markdown = output.to_markdown(grouped, is_summary=summarize)
                print(Markdown(raw_markdown))
                if output_dir:
                    md_path = output_dir / f"{prod_id}.md"
                    md_path.write_text(raw_markdown)
                    print(f"Wrote {md_path}")
                print(f"Analyzed {len(tasks)}")


def add_test_case(args):
    """Add a test case for the job ID specified.

    Downloads job logs, analyzes them, creates fixtures, and prepares a git branch
    for contributing the test case to LHCbDIRAC.

    :param args: Namespace with job_id attribute
    """
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    DIRAC.initialize()
    from DIRAC.Interfaces.API.Dirac import Dirac

    console = Console()
    job_id = args.job_id

    # Check if we're in an LHCbDIRAC repository
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_root = Path(result.stdout.strip())

        # Verify it's actually LHCbDIRAC
        if not (repo_root / "src" / "LHCbDIRAC").exists():
            console.print("[red]Not in LHCbDIRAC repository. Please cd to LHCbDIRAC root.[/red]")
            sys.exit(1)
    except subprocess.CalledProcessError:
        console.print("[red]Not in a git repository. Please cd to LHCbDIRAC root.[/red]")
        sys.exit(1)

    console.print(f"[green]Repository root:[/green] {repo_root}")

    # Get job parameters to find log location
    console.print(f"[blue]Fetching job parameters for {job_id}...[/blue]")
    dirac = Dirac()
    result = dirac.getJobParameters(job_id)

    if not result["OK"]:
        console.print(f"[red]Failed to get job parameters: {result['Message']}[/red]")
        sys.exit(1)

    params = result["Value"]

    # Extract log path from 'Log URL' parameter
    # Format: '<a href="https://lhcb-dirac-logse.web.cern.ch:443/lhcb/MC/2024/LOG/00335034/0000/00000030/">Log file directory</a>'
    # We want: /lhcb/MC/2024/LOG/00335034/0000/00000030/
    log_url_param = params.get("Log URL", "")

    url_match = re.search(r'href="([^"]+)"', log_url_param)
    if not url_match:
        console.print(f"[red]No Log URL found in job parameters[/red]")
        console.print(f"[dim]Available params: {list(params.keys())}[/dim]")
        sys.exit(1)

    log_url = url_match.group(1)
    console.print(f"[green]Log URL:[/green] {log_url}")

    # Extract path from URL (after the hostname)
    # URL format: https://lhcb-dirac-logse.web.cern.ch:443/lhcb/MC/2024/LOG/...
    path_match = re.search(r"https?://[^/]+(/lhcb/.+?)/?$", log_url)
    if not path_match:
        console.print(f"[red]Could not extract path from Log URL: {log_url}[/red]")
        sys.exit(1)

    log_path = path_match.group(1).lstrip("/")

    # Download logs to temporary location
    test_logs_dir = (
        repo_root / "src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/test/examples/logs"
    )
    job_dir = test_logs_dir / str(job_id)

    if job_dir.exists():
        console.print(f"[yellow]Warning: {job_dir} already exists. Overwriting...[/yellow]")
        shutil.rmtree(job_dir)

    job_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        zip_file = tmpdir / f"{job_id}.zip"

        # Download with xrdcp
        console.print(f"[blue]Downloading logs from EOS...[/blue]")
        xrd_url = f"root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/{log_path}.zip"

        try:
            subprocess.run(
                ["xrdcp", xrd_url, str(zip_file)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to download logs: {e.stderr.decode()}[/red]")
            sys.exit(1)

        # Unzip
        console.print(f"[blue]Extracting logs...[/blue]")
        subprocess.run(["unzip", "-q", str(zip_file), "-d", str(job_dir)], check=True)

    console.print(f"[green]Logs extracted to {job_dir}[/green]")

    # Move any files inside subfolders up to job_dir
    for subdir in job_dir.iterdir():
        if subdir.is_dir():
            for file in subdir.iterdir():
                file.rename(job_dir / file.name)
            subdir.rmdir()

    # Compress logs to tar.zst
    console.print(f"[blue]Compressing logs to tar.zst...[/blue]")
    tar_zst_file = test_logs_dir / f"{job_id}.tar.zst"

    try:
        # Create tar and pipe to zstd
        with subprocess.Popen(
            ["tar", "-cf", "-", "-C", str(test_logs_dir), str(job_id)],
            stdout=subprocess.PIPE,
        ) as tar_proc:
            with open(tar_zst_file, "wb") as zst_file:
                subprocess.run(
                    ["zstd", "-T0", "-19"],
                    stdin=tar_proc.stdout,
                    stdout=zst_file,
                    check=True,
                )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to compress: {e}[/red]")
        sys.exit(1)

    console.print(f"[green]Compressed to {tar_zst_file}[/green]")

    # Analyze the job to create the expected JSON output
    console.print(f"[blue]Analyzing job logs...[/blue]")
    from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.test import generate_fixture_jobid

    # Load job files

    reasons_yaml = (
        repo_root / "src/LHCbDIRAC/ProductionManagementSystem/Utilities/ProductionTools/LogAnalysis/reasons.yaml"
    )

    try:
        generate_fixture_jobid(job_id)
        json_file = test_logs_dir / f"{job_id}.json"
        if not json_file.exists():
            raise RuntimeError("Expected JSON output file not created")
        console.print(f"[green]Analysis output written to {json_file}[/green]")
    except NotImplementedError as e:
        from LHCbDIRAC.ProductionManagementSystem.Utilities.ProductionTools.LogAnalysis.test.Test_log_analysis import (
            UPDATE_REFERENCES_ENV_VAR,
            TEST_MODULE_NAME,
        )

        console.print(f"[red]Log analysis not implemented: {e}[/red]")
        console.print(f"[yellow]Please make the necessary modifications in {reasons_yaml}[/yellow]")
        console.print()
        console.print("[blue]Then run the test with:[/blue]")
        console.print(f"  [yellow]{UPDATE_REFERENCES_ENV_VAR}=1 pytest -k '{TEST_MODULE_NAME} and {job_id}'[/yellow]")
        console.print()
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to analyze logs: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Always clean up uncompressed directory - tar.zst has all needed data
        if job_dir.exists():
            shutil.rmtree(job_dir)

    # Add files
    console.print(f"[blue]Adding files to git...[/blue]")
    subprocess.run(["git", "add", str(tar_zst_file.relative_to(repo_root))], check=True, cwd=repo_root)
    subprocess.run(["git", "add", str(json_file.relative_to(repo_root))], check=True, cwd=repo_root)

    console.print(f"[green]✓ Test case added successfully![/green]")
    console.print()
    console.print("[blue]Next steps:[/blue]")
    console.print(f"  1. Commit changes: [yellow]git commit -m 'Add log analysis test case for job {job_id}'[/yellow]")
    console.print(f"  3. Push branch: [yellow]git push -u fork <branch>[/yellow]")
    console.print(f"  4. Open a merge request on GitLab")
    console.print()
    console.print(f"[dim]Files: {tar_zst_file.name}, {json_file.name}[/dim]")


if __name__ == "__main__":
    main()
