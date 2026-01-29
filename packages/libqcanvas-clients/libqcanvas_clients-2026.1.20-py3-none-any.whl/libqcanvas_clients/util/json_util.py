import json
from typing import Any

from httpx import Response


def check_status_and_parse_json(response: Response) -> Any:
    return json.loads(response.raise_for_status().text)
