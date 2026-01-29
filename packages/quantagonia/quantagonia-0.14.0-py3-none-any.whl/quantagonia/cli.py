# ruff: noqa: BLE001, D417
import datetime
import importlib.metadata
import json
import os
import pathlib
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from typer import Context
from typing_extensions import Annotated
from yaspin import yaspin

from quantagonia.cloud.cloud_runner import build_specs_list
from quantagonia.cloud.enums import JobStatus
from quantagonia.cloud.https_client import HTTPSClient
from quantagonia.cloud.solver_log import SolverLog
from quantagonia.parameters import HybridSolverParameters
from quantagonia.parser.solution_parser import SolutionParser

app = typer.Typer(help="CLI for Quantagonia's cloud-based HybridSolver.")
console = Console()


@dataclass
class AppState:
    api_key: str
    poll_frequency: int = 1


###
# Helpers that minimize code duplication
###


def _exit_with_error(error_msg: str) -> None:
    console.print(f"[red]Error:[/red] {error_msg}")
    sys.exit(1)


def _submit(
    client: HTTPSClient,
    problem_file: str,
    params_file: Optional[str],
    tag: str,
    context: str,
    quiet: bool,
    **cl_arguments,
) -> str:
    # check if file exists
    if not os.path.isfile(problem_file):
        _exit_with_error(f"File {problem_file} does not exist, exiting...")

    # check file extension
    _, _, extension = pathlib.Path(problem_file).name.partition(".")
    is_mip = extension in ["mps", "lp", "mps.gz", "lp.gz"]
    is_qubo = extension in ["qubo", "qubo.gz"]

    if not is_mip and not is_qubo:
        _exit_with_error(f"File {problem_file} is not in MIP or QUBO file format, exiting...")

    # first collect parameters given as command line arguments
    params_dict = {param: value for param, value in cl_arguments.items() if value not in [None, []]}

    # then overwrite with parameters given in parameter file
    if params_file:
        try:
            with open(params_file) as f:
                given_parameters = json.loads(f.read())
        except FileNotFoundError:
            _exit_with_error(f"Parameter file {params_file} does not exist, exiting...")

        for param, value in given_parameters.items():
            params_dict[param] = value

    # create empty params object
    params = HybridSolverParameters()

    # set collected options
    for param, value in params_dict.items():
        # get setter method from the parameter object
        setter = getattr(params, f"set_{param}")
        setter(value)

    # build specs from params and problem file
    specs = build_specs_list([params], [problem_file], {})

    # start solving job
    if quiet:
        try:
            job_id = client.submit_job(
                problem_files=[problem_file], specs=[specs], tag=tag, context=context, origin="cli"
            )

            print(f"Submitted job with ID: {job_id}")
        except Exception as e:
            _exit_with_error(f"Failed to submit job: {e}")

    else:
        has_error = False
        with yaspin(text="Submitting job to the HybridSolver...", color="yellow") as spinner:
            try:
                job_id = client.submit_job(
                    problem_files=[problem_file], specs=specs, tag=tag, context=context, origin="cli"
                )

                spinner.text = f"Submitted job with ID: {job_id}"
                spinner.ok("✅")
            except Exception as e:
                spinner.text = f"Failed to submit job: {e}"
                spinner.fail("❌")
                has_error = True
        # handle exit outside of spinner
        if has_error:
            sys.exit(1)

    return job_id


def _status(job_id: str, item: int, client: HTTPSClient, spinner: yaspin) -> bool:
    try:
        status = client.get_current_status(job_id)
        status = JobStatus(status[item])

        spinner.text = f"Status: {status.value}"

        if status == JobStatus.created:
            spinner.ok("⏳")
        elif status == JobStatus.running:
            spinner.ok("💻")
        elif status == JobStatus.finished:
            spinner.ok("✅")
        else:
            spinner.ok("❌")
    except Exception:
        spinner.text = f"Failed to retrieve status of job {job_id}"
        spinner.fail("❌")
        return False

    return True


def _monitor_job(job_id: str, client: HTTPSClient, solver_log: SolverLog, poll_frequency: int) -> None:
    """Monitor given job, i.e., print logs, final status etc."""
    # we want the exit to be outside the with statement such that the spinner closes
    has_error = False
    # if monitor is set, keep running and follow logs
    with yaspin(text=f"Processing job {job_id}...", color="yellow") as spinner:
        status = JobStatus.created

        while status in [JobStatus.created, JobStatus.running]:
            time.sleep(poll_frequency)
            try:
                status = client.check_job(job_id)
            except Exception:
                spinner.text = f"Failed to retrieve status for job {job_id}"
                spinner.fail("❌")
                has_error = True
            logs = client.get_current_log(job_id)
            with spinner.hidden():
                solver_log.update_log(logs[0])

        spinner.text = f"Status: {status}"

        if status == JobStatus.finished:
            with spinner.hidden():
                solver_log.update_log(logs[0])
            spinner.ok("✅")
        else:
            spinner.fail("❌")

    if has_error:
        sys.exit(1)


def _retrieve_billing_time(job_id: str, client: HTTPSClient) -> None:
    with yaspin(text=f"Retrieving billing time for job {job_id}...", color="yellow") as spinner:
        try:
            _, time_billed = client.get_results(job_id)
            spinner.text = f"Minutes billed: {time_billed}"
            spinner.ok("✅")
        except Exception:
            spinner.text = "Failed to retrieve billing time."
            spinner.fail("❌")


###
# CLI commands
###
@app.command()
def solve(
    ctx: Context,
    problem_file: str = typer.Argument(help="Path to optimization problem file."),
    params_file: str = typer.Option(None, help="Path to parameter file. If specified, override other options."),
    relative_gap: float = typer.Option(None, help="Stopping criterion: relative gap"),
    absolute_gap: float = typer.Option(None, help="Stopping criterion: absolute gap"),
    timelimit: int = typer.Option(None, help="Stopping criterion: runtime"),
    as_qubo: bool = typer.Option(None, help="Try to solve MIP as MIP and as QUBO"),
    as_qubo_only: bool = typer.Option(None, help="Try to solve MIP only as QUBO"),
    presolve: bool = typer.Option(None, help="Enable (default) or disable presolve"),
    heuristics_only: bool = typer.Option(None, help="Only apply primal heuristics and then terminate (QUBO only)"),
    quantum_heuristic: Annotated[
        Optional[List[str]], typer.Option(help="Adds given quantum heuristic to the heuristics pool")
    ] = None,
    context: str = typer.Option("", help="Billing context to run the job in."),
    tag: str = typer.Option("", help="Tag to identify the job later."),
    quiet: bool = typer.Option(False, help="Disable interactive output and only show final logs"),
) -> None:
    """Solve the optimization problem specified in the given file and actively monitor the progress.

    Outputs solver logs and the time billed. This command is equivalent to a 'submit' command
    followed by a 'monitor'.
    """
    client = HTTPSClient(api_key=ctx.obj.api_key)

    # submit job
    job_id = _submit(
        client,
        problem_file,
        params_file,
        tag,
        context,
        quiet,
        absolute_gap=absolute_gap,
        relative_gap=relative_gap,
        time_limit=timelimit,
        as_qubo=as_qubo,
        as_qubo_only=as_qubo_only,
        presolve=presolve,
        heuristics_only=heuristics_only,
        quantum_heuristics=quantum_heuristic,
    )

    solver_log = SolverLog()

    if quiet:
        try:
            status = JobStatus.created
            while status in [JobStatus.created, JobStatus.running]:
                status = client.get_current_status(job_id)
                status = JobStatus(status[0])
                time.sleep(ctx.obj.poll_frequency)

            logs = client.get_current_log(job_id)
            solver_log.update_log(logs[0])

        except Exception:
            _exit_with_error("Failed to retrieve status")

        print(f"\nFinished job with status {status.value}")

    else:
        # monitor job, i.e., print logs, final status etc.
        _monitor_job(job_id, client, solver_log, ctx.obj.poll_frequency)

        # get time billed
        _retrieve_billing_time(job_id, client)


@app.command()
def submit(
    ctx: Context,
    problem_file: str = typer.Argument(help="Path to optimization problem file."),
    params_file: str = typer.Option(None, help="Path to parameter file. If specified, override other options."),
    relative_gap: float = typer.Option(None, help="Stopping criterion: relative gap"),
    absolute_gap: float = typer.Option(None, help="Stopping criterion: absolute gap"),
    timelimit: int = typer.Option(None, help="Stopping criterion: runtime"),
    as_qubo: bool = typer.Option(None, help="Try to solve MIP as MIP and as QUBO"),
    as_qubo_only: bool = typer.Option(None, help="Try to solve MIP only as QUBO"),
    presolve: bool = typer.Option(None, help="Enable (default) or disable presolve"),
    heuristics_only: bool = typer.Option(None, help="Only apply primal heuristics and then terminate (QUBO only)"),
    quantum_heuristic: Annotated[
        Optional[List[str]], typer.Option(help="Adds given quantum heuristic to the heuristics pool")
    ] = None,
    context: str = typer.Option("", help="Billing context to run the job in."),
    tag: str = typer.Option("", help="Tag to identify the job later."),
    quiet: bool = typer.Option(False, help="Disable interactive output and only show final logs"),
) -> None:
    """Submit the given optimization problem in a non-blocking way.

    Use 'status', 'logs', and 'solution' commands to get results.
    """
    client = HTTPSClient(api_key=ctx.obj.api_key)

    # submit job
    _submit(
        client,
        problem_file,
        params_file,
        tag,
        context,
        quiet,
        absolute_gap=absolute_gap,
        relative_gap=relative_gap,
        time_limit=timelimit,
        as_qubo=as_qubo,
        as_qubo_only=as_qubo_only,
        presolve=presolve,
        heuristics_only=heuristics_only,
        quantum_heuristics=quantum_heuristic,
    )


@app.command()
def logs(
    ctx: Context,
    job_id: str = typer.Argument(help="The ID of the job to retrieve logs for."),
    item: int = typer.Option(0, help="The index of the batch item."),
) -> None:
    """Print the current logs of the given job.

    For batched jobs, the optional parameter 'item' selects the item of the batch.
    """
    client = HTTPSClient(api_key=ctx.obj.api_key)

    # single-shot log dumping of all available lines
    has_error = False
    with yaspin(text=f"Retrieving current logs for job {job_id}...", color="yellow") as spinner:
        try:
            logs = client.get_current_log(job_id)
            spinner.text = "Retrieved logs:"
            spinner.ok("✅")

            with spinner.hidden():
                for line in logs[item].split("\n"):
                    print(line)
        except Exception:
            spinner.text = "Failed to retrieve logs"
            spinner.fail("❌")
            has_error = True

    if has_error:
        sys.exit(1)


@app.command()
def monitor(
    ctx: Context,
    job_id: str = typer.Argument(help="The ID of the job to monitor."),
) -> None:
    """Resumes monitoring the progress (i.e., logs) of a given job, e.g., after a 'submit' command.

    For batched jobs, the optional parameter 'item' selects the item of the batch.
    """
    client = HTTPSClient(api_key=ctx.obj.api_key)
    solver_log = SolverLog()

    # monitor job, i.e., print logs, final status etc.
    _monitor_job(job_id, client, solver_log, ctx.obj.poll_frequency)

    # get time billed
    _retrieve_billing_time(job_id, client)


@app.command()
def status(
    ctx: Context,
    job_id: str = typer.Argument(help="The ID of the job to retrieve status for."),
    item: int = typer.Argument(0, help="The index of the batch item."),
) -> None:
    """Retrieves the status of a given job: CREATED, RUNNING, FINISHED, SUCCESS, TIMEOUT, TERMINATED, or ERROR.

    For batched jobs, the optional parameter 'item' selects the item of the batch.
    """
    with yaspin(text=f"Retrieving status for job {job_id}...", color="yellow") as spinner:
        client = HTTPSClient(api_key=ctx.obj.api_key)
        _status(job_id, item, client, spinner)


@app.command()
def solution(
    ctx: Context,
    job_id: str = typer.Argument(help="The ID of the job to retrieve solution for."),
    item: int = typer.Option(0, help="The index of the batch item."),
) -> None:
    """Display the solution vector for a given job if its computation completed with success.

    For batched jobs, the optional parameter 'item' selects the item of the batch.
    """
    with yaspin(text=f"Retrieving solution for job {job_id}...", color="yellow") as spinner:
        client = HTTPSClient(api_key=ctx.obj.api_key)

        try:
            res, _ = client.get_results(job_id)
            res = res[item]

            spinner.text = "Retrieved solution:"
            spinner.ok("✅")

            print(SolutionParser.parse(res["solution_file"]))

        except Exception:
            spinner.text = "Failed to retrieve solution."
            spinner.fail("❌")


@app.command()
def time_billed(
    ctx: Context,
    job_id: str = typer.Argument(help="The ID of the job to retrieve billing time for."),
) -> None:
    """Output the time billed for a particular job in minutes."""
    client = HTTPSClient(api_key=ctx.obj.api_key)

    _retrieve_billing_time(job_id, client)


@app.command("list")
def list_(ctx: Context, n: int = typer.Option(10, help="Maximum number of jobs to display")) -> None:
    """Shows information on the user's latest n jobs."""
    res = None
    with yaspin(text=f"Retrieving latest {n} jobs for given API key...", color="yellow") as spinner:
        client = HTTPSClient(api_key=ctx.obj.api_key)

        try:
            res = client.get_jobs(n)

            spinner.text = f"You have {len(res['running'])} active and {len(res['old'])} finished jobs" + (
                ":" if len(res["running"]) + len(res["old"]) > 0 else "."
            )
            spinner.ok("✅")

            # output jobs in a nice, tabular format
            def jobs2table(jobs: dict, title: str = "") -> None:
                tbl = Table(title=f"[bold]{title}[/bold]", title_justify="left")
                tbl.add_column()
                tbl.add_column("Job ID")
                tbl.add_column("Size", justify="right")
                (tbl.add_column("Tag"),)
                tbl.add_column("Type(s)")
                tbl.add_column("Filename(s)")
                tbl.add_column("Created")
                tbl.add_column("Time billed", justify="right")

                for job in jobs:
                    bs = int(job["batch_size"])

                    # should have a timezone but it's unclear to me what timezone it should be
                    dt = datetime.datetime.fromtimestamp(int(job["created"]))  # noqa: DTZ006
                    status = ""
                    if bool(job["finished"]) and bool(job["successful"]):
                        status = "[green]✔[/green]"
                    elif bool(job["finished"]) and not bool(job["successful"]):
                        status = "[red]✗[/red]"

                    tbl.add_row(
                        status,
                        job["job_id"],
                        f"{bs}",
                        "---" if job["tag"] == "" else job["tag"],
                        job["first_type"] + (f" (+ {bs - 1})" if bs > 1 else ""),
                        job["first_filename"] + (f" (+ {bs - 1})" if bs > 1 else ""),
                        dt.strftime("%d.%m.%Y %H:%M:%S"),
                        job["time_billed"],
                    )
                console.print(tbl)

            if len(res["running"]) > 0:
                print("")
                jobs2table(res["running"], title="Active jobs")

            if len(res["old"]) > 0:
                print("")
                jobs2table(res["old"], title="Finished jobs")

        except Exception:
            spinner.text = "Failed to retrieve list of jobs."
            spinner.fail("❌")


@app.command()
def cancel(
    ctx: Context,
    job_id: str = typer.Argument(help="The ID of the job to cancel"),
) -> None:
    """Cancel a job that is currently running."""
    with yaspin(text=f"Canceling job {job_id}...", color="yellow") as spinner:
        client = HTTPSClient(api_key=ctx.obj.api_key)

        try:
            client.interrupt_job(job_id)

            spinner.text = "Job canceled"
            spinner.ok("✅")
        except Exception:
            spinner.text = "Failed to cancel job"
            spinner.fail("❌")


@app.command()
def api_key(ctx: Context) -> None:
    """Prints the API key set through QUANTAGONIA_API_KEY."""
    console.print(f"Your API Key: [green]{ctx.obj.api_key}[/green]")


@app.command()
def version() -> None:
    """Prints the version of this Python package."""
    __version__ = importlib.metadata.version("quantagonia")
    print(__version__)


@app.callback()
def main(ctx: Context) -> None:
    if "QUANTAGONIA_API_KEY" not in os.environ:
        _exit_with_error("Quantagonia API Key not found. Please set the 'QUANTAGONIA_API_KEY' environment variable.")
    api_key = os.environ["QUANTAGONIA_API_KEY"]

    ctx.obj = AppState(api_key)


def entrypoint() -> None:
    app()


if __name__ == "__main__":
    entrypoint()
