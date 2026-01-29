# ruff: noqa: N815 allow camelCase because this is the model for the S3 query that requires these fields
from dataclasses import dataclass


@dataclass
class PresignedS3:
    jobId: str = ""
    batchNumber: str = ""
    fileName: str = ""
    metaAuthor: str = ""
    metaVersion: str = ""
    contentType: str = ""
    url: str = ""
