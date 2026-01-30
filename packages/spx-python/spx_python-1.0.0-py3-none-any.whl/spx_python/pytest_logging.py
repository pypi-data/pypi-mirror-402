# SPDX-License-Identifier: MIT
"""Pytest integration helpers for logging SPX test events."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict

import pytest

from .client import SpxClient
from .unittest_logging import spx_append_attribute_value, spx_ensure_attribute

__all__ = ["SpxPytestLoggerPlugin"]


class SpxPytestLoggerPlugin:
    def __init__(self, instance_factory: Callable[[], SpxClient], *, attr_path: str = "test_logs"):
        self.instance_factory = instance_factory
        self.attr_path = attr_path
        self._node_instances: dict[str, SpxClient] = {}

    def _record(self, instance: SpxClient, payload: Dict[str, Any]) -> None:
        spx_append_attribute_value(instance, self.attr_path, payload)

    def instance_fixture(self):
        import pytest

        plugin = self

        @pytest.fixture(scope="class")
        def spx_instance(request):
            instance = plugin.instance_factory()
            spx_ensure_attribute(instance, plugin.attr_path, default=[])

            cls = getattr(request, "cls", None)
            if cls is not None:
                cls.spx_log_instance = instance

            return instance

        return spx_instance

    def log_fixture(self):
        import pytest

        plugin = self

        @pytest.fixture
        def spx_log(spx_instance, request):
            nodeid = getattr(request.node, "nodeid", None)
            if nodeid is not None:
                plugin._node_instances[nodeid] = spx_instance

            def _log(kind: str, message: str | None = None, **meta: Any):
                payload = {"ts": time.time(), "kind": kind}
                if message is not None:
                    payload["message"] = message
                payload.update(meta)
                plugin._record(spx_instance, payload)

            return _log

        return spx_log

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.when != "call":
            return

        nodeid = getattr(item, "nodeid", None)
        instance = item.funcargs.get("spx_instance")
        if nodeid is not None:
            if instance is None:
                instance = self._node_instances.pop(nodeid, None)
            else:
                self._node_instances.pop(nodeid, None)
        if instance is None:
            cls = getattr(item, "cls", None)
            instance = getattr(cls, "spx_log_instance", None) if cls else None
        if instance is None:
            return

        payload = {
            "ts": time.time(),
            "kind": "testcase",
            "event": "end",
            "status": report.outcome,
            "nodeid": report.nodeid,
            "duration": getattr(report, "duration", None),
        }
        if report.failed:
            payload["message"] = str(report.longrepr)
        self._record(instance, payload)
