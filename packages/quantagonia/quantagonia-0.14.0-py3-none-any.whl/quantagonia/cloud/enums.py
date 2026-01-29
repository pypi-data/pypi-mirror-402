# ruff: noqa: PIE796 Enum contains duplicate value: `"/job"`
from enum import Enum


class Endpoints(str, Enum):
    checkjob = "/api/v2/jobs/{}"
    getcurstatus = "/api/v2/jobs/{}/status"
    getcursolution = "/api/v2/jobs/{}/solution"
    getcurlog = "/api/v2/jobs/{}/log"
    getresults = "/api/v2/jobs/{}/result"
    getjobs = "/api/v2/jobs"
    interruptjob = "/api/v2/jobs/{}"
    postjob = "/api/v2/jobs"
    s3 = "/api/v2/jobs/upload-url"


class JobStatus(str, Enum):
    created = "CREATED"
    running = "RUNNING"
    finished = "FINISHED"
    terminated = "TERMINATED"
    timeout = "TIMEOUT"
