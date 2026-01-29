from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union

__all__ = [
    "UpdateResult",
    "FetchResultSuccess",
    "FetchResultError",
    "FetchResult",
    "SummaryPageError",
    "Link",
    "SummaryRecord",
    "FullRecord",
    "parse_id",
]


@dataclass
class UpdateResult:
    id: str
    success: bool
    status_code: int


@dataclass
class FetchResultSuccess:
    data: Optional[dict]
    success: Literal[True] = True


@dataclass
class FetchResultError:
    error: Optional[str]
    success: Literal[False] = False


FetchResult = Union[FetchResultSuccess, FetchResultError]


@dataclass
class SummaryPageError:
    offset: int
    limit: int
    q: Optional[str]
    status_code: int
    error: str
    response: Optional[str]


@dataclass
class Link:
    rel: str
    href: str


@dataclass
class SummaryRecord:
    id: str
    type: str
    links: List[Link]
    raw: Dict[str, Any]


@dataclass
class FullRecord:
    id: str
    type: str
    links: List[Link]
    raw: Dict[str, Any]


def parse_id(url: str) -> str:
    """Extract record ID from NetSuite Location header URL."""
    return url.rsplit("/", 1)[-1]
