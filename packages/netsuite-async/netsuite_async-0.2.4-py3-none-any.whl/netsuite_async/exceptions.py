from __future__ import annotations

from typing import Any, Optional

import httpx

__all__ = [
    "NetsuiteError",
    "NetsuiteRequestError",
    "NetsuiteAuthError",
    "NetsuiteRateLimitError",
    "NetsuiteValidationError",
    "NetsuiteServerError",
    "NetsuiteResponseError",
    "NetsuiteClientException",
    "raise_for_response",
]


class NetsuiteError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        operation: Optional[str] = None,
        record_name: Optional[str] = None,
        details: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.operation = operation
        self.record_name = record_name
        self.details = details
        self.request_id = request_id


class NetsuiteRequestError(NetsuiteError):
    """Base class for request/response related errors."""


class NetsuiteAuthError(NetsuiteRequestError):
    """Raised when authentication or authorization fails."""


class NetsuiteRateLimitError(NetsuiteRequestError):
    """Raised when NetSuite signals a rate limiting event."""


class NetsuiteValidationError(NetsuiteRequestError):
    """Raised for 4xx validation or bad request responses."""


class NetsuiteServerError(NetsuiteError):
    """Raised when NetSuite returns a 5xx error."""


class NetsuiteResponseError(NetsuiteError):
    """Raised when NetSuite returns an unexpected but successful response."""


class NetsuiteClientException(NetsuiteRequestError):
    """
    Backwards compatible alias for the old single exception type.

    Prefer using the more specific subclasses from this module going forward.
    """


def raise_for_response(
    response: httpx.Response,
    *,
    operation: str,
    record_name: Optional[str] = None,
) -> None:
    """Raise an appropriately typed exception for non-2xx responses."""

    status = response.status_code
    payload = _safe_json(response)
    summary = _extract_summary(payload)
    request_id = response.headers.get("X-REQUEST-ID") or response.headers.get("X-Request-Id")
    message = _build_message(operation, record_name, status, summary)
    exc_cls = _exception_for_status(status)
    raise exc_cls(
        message,
        status_code=status,
        operation=operation,
        record_name=record_name,
        details=payload or response.text,
        request_id=request_id,
    )


def _safe_json(response: httpx.Response) -> Optional[Any]:
    try:
        return response.json()
    except ValueError:
        return None


def _extract_summary(payload: Optional[Any]) -> Optional[str]:
    if not isinstance(payload, dict):
        return None

    for key in ("message", "detail", "error", "title"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            for key in ("message", "detail"):
                value = first.get(key)
                if isinstance(value, str):
                    return value
    return None


def _build_message(
    operation: str,
    record_name: Optional[str],
    status_code: int,
    summary: Optional[str],
) -> str:
    op = operation.capitalize()
    scope = f"{op} for {record_name}" if record_name else op
    message = f"{scope} failed ({status_code})"
    if summary:
        message = f"{message}: {summary}"
    return message


def _exception_for_status(status_code: int):
    if status_code in (401, 403):
        return NetsuiteAuthError
    if status_code == 429:
        return NetsuiteRateLimitError
    if 400 <= status_code < 500:
        return NetsuiteValidationError
    if status_code >= 500:
        return NetsuiteServerError
    return NetsuiteClientException
