
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import Request


@dataclass
class APIEndpoint: 
    """Configuration for a single API endpoint."""
    method: str
    path: str
    delegate: Callable[[Request], Awaitable[Any]]