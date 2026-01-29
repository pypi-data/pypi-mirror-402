import dataclasses
import json
from typing import Any


class DtoJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:  # noqa: ANN401 use of Any is allowed here
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)
