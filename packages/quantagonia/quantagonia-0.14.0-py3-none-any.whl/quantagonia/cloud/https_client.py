from __future__ import annotations

import copy
import gzip
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from quantagonia import __version__
from quantagonia.cloud.dto.encoder import DtoJSONEncoder
from quantagonia.cloud.dto.job import JobDto
from quantagonia.cloud.dto.presigned_s3 import PresignedS3
from quantagonia.cloud.enums import Endpoints
from quantagonia.errors import SolverError


class HTTPSClient:
    """HTTPS Client for the HybridSolver with low-level functions to manage optimization tasks.

    Args:
        api_key (str): The API key to be used to authenticate with the HybridSolver.
        server (str): The API server, which defaults to the production server.
        custom_headers (dict): (optional) Custom headers for the https requests.

    """

    COMPRESSION_THRESHOLD = 10 * 1024 * 1024  # 10 MB
    PROD_SERVER = "https://api.quantagonia.com"

    def __init__(self, api_key: str, custom_headers: dict | None = None) -> None:
        self.api_key = api_key
        server = os.environ.get("QUANTAGONIA_SERVER", self.PROD_SERVER)
        if server != self.PROD_SERVER:
            print(f"Job is submitted to non-default server {server}.")
        self.server = server
        self.custom_headers = custom_headers if custom_headers is not None else {}

        self.retry = Retry(total=5, backoff_factor=1, allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE"]))
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=self.retry))
        self.session.mount("https://", HTTPAdapter(max_retries=self.retry))

    def _upload_file(self, job_id: str, ind: int, file_path: Path) -> str:
        with tempfile.TemporaryDirectory() as temp_dir:
            if file_path.stat().st_size >= HTTPSClient.COMPRESSION_THRESHOLD and file_path.suffix.lower() not in [
                ".gz"
            ]:
                compressed_path = Path(temp_dir, f"{file_path.name}.gz")
                with open(file_path, "rb") as f_in, gzip.open(compressed_path, "wb", compresslevel=1) as f_out:
                    shutil.copyfileobj(f_in, f_out)
                upload_path = compressed_path
            else:
                upload_path = file_path

            ps3_problem_file = PresignedS3(
                jobId=job_id, contentType="application/octet-stream", batchNumber=str(ind), fileName=upload_path.name
            )
            data_for_s3 = json.dumps(ps3_problem_file, cls=DtoJSONEncoder)
            response = self.session.post(
                self.server + Endpoints.s3,
                data=data_for_s3,
                headers={"X-api-key": self.api_key, "Content-type": "application/json", **self.custom_headers},
            )
            if not response.ok:
                msg = "Unable to get an S3 presigned URL"
                raise RuntimeError(msg)

            file_uploader = response.json()
            headers = {
                "X-amz-meta-author": file_uploader["metaAuthor"],
                "X-amz-meta-version": file_uploader["metaVersion"],
                "Content-type": "application/octet-stream",
            }

            with open(upload_path, "rb") as f:
                upload_response = self.session.put(file_uploader["url"], data=f, headers=headers)

            if not upload_response.ok:
                raise RuntimeError(upload_response.text)
            return upload_path.name

    def submit_job(
        self,
        problem_files: list,
        specs: list,
        description_files: list | None = None,
        tag: str = "",
        context: str = "",
        origin: str = "python-api-" + str(__version__),
    ) -> str:
        job_id = str(uuid.uuid4())  # generate a random job id

        # sanitize problem files and description files
        if description_files is None:
            description_files = []
        if len(description_files) > 0 and len(description_files) != len(problem_files):
            msg = "The number of description files must match the number of problem files."
            raise ValueError(msg)

        # upload problem files to S3
        problem_file_paths = []
        for ind, prob_file in enumerate(problem_files):
            problem_file_paths.append(self._upload_file(job_id, ind, Path(prob_file)))

        # upload description files to S3
        description_file_paths = []
        if description_files is not None:
            for ind, desc_file in enumerate(description_files):
                description_file_paths.append(self._upload_file(job_id, ind, Path(desc_file)))

        start_job = JobDto(
            jobId=job_id,
            problemFiles=problem_file_paths,
            descriptionFiles=description_file_paths,
            specs=specs,
            tag=tag,
            context=context,
            origin=origin,
        )
        start_job_data = json.dumps(start_job, cls=DtoJSONEncoder)
        started_job = self.session.post(
            self.server + Endpoints.postjob,
            data=start_job_data,
            headers={"X-api-key": self.api_key, "Content-type": "application/json", **self.custom_headers},
        )
        # TODO: what happens server-side with the posted data? Is the Lambda doing something with it?
        if not started_job.ok:
            error_report = started_job.json()
            raise RuntimeError(error_report)

        return started_job.json()["jobId"]

    def _replace_file_content_from_url(self, e: dict, key: str) -> None:
        e[key] = self._get_file_content_from_url(e[key])

    def _get_file_content_from_url(self, e: dict | str) -> str:
        if isinstance(e, dict) and "error" in e:
            return "Error: " + e["error"]
        if isinstance(e, dict) and "url" in e:
            if e["url"] == "":
                return ""
            response = self.session.get(e["url"])
            if response.status_code == 200:
                return response.text
            return ""
        return e

    def check_job(self, jobid: str) -> str:
        response = self.session.get(
            self.server + Endpoints.checkjob.format(str(jobid)),
            headers={"X-api-key": self.api_key, **self.custom_headers},
        )
        if response.ok:
            return response.json()["status"]
        if response.status_code > 499:
            log = self.get_current_log(jobid)
            error_report = response.json()
            error_report["details"] = log[0]
            raise SolverError(error_report)
        if response.status_code < 499:
            error_report = response.json()
            raise RuntimeError(error_report)
        error_message = "Unknown error"
        raise RuntimeError(error_message)

    def get_current_status(self, jobid: str) -> str:
        response = self.session.get(
            self.server + Endpoints.getcurstatus.format(str(jobid)),
            headers={"X-api-key": self.api_key, **self.custom_headers},
        )

        return json.loads(response.text)

    def get_current_solution(self, jobid: str) -> list[str]:
        response = self.session.get(
            self.server + Endpoints.getcursolution.format(str(jobid)),
            headers={"X-api-key": self.api_key, **self.custom_headers},
        )

        if response.ok:
            array = json.loads(response.text)
            if not isinstance(array, list):
                error_message = f"Expected a list from the /getcurrentsolution endpoint, got {type(array)}"
                raise RuntimeError(error_message)
            for batch_item in array:
                self._replace_file_content_from_url(batch_item, "solution")
            return array

        error_report = response.json()
        raise RuntimeError(error_report)

    def get_current_log(self, jobid: str) -> list[str]:
        response = self.session.get(
            self.server + Endpoints.getcurlog.format(str(jobid)),
            headers={"X-api-key": self.api_key, **self.custom_headers},
        )
        if not response.ok:
            error_report = response.json()
            raise RuntimeError(error_report)
        return [self._get_file_content_from_url(e) for e in json.loads(response.text)]

    def get_results(self, jobid: str) -> tuple[dict, int]:
        response = self.session.get(
            self.server + Endpoints.getresults.format(str(jobid)),
            headers={"X-api-key": self.api_key, **self.custom_headers},
        )

        if not response.ok:
            error_report = response.json()
            raise RuntimeError(error_report)

        result = json.loads(response.text)
        array = copy.deepcopy(result["result"])

        for e in array:
            self._replace_file_content_from_url(e, "solution_file")
            self._replace_file_content_from_url(e, "solver_log")

        return array, int(result["time_billed"])

    def get_jobs(self, n: int) -> dict:
        params = {"n": str(n)}
        response = self.session.get(
            self.server + Endpoints.getjobs, params=params, headers={"X-api-key": self.api_key, **self.custom_headers}
        )

        if not response.ok:
            error_report = response.json()
            raise RuntimeError(error_report)

        return json.loads(response.text)

    def interrupt_job(self, jobid: str) -> None:
        response = self.session.delete(
            self.server + Endpoints.interruptjob.format(str(jobid)),
            headers={"X-api-key": self.api_key, **self.custom_headers},
        )

        if not response.ok:
            error_report = response.json()
            raise RuntimeError(error_report)
