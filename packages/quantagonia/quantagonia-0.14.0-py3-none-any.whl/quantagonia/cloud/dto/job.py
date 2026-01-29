# ruff: noqa: N815 allow camelCase because this is the model for the job query that requires these fields

from dataclasses import dataclass, field
from typing import List


@dataclass(init=True, repr=True, eq=True)
class JobDto:
    jobId: str = ""
    problemFiles: List[str] = field(default_factory=list)
    descriptionFiles: List[str] = field(default_factory=list)
    specs: List[str] = field(default_factory=list)
    tag: str = ""
    context: str = ""
    origin: str = ""
