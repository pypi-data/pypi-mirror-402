from __future__ import annotations

import pathlib
import sys
from time import sleep
from typing import Any, Callable

from yaspin import yaspin

from quantagonia.cloud.enums import JobStatus
from quantagonia.cloud.https_client import HTTPSClient

# local imports
from quantagonia.cloud.solver_log import SolverLog
from quantagonia.enums import HybridSolverProblemType
from quantagonia.parameters import HybridSolverParameters
from quantagonia.parser.log_parser import SolverLogParser
from quantagonia.parser.solution_parser import SolutionParser

ERROR_SYMBOL = "❌"


class CloudRunner:
    """The main interface to solve and manage optimization tasks with the HybridSolver.

    Args:
        api_key (str): The API key to be used to authenticate with the HybridSolver.
    """

    def __init__(self, api_key: str):
        self._https_client = HTTPSClient(api_key=api_key)

    def solve(
        self,
        input_files: str | list,
        params: HybridSolverParameters | list[HybridSolverParameters] = None,
        tag: str = "",
        suppress_output: bool = False,
        **kwargs,
    ) -> tuple[list[dict[str, Any]], int]:
        """Solves the given input file(s) and prints the progress to the console.  Note that this is a blocking method.

        If you want to solve problems non-blocking or need finer control on what to do
        depending on the progress of the solve, use lower-level methods like :code:`submit()` and  :code:`progress()`.

        Args:
            input_files (str or List[str]): String or list of strings with path(s) to the input file(s).
            params (HybridSolverParameters or List[HybridSolverParameters]): (optional) HybridSolverParameters
                                                                             or list of HybridSolverParameters.
            tag (str): (optional) Attaches a tag to the compute job.
            suppress_output (bool): (optional) If true, all output is suppressed.
            kwargs (dict): (optional) Keyword arguments, see below.

        Keyword Arguments:
            description_files (str or List[str]): (optional) String or list[str] with path(s) to the descr. file(s).
            submit_callback: (optional) Custom callback function that is called when a job is submitted. Defaults to
                None.
            new_incumbent_callback: (optional) A callback function to call if a new incumbent is found in the batch
                item. Defaults to None.
            poll_frequency (float): (optional) The frequency (as float, in seconds) at which the function should poll
                for job status. Defaults to 1.
            timeout  (float): (optional) The maximum amount of time (as float, in seconds) to wait for the job to
                finish before timing out. Defaults to 14400.

        Returns:
            tuple(list, int): A tuple for which the first item is a list and the second item is an integer.
                The list consists of dictionaries containing results of the solve. The integer specifies
                the minutes billed for the job.
        """
        input_is_list = isinstance(input_files, list)  # used for convenience in the return

        # parse keyword args
        (description_files, poll_frequency, timeout, new_incumbent_callback, submit_callback, job_options, context) = (
            self._parse_kwargs(**kwargs)
        )

        input_files, params = self._sanitize_input(input_files, params, description_files)
        batch_size = len(input_files)

        # prepare solver logs
        solver_logs = [SolverLog() for ix in range(batch_size)]

        # the api expects a list of specification dictionaries, which we build here
        specs = build_specs_list(params, input_files, job_options)

        # submit job
        jobid = self._submit_job_on_solve(
            input_files, specs, description_files, tag, suppress_output, context, submit_callback
        )

        # wait until job is processed
        status: JobStatus = self._wait_for_job_on_solve(
            jobid, suppress_output, poll_frequency, timeout, solver_logs, batch_size, new_incumbent_callback
        )

        # print final prompt
        if status != JobStatus.finished:
            msg = f"Job with jobid {jobid} error. Status of the job: {status}"
            raise RuntimeError(msg)
        if not suppress_output:
            print(f"Finished processing job {jobid}...")

        # try to get results
        try:
            res, time_billed = self._https_client.get_results(jobid=jobid)
        except RuntimeError as runtime_e:
            sys.exit(f"{ERROR_SYMBOL}: " + str(runtime_e))

        # put logs to the result dict
        if not suppress_output:
            for ix in range(batch_size):
                solver_logs[ix].update_log(res[ix]["solver_log"])

        # parse solver logs and add solution
        res = self._polish_result(res)

        # convenience: don't return a list, if input was not a list
        if not input_is_list:
            res = res[0]

        return res, time_billed

    def submit(
        self,
        input_files: str | list[str],
        params: HybridSolverParameters | list[HybridSolverParameters] = None,
        tag: str = "",
        **kwargs,
    ) -> str:
        """Submits the given instance file(s) to the HybridSolver and returns the corresponding job id.

        Args:
            input_files (str or List[str]): String or list of strings with path(st) to the input file(s).
            params (HybridSolverParameters or List[HybridSolverParameters]): (optional) HybridSolverParameters or
            list of HybridSolverParameters.
            tag (str): (optional) Attaches a tag to the compute job.
            kwargs (dict): (optional) Keyword arguments, see below.

        Keyword Arguments:
            description_files (str or List[str]): (optional) String or list[str] with path(s) to the descr. file(s).
            submit_callback: (optional) Custom callback function that is called when a job is submitted.
                Defaults to None.

        Returns:
            str: The job id.

        """
        # parse keyword args
        (description_files, _, _, _, submit_callback, job_options, context) = self._parse_kwargs(**kwargs)

        input_files, params = self._sanitize_input(input_files, params, description_files)

        # the api expects a list of specification dictionaries, which we build here
        specs = build_specs_list(params, input_files, job_options)

        # submit job
        jobid = self._https_client.submit_job(
            problem_files=input_files, description_files=description_files, specs=specs, tag=tag, context=context
        )
        if submit_callback is not None:
            submit_callback(jobid)

        return jobid

    def logs(
        self,
        jobid: str,
    ) -> list[str]:
        """Retrieves a list of logs for the given job.

        Args:
            jobid (str): The ID of the job to retrieve logs for.

        Returns:
            list: A list of strings with the log for each item of the job.

        """
        return self._https_client.get_current_log(jobid)

    def status(
        self,
        jobid: str,
    ) -> JobStatus:
        """Retrieves the status of the given job.

        The status is one of CREATED, RUNNING, FINISHED, TERMINATED, or TIMEOUT.
        Note that this only tells the processing status of the job,
        but nothing about the status of the items of the job.
        To give an example, a job is also considered finished, if all items exited with an error.
        Please use the :code:`progress` method to retrieve results for the job items.

        Args:
            jobid (str): The ID of the job.

        Returns:
            JobStatus: The status of the job.

        """
        status = self._https_client.check_job(jobid)
        return JobStatus(status)

    def progress(
        self,
        jobid: str,
    ) -> list[dict[str, Any]]:
        """Retrieves a list of progress information for each item of the given job.

        The progress is a dictionary with keys for current
            'job_status',
            'solver_status',
            'bound',
            'objective',
            'abs_gap',
            'rel_gap',
            'solution',
            'wall_time',
            'nodes', and
            'num_incumbents'.

        Args:
            jobid (str): The ID of the job to retrieve progress for.

        Returns:
            list: A list of dictionaries with progress for each item of the job.
        """
        progress_list = self._https_client.get_current_solution(jobid)

        # parse the solution file
        for p in progress_list:
            p["solution"] = SolutionParser.parse(p["solution"])

        return progress_list

    def cancel(self, jobid: str) -> None:
        """Sends an interrupt signal to stop the execution of the specified job.

        Args:
            jobid (str): The id of the job to be canceled.

        """
        self._https_client.interrupt_job(jobid)

    @staticmethod
    def _parse_kwargs(
        **kwargs,
    ) -> tuple[list[str], int, int, Callable[[int, float, dict], None] | None, Callable[[str], None] | None, dict, str]:
        # Get description_files and ensure it's a list of strings
        description_files = kwargs.get("description_files", [])
        if not isinstance(description_files, (list, str)):
            msg = "description_files must be a string or list of strings"
            raise TypeError(msg)
        if isinstance(description_files, str):
            description_files = [description_files]

        # Get poll_frequency and ensure it's a number
        poll_frequency = kwargs.get("poll_frequency", 1)
        if not isinstance(poll_frequency, int):
            msg = "poll_frequency must be an integer"
            raise TypeError(msg)

        # Get timeout and ensure it's a number
        timeout = kwargs.get("timeout", 14400)
        if not isinstance(timeout, int):
            msg = "timeout must be an integer"
            raise TypeError(msg)

        # Get callbacks and ensure they're callable or None
        new_incumbent_callback = kwargs.get("new_incumbent_callback", None)
        if new_incumbent_callback is not None and not callable(new_incumbent_callback):
            msg = "new_incumbent_callback must be callable"
            raise TypeError(msg)

        submit_callback = kwargs.get("submit_callback", None)
        if submit_callback is not None and not callable(submit_callback):
            msg = "submit_callback must be callable"
            raise TypeError(msg)

        # Get job_options and ensure it's a dict
        job_options = kwargs.get("job_options", {})
        if not isinstance(job_options, dict):
            msg = "job_options must be a dictionary"
            raise TypeError(msg)

        # Get context and ensure it's a string
        context = kwargs.get("context", "")
        if not isinstance(context, str):
            msg = "context must be a string"
            raise TypeError(msg)

        return description_files, poll_frequency, timeout, new_incumbent_callback, submit_callback, job_options, context

    @staticmethod
    def _sanitize_input(
        input_files: str | list[str],
        params: HybridSolverParameters | list[HybridSolverParameters],
        description_files: list[str],
    ) -> tuple[list[str], list[HybridSolverParameters]]:
        # input file to list
        if isinstance(input_files, (str, pathlib.Path)):
            input_files = [input_files]
        # params to list
        if isinstance(params, HybridSolverParameters):
            params = [params]
        # initialize params list if it is not passed
        if params is None:
            params = [HybridSolverParameters() for _ in input_files]

        # at this stage, we should have two list of same length
        if len(input_files) != len(params):
            msg = f"Number of passed input files ({len(input_files)} does not match number"
            msg += f" of passed parameters ({len(params)})."
            raise RuntimeError(msg)

        if len(description_files) > 0 and len(description_files) != len(input_files):
            msg = f"Number of passed description files ({len(description_files)} does not match number"
            msg += f" of passed input files ({len(input_files)})."
            raise RuntimeError(msg)

        # no need to return description_files as it is not updated
        return input_files, params

    def _submit_job_on_solve(
        self,
        input_files: list,
        specs: list,
        description_files: list[str],
        tag: str,
        suppress_output: bool,
        context: str,
        submit_callback: Callable[[str], None],
    ) -> str:
        # print initial submission prompt
        if not suppress_output:
            spinner = yaspin()
            spinner.text = "Submitting job to the HybridSolver..."
            spinner.start()
        # try to submit
        try:
            jobid = self._https_client.submit_job(
                problem_files=input_files, specs=specs, description_files=description_files, tag=tag, context=context
            )
            if submit_callback is not None:
                submit_callback(jobid)
        except FileNotFoundError as fnf_e:
            if not suppress_output:
                spinner.text = "File not found"
                spinner.ok(ERROR_SYMBOL)
                spinner.stop()
            sys.exit(str(fnf_e))
        except ConnectionError as c_e:
            if not suppress_output:
                spinner.text = "Connection error"
                spinner.ok(ERROR_SYMBOL)
                spinner.stop()
            sys.exit(str(c_e))
        except Exception:
            if not suppress_output:
                spinner.text = "Cannot submit job"
                spinner.ok(ERROR_SYMBOL)
                spinner.stop()
            raise

        # print queueing
        if not suppress_output:
            spinner.text = f"Queued job with jobid {jobid}..."
            spinner.ok("✔")
            spinner.stop()

        return jobid

    def _wait_for_job_on_solve(
        self,
        jobid: str,
        suppress_output: bool,
        poll_frequency: float,
        timeout: float,
        solver_logs: list,
        batch_size: int,
        new_incumbent_callback: Callable[[int, float, dict], None] | None = None,
    ) -> JobStatus:
        """Polls the status of a job given by `jobid` until it reaches a final status or until the timeout is exceeded.

        The function updates the solver logs and calls the new incumbent callback function if a
        new incumbent is found in the batch item.

        Args:
            jobid: A UUID object that identifies the job to poll the status for.
            suppress_output (bool): (optional) If true, all output is suppressed.
            poll_frequency: The frequency (as float, in seconds) at which the function should poll for job status.
            timeout: The maximum amount of time (as float, in seconds) to wait for the job to finish before timing out.
            solver_logs: A list of `SolverLog` objects to update with the current log of the job.
            batch_size: The size of the batch for the job as an integer.
            new_incumbent_callback: (optional) A callback function to call if a new incumbent is found in the
            batch item. Defaults to None.

        Returns:
            JobStatus: A `JobStatus` enum value indicating whether the job has finished, terminated, or timed out.

        """
        printed_created = False
        printed_running = False
        spinner = yaspin()

        batch_num_incumbents = [0] * batch_size

        for _ in range(int(timeout / poll_frequency)):
            sleep(poll_frequency)

            try:
                status = self._https_client.check_job(jobid=jobid)
            except RuntimeError as runtime_e:
                sys.exit(f"{ERROR_SYMBOL} Unable to check job:\n\n{runtime_e}")

            if printed_running and not suppress_output:
                try:
                    logs = self._https_client.get_current_log(jobid=jobid)
                except RuntimeError as runtime_e:
                    sys.exit(f"{ERROR_SYMBOL} Unable to get log:\n\n{runtime_e}")

                for ix in range(batch_size):
                    solver_logs[ix].update_log(logs[ix])

            # stop spinner if necessary: for small problems polling interval might be too long to
            # ever reach JobStatus.running
            if status in [JobStatus.running, JobStatus.finished] and not (printed_running or suppress_output):
                spinner.text = f"Job {jobid} unqueued, processing..."
                spinner.ok("✔")
                spinner.stop()
                solver_logs[0].next_time_add_new_line()
                printed_running = True

            if status in [JobStatus.finished, JobStatus.terminated]:
                return status
            if status == JobStatus.created and not (suppress_output or printed_created):
                printed_created = True
                spinner.text = "Waiting in the queue for a free slot..."
                spinner.start()
                solver_logs[0].next_time_add_new_line()
            elif status == JobStatus.running and new_incumbent_callback is not None:
                try:
                    batch_solutions = self._https_client.get_current_solution(jobid=jobid)
                except RuntimeError as runtime_e:
                    sys.exit(f"{ERROR_SYMBOL}: " + str(runtime_e))

                for ix in range(batch_size):
                    if int(batch_solutions[ix]["num_incumbents"]) > batch_num_incumbents[ix]:
                        new_incumbent_callback(ix, batch_solutions[ix]["objective"], batch_solutions[ix]["solution"])
                        batch_num_incumbents[ix] = int(batch_solutions[ix]["num_incumbents"])

        return JobStatus.timeout

    @staticmethod
    def _polish_result(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for r in results:
            # parse and add solve stats
            logparser = SolverLogParser(r["solver_log"])
            r.update(logparser.get_solver_summary())
            # add solution
            r["solution"] = SolutionParser.parse(r["solution_file"])
            # no need to keep the solution file
            r.pop("solution_file")

        return results


#################################
# helper functions
#################################


def build_specs_list(params: list, problem_files: list, job_options: dict) -> list[dict[str, Any]]:
    """Build a list of spec dictionaries consisting of solver parameters and the problem type.

    Here we use the file suffix to determine the problem type.
    A proper problem type detection is done serverside.
    """
    specs = []
    for idx, param in enumerate(params):
        spec = {
            "solver_config": param.to_dict(),
            "problem_type": get_problem_type_from_filename(problem_files[idx]).value,
            "processing": job_options,
        }
        specs.append(spec)

    return specs


def get_problem_type_from_filename(problem_file_name: str) -> HybridSolverProblemType:
    # remove suffixes
    problem_file_name = pathlib.Path(problem_file_name)
    suffixes = problem_file_name.suffixes
    suffixes.reverse()  # reverse list to check last suffix first
    for suffix in suffixes:
        if suffix in [".qubo"]:
            return HybridSolverProblemType.QUBO
        if suffix in [".lp", ".mps"]:
            return HybridSolverProblemType.MIP

    msg = "Could not detect problem type."
    raise RuntimeError(msg)
