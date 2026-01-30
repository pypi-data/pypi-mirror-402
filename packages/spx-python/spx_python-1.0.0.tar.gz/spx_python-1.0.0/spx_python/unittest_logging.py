# SPDX-License-Identifier: MIT
"""Utilities for logging unittest assertions/results into SPX instances."""
from __future__ import annotations

import functools
import time
import unittest
from typing import Any, Dict, Optional

from .client import SpxClient


def _json_safe(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return repr(value)


__all__ = [
    "spx_ensure_attribute",
    "spx_append_attribute_value",
    "spx_log_test_case",
    "SpxAssertionLoggingMixin",
]


def _attribute_segments(attr_path: str) -> list[str]:
    segments = [seg for seg in attr_path.strip("/").split("/") if seg]
    if segments and segments[0] == "attributes":
        segments = segments[1:]
    if not segments:
        raise ValueError("attr_path must contain at least one segment")
    return segments


def _attribute_internal_value_path(attr_path: str) -> str:
    segments = [seg for seg in attr_path.strip("/").split("/") if seg]
    if not segments or segments[0] != "attributes":
        segments.insert(0, "attributes")
    if segments[-1] != "internal_value":
        segments.append("internal_value")
    return "/".join(segments)


def _get_attribute(instance: SpxClient, attr_path: str):
    attr = instance["attributes"]
    for segment in _attribute_segments(attr_path):
        attr = attr[segment]
    return attr


def spx_ensure_attribute(instance: SpxClient, attr_path: str, default: Optional[Any] = None):
    try:
        attr = _get_attribute(instance, attr_path)
    except Exception:
        seed = [] if default is None else default
        instance.put_attr(_attribute_internal_value_path(attr_path), seed)
        attr = _get_attribute(instance, attr_path)
        return attr

    if default is not None and attr.internal_value is None:
        attr.internal_value = default
    return attr


def spx_append_attribute_value(instance: SpxClient, attr_path: str, entry: Dict[str, Any]) -> None:
    attr = spx_ensure_attribute(instance, attr_path, default=[])
    entries = list(attr.internal_value or [])
    entries.append(_json_safe(entry))
    attr.internal_value = entries


def spx_log_test_case(*, attr_path: Optional[str] = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            instance = getattr(self, "spx_log_instance", None)
            log_attr = attr_path or getattr(self, "spx_log_attr", "test_logs")
            name = func.__name__

            def _log(event: str, status: Optional[str] = None, message: Optional[str] = None):
                if not instance:
                    return
                payload = {
                    "ts": time.time(),
                    "kind": "testcase",
                    "event": event,
                    "name": name,
                }
                if status:
                    payload["status"] = status
                if message:
                    payload["message"] = message
                spx_append_attribute_value(instance, log_attr, payload)

            _log("start")
            try:
                result = func(self, *args, **kwargs)
            except Exception as exc:
                _log("end", status="fail", message=str(exc))
                raise
            else:
                _log("end", status="pass")
                return result

        return wrapper

    return decorator


def _wrap_assert(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        attr_path = getattr(self, "spx_log_attr", None)
        instance = getattr(self, "spx_log_instance", None)
        if not (attr_path and instance):
            return method(self, *args, **kwargs)

        label = method.__name__
        timestamp = time.time()

        def _log(status: str, message: Optional[str] = None):
            spx_append_attribute_value(
                instance,
                attr_path,
                {
                    "ts": timestamp,
                    "kind": "assertion",
                    "label": label,
                    "status": status,
                    "args": _json_safe(args),
                    "kwargs": _json_safe(kwargs),
                    "message": message,
                },
            )

        try:
            result = method(self, *args, **kwargs)
        except AssertionError as exc:
            _log("fail", str(exc))
            raise
        else:
            _log("pass")
            return result

    return wrapper


def _wrap_unittest_assertions(cls):
    for name in dir(unittest.TestCase):
        if name.startswith("assert"):
            attr = getattr(unittest.TestCase, name)
            if callable(attr):
                setattr(cls, name, _wrap_assert(attr))
    return cls


@_wrap_unittest_assertions
class SpxAssertionLoggingMixin:
    spx_log_instance: Optional[SpxClient] = None
    spx_log_attr: str = "test_logs"
