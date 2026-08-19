from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ModelResult:
    model: str
    ok: bool
    error: Optional[str]
    latency_ms: Optional[int]
    raw_text: Optional[str]
    status_code: Optional[int]
    response_json: Optional[Dict[str, Any]]
    response_text: Optional[str]


class HttpStatusError(Exception):
    def __init__(self, status_code: int, body: str, data: Optional[Dict[str, Any]]) -> None:
        super().__init__(f"{status_code} {body}")
        self.status_code = status_code
        self.body = body
        self.data = data
