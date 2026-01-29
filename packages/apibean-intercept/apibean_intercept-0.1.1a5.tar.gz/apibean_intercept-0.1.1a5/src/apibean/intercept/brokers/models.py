from dataclasses import dataclass
from typing import Dict, Any, Optional
from fastapi import Request


@dataclass
class RequestContext:
    method: str
    path: str
    headers: Dict[str, str]
    query: Dict[str, Any]
    body: Optional[Any]

    # derived from request.url
    base_url: str

    # raw object
    raw_request: Request


@dataclass
class ResponseContext:
    status_code: int
    headers: dict
    body: Any
