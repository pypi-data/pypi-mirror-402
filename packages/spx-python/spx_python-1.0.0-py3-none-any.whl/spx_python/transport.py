

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers
"""
HTTP transport & response handling helpers for the SPX Python client.

This module keeps `client.py` lean by extracting common request/response
plumbing, fault extraction and logging. It intentionally has no dependency
on SpxClient internals.
"""
from __future__ import annotations

import json
from typing import Any, Optional, Callable, Dict

from .faults import emit_fault_log, format_pretty_fault

__all__ = [
    "extract_fault_from_response",
    "emit_fault_event",
    "perform_request",
]


def _safe_get(dct: Any, key: str, default: Any = None) -> Any:
    try:
        if isinstance(dct, dict):
            return dct.get(key, default)
    except Exception:
        pass
    return default


def extract_fault_from_response(resp: Any) -> Dict[str, Any]:
    """Normalize various server error shapes to a unified *fault* dict.

    The function is resilient to *requests.Response* and test-double objects
    that expose *status_code*, *headers*, *json()*, and *text*.
    """
    # Correlation id from headers (best-effort)
    corr = None
    try:
        headers = getattr(resp, "headers", {}) or {}
        corr = headers.get("x-correlation-id") or headers.get("X-Correlation-Id")
    except Exception:
        corr = None

    # Normalize status code once
    try:
        status = int(getattr(resp, "status_code", None))
    except Exception:
        status = None

    # Try to parse JSON body
    data: Optional[Dict[str, Any]] = None
    try:
        parsed = resp.json()  # type: ignore[attr-defined]
        data = parsed if isinstance(parsed, dict) else None
    except Exception:
        data = None

    # 1) Already our diagnostics fault format
    if isinstance(data, dict) and data.get("type") == "fault":
        fault = dict(data)  # shallow copy to avoid mutating caller
        if fault.get("http_status") is None:
            fault["http_status"] = status
        if not fault.get("correlation_id") and corr:
            fault["correlation_id"] = corr
        return fault

    # 2) RFC7807 (+ optional extensions)
    if isinstance(data, dict) and ("title" in data or "status" in data or "type" in data):
        # Some servers omit status in body; prefer HTTP status
        body_status = _safe_get(data, "status")
        try:
            body_status = int(body_status) if body_status is not None else status
        except Exception:
            body_status = status

        # Prefer problem+json extensions when present
        extensions = data.get("extensions") if isinstance(data.get("extensions"), dict) else {}
        if extensions.get("type") == "fault":
            fault = dict(extensions)
            if fault.get("http_status") is None:
                fault["http_status"] = body_status
            if not fault.get("correlation_id") and corr:
                fault["correlation_id"] = corr
            return fault

        # Generic problem normalization
        return {
            "type": "fault",
            "event": data.get("type", "problem"),
            "http_status": body_status,
            "action": _safe_get(extensions, "action"),
            "component": _safe_get(extensions, "component"),
            "correlation_id": _safe_get(extensions, "correlation_id") or corr,
            "error": {
                "type": data.get("title", "HTTPError"),
                "message": data.get("detail") or data.get("description") or "",
            },
            "breadcrumbs": _safe_get(extensions, "breadcrumbs"),
            "extra": _safe_get(extensions, "extra"),
        }

    # 3) FastAPI/Starlette default shape {"detail": ...} or unknown JSON
    if isinstance(data, dict):
        message = data.get("detail") if "detail" in data else json.dumps(data, ensure_ascii=False)
        return {
            "type": "fault",
            "event": "http_error",
            "http_status": status,
            "action": None,
            "component": None,
            "correlation_id": corr,
            "error": {
                "type": "HTTPError",
                "message": message,
            },
        }

    # 4) Non-JSON / no body
    try:
        text = getattr(resp, "text", "")
    except Exception:
        text = ""
    return {
        "type": "fault",
        "event": "http_error",
        "http_status": status,
        "action": None,
        "component": None,
        "correlation_id": corr,
        "error": {
            "type": "HTTPError",
            "message": text,
        },
    }


def emit_fault_event(
    logger: Any,
    resp: Any,
    where: str,
    *,
    on_fault: Optional[Callable[[Dict[str, Any]], None]] = None,
    pretty_errors: bool = True,
    client_fault_verbose: bool = False,
) -> Dict[str, Any]:
    """Extract, log and emit a client-side fault event.

    Returns the normalized *fault* dict.
    """
    fault = extract_fault_from_response(resp)
    payload = {
        "where": where,
        "method": getattr(getattr(resp, "request", None), "method", None),
        "url": getattr(getattr(resp, "request", None), "url", None),
        "http_status": getattr(resp, "status_code", None),
        "correlation_id": fault.get("correlation_id")
        or (getattr(getattr(resp, "headers", None), "get", lambda *_: None)("x-correlation-id")),
        "fault": fault,
    }

    # user hook first (non-fatal)
    try:
        if on_fault:
            on_fault(payload)
    except Exception:
        pass

    emit_fault_log(
        logger,
        fault,
        where=where,
        pretty=pretty_errors,
        verbose=client_fault_verbose,
        payload=payload,
    )
    return fault


def perform_request(
    http_client: Any,
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    where: str,
    pretty_errors: bool,
    client_fault_verbose: bool,
    on_fault: Optional[Callable[[Dict[str, Any]], None]],
    logger: Any,
    api_error_cls: Any,
    **kwargs: Any,
):
    """Perform HTTP request, normalize faults and raise the provided error class on 4xx/5xx.

    The *api_error_cls* must accept signature *(message, response=None, fault=None)*.
    Returns the response on success.
    """
    resp = http_client.request(method, url, headers=headers or {}, **kwargs)
    if 400 <= getattr(resp, "status_code", 0):
        fault = emit_fault_event(
            logger,
            resp,
            where,
            on_fault=on_fault,
            pretty_errors=pretty_errors,
            client_fault_verbose=client_fault_verbose,
        )
        msg = (
            format_pretty_fault(fault, where=where)
            if pretty_errors
            else f"{method} {url} -> {getattr(resp, 'status_code', None)}"
        )
        raise api_error_cls(msg, response=resp, fault=fault)
    return resp
