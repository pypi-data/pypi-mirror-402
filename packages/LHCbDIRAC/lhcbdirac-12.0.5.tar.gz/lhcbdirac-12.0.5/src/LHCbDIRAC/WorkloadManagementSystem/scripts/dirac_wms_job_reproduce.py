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
"""Reproduce DIRAC jobs locally for debugging and testing purposes.

This script helps you download job logs and execute jobs locally using the same
environment and inputs as the original job on the grid.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Annotated

import DIRAC

app = typer.Typer(
    name="dirac-wms-job-reproduce",
    help="Reproduce DIRAC jobs locally for debugging and testing",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def parse_identifier(identifier: str) -> tuple[str, str | int]:
    """Parse the input identifier and determine its type.

    Returns:
        tuple of (identifier_type, value) where identifier_type is one of:
        - "job_id": integer job ID
        - "logse_url": root:// URL to LogSE
        - "logse_lfn": LFN path to log file
    """
    # Check if it's a LogSE URL
    if identifier.startswith("root://"):
        return ("logse_url", identifier)

    # Check if it's a LogSE LFN (with or without LFN: prefix)
    # Format: /lhcb/.../LOG/... or LFN:/lhcb/.../LOG/...
    lfn = identifier.removeprefix("LFN:")
    if lfn.startswith("/lhcb/") and "/LOG/" in lfn:
        return ("logse_lfn", lfn)

    # Try to parse as job ID
    try:
        job_id = int(identifier)
        return ("job_id", job_id)
    except ValueError:
        console.print(f"[red]Could not parse identifier: {identifier}[/red]")
        console.print("[yellow]Expected one of:[/yellow]")
        console.print("  - Job ID: 1234567")
        console.print("  - LogSE URL: root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/...")
        console.print("  - LogSE LFN: /lhcb/LHCb/Collision25/LOG/00329360/0000/00001030.zip")
        console.print("  - LogSE LFN: LFN:/lhcb/LHCb/Collision25/LOG/00329360/0000/00001030.zip")
        raise typer.Exit(1)


def get_log_path_from_logse_url(logse_url: str) -> str:
    """Extract the log path from a LogSE URL.

    Example input: root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/lhcb/LHCb/Collision25/LOG/00329360/0000/00001030.zip
    Returns: lhcb/LHCb/Collision25/LOG/00329360/0000/00001030
    """
    # Extract path after logSE/
    match = re.search(r"logSE/(.+?)(\.zip)?$", logse_url)
    if not match:
        console.print(f"[red]Could not parse LogSE URL: {logse_url}[/red]")
        raise typer.Exit(1)

    log_path = match.group(1)
    console.print(f"[green]Extracted log path:[/green] {log_path}")
    return log_path


def get_log_path_from_logse_lfn(logse_lfn: str) -> str:
    """Extract the log path from a LogSE LFN.

    Example input: /lhcb/LHCb/Collision25/LOG/00329360/0000/00001030.zip
    Returns: lhcb/LHCb/Collision25/LOG/00329360/0000/00001030
    """
    # Remove leading slash and .zip extension if present
    log_path = logse_lfn.lstrip("/")
    if log_path.endswith(".zip"):
        log_path = log_path[:-4]

    console.print(f"[green]Extracted log path:[/green] {log_path}")
    return log_path


def get_log_path_from_job_id(job_id: int) -> str:
    """Get the EOS log path for a given job ID.

    Queries DIRAC for the job parameters to find the log URL, then extracts
    the EOS path from it.
    """
    console.print(f"[blue]Fetching job parameters for job {job_id}...[/blue]")

    from DIRAC.Interfaces.API.Dirac import Dirac

    dirac = Dirac()
    result = dirac.getJobParameters(job_id)

    if not result["OK"]:
        console.print(f"[red]Failed to get job parameters: {result['Message']}[/red]")
        raise typer.Exit(1)

    params = result["Value"]

    # Extract log path from 'Log URL' parameter
    # Format: '<a href="https://lhcb-dirac-logse.web.cern.ch:443/lhcb/MC/2024/LOG/00335034/0000/00000030/">Log file directory</a>'
    log_url_param = params.get("Log URL", "")

    url_match = re.search(r'href="([^"]+)"', log_url_param)
    if not url_match:
        console.print(f"[red]No Log URL found in job parameters[/red]")
        console.print(f"[dim]Available params: {list(params.keys())}[/dim]")
        raise typer.Exit(1)

    log_url = url_match.group(1)

    # Extract path from URL (after the hostname)
    # URL format: https://lhcb-dirac-logse.web.cern.ch:443/lhcb/MC/2024/LOG/...
    path_match = re.search(r"https?://[^/]+(/lhcb/.+?)/?$", log_url)
    if not path_match:
        console.print(f"[red]Could not extract path from Log URL: {log_url}[/red]")
        raise typer.Exit(1)

    log_path = path_match.group(1).lstrip("/")
    console.print(f"[green]Found log path:[/green] {log_path}")

    return log_path


@app.command(name="download")
def download_job(
    identifier: Annotated[
        str,
        typer.Argument(help="Job ID, LogSE URL, or LogSE LFN"),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Directory to download job files to (default: creates temp dir)"),
    ] = None,
    keep_zip: Annotated[bool, typer.Option("--keep-zip", help="Keep the downloaded zip file")] = False,
):
    """Download job logs and set up reproducer environment.

    Accepts three identifier formats:
    - Job ID: 1234567
    - LogSE URL: root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/...
    - LogSE LFN: /lhcb/LHCb/Collision25/LOG/00329360/0000/00001030.zip

    This command:
    1. Resolves the identifier to get the job's log location
    2. Downloads the job logs from EOS
    3. Extracts the logs to a directory

    You can then run the job locally using the 'run' command.
    """

    # Check for conflicting environment variables that would interfere with job execution
    conflicting_vars = []
    if "JOBID" in os.environ:
        conflicting_vars.append(("JOBID", os.environ["JOBID"]))
    if "DIRACJOBID" in os.environ:
        conflicting_vars.append(("DIRACJOBID", os.environ["DIRACJOBID"]))

    if conflicting_vars:
        console.print()
        console.print(f"[red]{'🐲 Dragons! ' * 8}[/red]")
        console.print()
        console.print("[red]Error: Conflicting environment variables detected[/red]")
        console.print()
        console.print("The following environment variables are set and will cause nasty things to happen:")
        for var_name, var_value in conflicting_vars:
            console.print(f"  [yellow]{var_name}[/yellow] = {var_value}")
        console.print()
        console.print("Please unset these variables before running this script:")
        for var_name, _ in conflicting_vars:
            console.print(f"  [cyan]unset {var_name}[/cyan]")
        console.print()
        console.print(f"[red]{'🐲 Dragons! ' * 8}[/red]")
        console.print()
        raise typer.Exit(1)

    DIRAC.initialize()

    # Parse the identifier
    id_type, value = parse_identifier(identifier)

    # Resolve to job ID and log path
    if id_type == "job_id":
        job_id = value
        log_path = get_log_path_from_job_id(job_id)
    elif id_type == "logse_url":
        log_path = get_log_path_from_logse_url(value)
        # We don't have a job ID in this case, just use the log path for identification
        job_id = None
    elif id_type == "logse_lfn":
        log_path = get_log_path_from_logse_lfn(value)
        # We don't have a job ID in this case, just use the log path for identification
        job_id = None
    else:
        console.print(f"[red]Unknown identifier type: {id_type}[/red]")
        raise typer.Exit(1)

    # Create output directory
    if output_dir is None:
        if job_id:
            output_dir = Path(tempfile.mkdtemp(prefix=f"job_{job_id}_"))
        else:
            output_dir = Path(tempfile.mkdtemp(prefix="job_"))
        console.print(f"[blue]Created temporary directory:[/blue] {output_dir}")
    else:
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[blue]Using output directory:[/blue] {output_dir}")

    # Use log path basename for zip filename if we don't have a job ID
    if job_id:
        zip_file = output_dir / f"{job_id}.zip"
    else:
        zip_basename = Path(log_path).name
        zip_file = output_dir / f"{zip_basename}.zip"

    # Download with xrdcp
    xrd_url = f"root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/{log_path}.zip"
    console.print(f"[blue]Downloading logs from EOS...[/blue]")
    console.print(f"[dim]Source: {xrd_url}[/dim]")

    try:
        subprocess.run(
            ["xrdcp", xrd_url, str(zip_file)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to download logs:[/red]")
        console.print(e.stderr.decode())
        raise typer.Exit(1)
    except FileNotFoundError:
        console.print("[red]xrdcp command not found. Please ensure xrootd client is installed.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Downloaded to {zip_file}[/green]")

    # Unzip
    console.print(f"[blue]Extracting logs...[/blue]")
    try:
        subprocess.run(
            ["unzip", "-q", str(zip_file), "-d", str(output_dir)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to extract logs:[/red]")
        console.print(e.stderr.decode())
        raise typer.Exit(1)

    # Find the extracted directory (usually there's one subdirectory)
    subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if len(subdirs) == 1:
        job_dir = subdirs[0]
    else:
        # Multiple or no subdirectories, use output_dir
        job_dir = output_dir

    console.print(f"[green]Logs extracted to {job_dir}[/green]")

    # Remove zip file unless requested to keep it
    if not keep_zip:
        zip_file.unlink()
        console.print(f"[dim]Removed {zip_file}[/dim]")

    # Display next steps
    console.print()
    if job_id:
        title_msg = f"[green]Job logs downloaded successfully![/green]\n\n[blue]Job ID:[/blue] {job_id}\n"
    else:
        title_msg = f"[green]Job logs downloaded successfully![/green]\n\n"

    console.print(
        Panel.fit(
            f"{title_msg}"
            f"[blue]Job directory:[/blue] {job_dir}\n\n"
            f"[yellow]Next steps:[/yellow]\n"
            f"  1. Review the job files in {job_dir}\n"
            f"  2. Run the job locally:\n"
            f"     [cyan]dirac-wms-job-reproduce run {job_dir}[/cyan]\n"
            f"     or: [cyan]cd {job_dir} && (lb-dirac) dirac-jobexec jobDescription.xml[/cyan]\n"
            f"  3. Create a minimal reproducer if needed for bug reports\n\n",
            title="Download Complete",
            border_style="green",
        )
    )


@app.command(name="run")
def run_reproducer(
    job_dir: Annotated[Path, typer.Argument(help="Job directory (from 'download' command)")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show commands without executing")] = False,
    download: Annotated[
        bool, typer.Option("--download", help="Download input files (sets inputDataPolicy to DownloadInputData)")
    ] = False,
    protocol: Annotated[
        bool, typer.Option("--protocol", help="Access files by protocol (sets inputDataPolicy to InputDataByProtocol)")
    ] = False,
):
    """Run the reproducer from a downloaded job directory.

    This command:
    1. Extracts input data LFNs from jobDescription.xml
    2. Generates the XML catalog with bookkeeping information
    3. Executes the job locally using dirac-jobexec

    The job will run in the same environment as on the grid, using the original
    jobDescription.xml and input files.

    By default, uses InputDataByProtocol. Use --download to download files locally first,
    or --protocol to explicitly use protocol-based access.
    """
    # Validate flags
    if download and protocol:
        console.print("[red]Error: Cannot specify both --download and --protocol[/red]")
        raise typer.Exit(1)

    # Check for conflicting environment variables that would interfere with job execution
    conflicting_vars = []
    if "JOBID" in os.environ:
        conflicting_vars.append(("JOBID", os.environ["JOBID"]))
    if "DIRACJOBID" in os.environ:
        conflicting_vars.append(("DIRACJOBID", os.environ["DIRACJOBID"]))

    if conflicting_vars:
        console.print()
        console.print(f"[red]{'🐲 Dragons! ' * 8}[/red]")
        console.print()
        console.print("[red]Error: Conflicting environment variables detected[/red]")
        console.print()
        console.print("The following environment variables are set and will cause nasty things to happen:")
        for var_name, var_value in conflicting_vars:
            console.print(f"  [yellow]{var_name}[/yellow] = {var_value}")
        console.print()
        console.print("Please unset these variables before running this script:")
        for var_name, _ in conflicting_vars:
            console.print(f"  [cyan]unset {var_name}[/cyan]")
        console.print()
        console.print(f"[red]{'🐲 Dragons! ' * 8}[/red]")
        console.print()
        raise typer.Exit(1)

    # Determine input data policy
    if download:
        input_data_policy = "DIRAC.WorkloadManagementSystem.Client.DownloadInputData"
    else:
        # Default to protocol-based access
        input_data_policy = "DIRAC.WorkloadManagementSystem.Client.InputDataByProtocol"

    DIRAC.initialize()

    job_dir = Path(job_dir).resolve()

    if not job_dir.exists():
        console.print(f"[red]Job directory does not exist: {job_dir}[/red]")
        raise typer.Exit(1)

    # Check for jobDescription.xml
    job_desc = job_dir / "jobDescription.xml"
    if not job_desc.exists():
        console.print(f"[red]jobDescription.xml not found in {job_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Working directory:[/blue] {job_dir}")
    console.print(f"[blue]Job description:[/blue] {job_desc}")

    # Extract input data LFNs and generate XML catalog
    console.print(f"[blue]Extracting input data LFNs from jobDescription.xml...[/blue]")

    try:
        # Read jobDescription.xml and extract LFNs
        with open(job_desc) as f:
            job_xml = f.read()

        # Find InputData parameter (handles both CDATA and plain text)
        # Format 1: <![CDATA[/lhcb/.../file1.dst;/lhcb/.../file2.dst;...]]>
        # Format 2: <value>/lhcb/.../file1.dst;/lhcb/.../file2.dst;...</value>
        lfn_match = re.search(
            r'name="InputData"[^>]*>.*?<!\[CDATA\[(.*?)\]\]>|name="InputData"[^>]*><value>(.*?)</value>',
            job_xml,
            re.DOTALL,
        )

        if lfn_match:
            input_data = lfn_match.group(1) or lfn_match.group(2) or ""
            # Split by semicolons - handles format like:
            # /lhcb/.../file1.dst;/lhcb/.../file2.dst;...
            lfns = [lfn.strip() for lfn in input_data.split(";") if lfn.strip() and lfn.strip().startswith("/lhcb")]

            if lfns:
                console.print(f"[green]Found {len(lfns)} input file(s)[/green]")
                for lfn in lfns[:5]:  # Show first 5
                    console.print(f"  [dim]{lfn}[/dim]")
                if len(lfns) > 5:
                    console.print(f"  [dim]... and {len(lfns) - 5} more[/dim]")
            else:
                console.print("[yellow]No input files found in job description[/yellow]")
                lfns = []
        else:
            console.print("[yellow]No InputData parameter found in job description[/yellow]")
            lfns = []

    except Exception as e:
        console.print(f"[red]Failed to parse jobDescription.xml: {e}[/red]")
        raise typer.Exit(1)

    # Generate commands
    commands = []

    if lfns:
        # Generate XML catalog
        policy_name = input_data_policy.split(".")[-1]
        console.print(f"[blue]Generating XML catalog from {len(lfns)} LFN(s)...[/blue]")
        console.print(f"[dim]Input data policy: {policy_name}[/dim]")

        from DIRAC.Interfaces.API.Dirac import Dirac

        dirac = Dirac()
        catalog_result = dirac.getInputDataCatalog(lfns, [], "pool_xml_catalog.xml", inputDataPolicy=input_data_policy)

        if not catalog_result["OK"]:
            console.print(f"[red]Failed to generate XML catalog: {catalog_result['Message']}[/red]")
            raise typer.Exit(1)

        print(catalog_result)

        console.print(f"[green]✓ XML catalog generated[/green]")

    # Execute job
    console.print(f"[blue]Preparing to execute job...[/blue]")

    jobexec_cmd = [
        "dirac-jobexec",
        str(job_desc),
    ]

    commands.append(("Execute job", jobexec_cmd, None))

    # Show or execute commands
    if dry_run:
        console.print()
        console.print("[yellow]Dry run mode - commands that would be executed:[/yellow]")
        console.print()

        for i, (desc, cmd, stdin_data) in enumerate(commands, 1):
            console.print(f"[cyan]{i}. {desc}:[/cyan]")
            if stdin_data:
                console.print(f"   echo {repr(stdin_data)} | {' '.join(cmd)}")
            else:
                console.print(f"   {' '.join(cmd)}")
            console.print()

        console.print("[yellow]Run without --dry-run to execute[/yellow]")
    else:
        # Execute commands
        console.print()
        console.print("[green]Executing reproducer...[/green]")
        console.print()

        for desc, cmd, stdin_data in commands:
            console.print(f"[cyan]Running: {desc}[/cyan]")
            console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

            try:
                if stdin_data:
                    result = subprocess.run(
                        cmd,
                        input=stdin_data,
                        text=True,
                        cwd=job_dir,
                        check=True,
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        cwd=job_dir,
                        check=True,
                    )

                console.print(f"[green]✓ {desc} completed[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]✗ {desc} failed with exit code {e.returncode}[/red]")
                raise typer.Exit(1)
            except FileNotFoundError:
                console.print(f"[red]Command not found: {cmd[0]}[/red]")
                raise typer.Exit(1)

            console.print()

        console.print("[green]Job execution completed![/green]")


@app.command(name="reproduce")
def reproduce_job(
    identifier: Annotated[
        str,
        typer.Argument(help="Job ID, LogSE URL, or LogSE LFN"),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", "-o", help="Directory to download job files to (default: creates temp dir)"),
    ] = None,
    keep_zip: Annotated[bool, typer.Option("--keep-zip", help="Keep the downloaded zip file")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show commands without executing")] = False,
    download: Annotated[
        bool, typer.Option("--download", help="Download input files (sets inputDataPolicy to DownloadInputData)")
    ] = False,
    protocol: Annotated[
        bool, typer.Option("--protocol", help="Access files by protocol (sets inputDataPolicy to InputDataByProtocol)")
    ] = False,
):
    """Download and run a job reproducer in one step.

    Accepts three identifier formats:
    - Job ID: 1234567
    - LogSE URL: root://eoslhcb.cern.ch//eos/lhcb/grid/prod/lhcb/logSE/...
    - LogSE LFN: /lhcb/LHCb/Collision25/LOG/00329360/0000/00001030.zip

    This is a convenience command that combines 'download' and 'run'.
    Equivalent to running:
      dirac-wms-job-reproduce download <IDENTIFIER> -o <OUTPUT_DIR>
      dirac-wms-job-reproduce run <OUTPUT_DIR> [--download|--protocol]

    By default, uses InputDataByProtocol. Use --download to download files locally first,
    or --protocol to explicitly use protocol-based access.
    """
    # Download the job
    download_job(identifier, output_dir, keep_zip)

    # Find the job directory
    if output_dir is None:
        console.print("[red]Cannot automatically determine job directory from temp dir[/red]")
        console.print("[yellow]Please use 'download' and 'run' commands separately[/yellow]")
        raise typer.Exit(1)

    output_dir = Path(output_dir).resolve()
    subdirs = [d for d in output_dir.iterdir() if d.is_dir()]

    if len(subdirs) == 1:
        job_dir = subdirs[0]
    else:
        job_dir = output_dir

    # Add a separator
    console.print()
    console.rule("[bold]Starting Job Execution[/bold]")
    console.print()

    # Run the reproducer
    run_reproducer(job_dir, dry_run, download, protocol)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
