# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers Sp. z o.o.
# See the accompanying LICENSE file for terms.

"""Shared helpers for preparing SPX models and instances in integration tests."""
from __future__ import annotations

import hashlib
import json
import math
import time
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Union

import yaml

from .client import SpxClient
from .pytest_logging import SpxPytestLoggerPlugin
from .unittest_logging import (
    SpxAssertionLoggingMixin,
    spx_append_attribute_value,
    spx_ensure_attribute,
    spx_log_test_case,
)

__all__ = [
    "load_model_definition",
    "load_model",
    "ensure_model",
    "ensure_instance",
    "create_instance",
    "bootstrap_model_instance",
    "wait_seconds",
    "wait_for_condition",
    "wait_for_attribute",
    "wait_for_attribute_value",
    "wait_for_state",
    "wait_for_instance",
    "spx_ensure_attribute",
    "spx_append_attribute_value",
    "spx_log_test_case",
    "SpxAssertionLoggingMixin",
    "SpxPytestLoggerPlugin",
]


def load_model_definition(model_path: Path) -> Dict[str, Any]:
    """Load a model definition from YAML or JSON based on file extension."""
    path = Path(model_path)
    suffix = path.suffix.lower()
    with path.open("r", encoding="utf-8") as handle:
        if suffix == ".json":
            return json.load(handle)
        return yaml.safe_load(handle)


def load_model(
    client: SpxClient,
    model_name: str,
    model_path: Union[str, Path],
) -> bool:
    """Load a model definition from disk and register/update it under model_name.

    Returns True if the remote definition changed and had to be updated.
    """
    definition = load_model_definition(Path(model_path))
    return ensure_model(client, model_name, definition)


def extract_model_definition(model_doc: Any) -> Optional[Dict[str, Any]]:
    if isinstance(model_doc, dict):
        for key in ("definition", "model", "data"):
            candidate = model_doc.get(key)
            if isinstance(candidate, dict):
                return candidate
        return model_doc
    return None


def fingerprint_model(model_def: Optional[Dict[str, Any]]) -> Optional[str]:
    if model_def is None:
        return None
    try:
        serialised = json.dumps(model_def, sort_keys=True, separators=(",", ":"))
    except TypeError:
        return None
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def ensure_model(client, model_key: str, model_def: Dict[str, Any]) -> bool:
    """Ensure the given model is registered. Returns True if updated."""
    models_client = client["models"]
    current_doc = None
    try:
        current_doc = models_client[model_key].definition
    except Exception:
        current_doc = None

    current_def = extract_model_definition(current_doc)
    local_fp = fingerprint_model(model_def)
    remote_fp = fingerprint_model(current_def)

    if local_fp != remote_fp:
        models_client[model_key] = model_def
        return True
    return False


def _fetch_instance_with_retry(instances, instance_key: str, *, attempts: int = 60, delay: float = 0.2):
    """Retry fetching instance by key to tolerate eventual consistency."""
    last_exc: Optional[Exception] = None
    attempts = max(1, attempts)
    for attempt in range(attempts):
        try:
            if instance_key in instances:
                return instances[instance_key]
        except Exception as exc:
            last_exc = exc
        if attempt < attempts - 1:
            time.sleep(delay)
    if last_exc is not None:
        raise last_exc
    raise KeyError(instance_key)


def wait_for_instance(
    client: SpxClient,
    instance_key: str,
    *,
    timeout: float = 5.0,
    interval: float = 0.2,
    raise_on_timeout: bool = True,
) -> Optional[SpxClient]:
    """Block until an instance with the given key becomes available.

    Returns the instance SpxClient or None (if raise_on_timeout=False).
    """
    timeout = max(0.0, timeout)
    interval = max(0.01, interval)
    attempts = max(1, int(math.ceil(timeout / interval)) or 1)
    instances = client["instances"]
    try:
        return _fetch_instance_with_retry(instances, instance_key, attempts=attempts, delay=interval)
    except Exception as exc:
        if raise_on_timeout:
            raise TimeoutError(f"Instance {instance_key!r} not available after {timeout}s") from exc
        return None


def ensure_instance(
    client,
    instance_key: str,
    model_key: str,
    *,
    overrides: Optional[Dict[str, Any]] = None,
    recreate: bool = False,
    ensure_running: bool = True,
    reset_on_create: bool = True,
    start_on_create: bool = True,
):
    """Ensure an instance exists for the given model and is running."""
    instances = client["instances"]

    try:
        existing = instances[instance_key]
    except Exception:
        existing = None

    if recreate or existing is None:
        if existing is not None:
            try:
                existing.stop()
            except Exception:
                pass
            try:
                del instances[instance_key]
            except Exception:
                pass

        create_attempts = 3
        inst = None
        for attempt in range(create_attempts):
            instances[instance_key] = model_key
            try:
                inst = _fetch_instance_with_retry(instances, instance_key)
                break
            except Exception:
                if attempt >= create_attempts - 1:
                    raise
                time.sleep(0.5)
        if inst is None:
            raise KeyError(instance_key)
        if overrides:
            for attr_path, value in overrides.items():
                inst.put_attr(attr_path, value)
        if reset_on_create:
            inst.reset()
        if start_on_create:
            inst.start()
        return inst

    inst = existing
    if overrides:
        for attr_path, value in overrides.items():
            inst.put_attr(attr_path, value)
    if ensure_running:
        try:
            state = inst.get().get("state")
        except Exception:
            state = None
        if state not in {"running", "RUNNING"}:
            try:
                inst.start()
            except Exception:
                pass
    return inst


def _normalise_instance_key(model_name: str) -> str:
    """Convert model name into a snake-like key suitable for instances."""
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", model_name.strip())
    slug = slug.strip("_").lower()
    return slug or "instance"


def create_instance(
    client: SpxClient,
    model_name: str,
    *,
    instance_key: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    ensure_running: bool = True,
    reset_on_create: bool = True,
    start_on_create: bool = True,
) -> SpxClient:
    """Create an SPX instance for the given model and return its client wrapper.

    The instance key defaults to a slug derived from the model name and is
    suffixed with an index if needed to avoid collisions.
    """
    instances = client["instances"]
    base_key = instance_key or _normalise_instance_key(model_name)

    candidate = base_key
    if candidate in instances:
        suffix = 2
        while f"{base_key}_{suffix}" in instances:
            suffix += 1
        candidate = f"{base_key}_{suffix}"

    return ensure_instance(
        client,
        candidate,
        model_name,
        overrides=overrides,
        recreate=False,
        ensure_running=ensure_running,
        reset_on_create=reset_on_create,
        start_on_create=start_on_create,
    )


def bootstrap_model_instance(
    spx_module,
    *,
    product_key: str,
    base_url: str,
    model_path: Path,
    model_key: str,
    instance_key: str,
    attribute_overrides: Optional[Dict[str, Any]] = None,
):
    """Load a model and ensure an instance is available, returning (client, instance, model_changed)."""
    client = spx_module.init(address=base_url, product_key=product_key)
    model_def = load_model_definition(model_path)
    model_changed = ensure_model(client, model_key, model_def)

    overrides = dict(attribute_overrides or {})

    instance = ensure_instance(
        client,
        instance_key,
        model_key,
        overrides=overrides,
        recreate=model_changed,
    )

    return client, instance, model_changed


def wait_seconds(duration: float, interval: float = 0.2) -> None:
    """Sleep for duration seconds, yielding periodically to keep loops responsive."""
    deadline = time.time() + max(0.0, duration)
    while time.time() < deadline:
        remaining = max(0.0, deadline - time.time())
        time.sleep(min(interval, remaining))


def wait_for_condition(
    predicate: Callable[[], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> bool:
    """Poll predicate until it returns True or timeout expires."""
    deadline = time.time() + max(0.0, timeout)
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def _resolve_attr_value(component: Any, attr_path: str) -> Any:
    """Fetch attribute value by traversing via client-style indexing."""
    segments = [seg for seg in attr_path.strip("/").split("/") if seg]
    if not segments:
        raise ValueError("attr_path must contain at least one segment")
    target = component
    for segment in segments:
        target = target[segment]
    result = getattr(target, "internal_value", target)
    if isinstance(result, dict) and "value" in result:
        return result["value"]
    return result


def wait_for_attribute(
    instance: SpxClient,
    attr_path: str,
    predicate: Callable[[Any], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> bool:
    """Wait until predicate(value) returns True for the given attribute path."""

    def _wrapped() -> bool:
        try:
            value = _resolve_attr_value(instance, attr_path)
        except Exception:
            return False
        return predicate(value)

    return wait_for_condition(_wrapped, timeout=timeout, interval=interval)


def wait_for_attribute_value(
    instance: SpxClient,
    attr_path: str,
    expected: Any,
    *,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> bool:
    """Wait until an attribute equals the expected value."""
    return wait_for_attribute(
        instance,
        attr_path,
        lambda value: value == expected,
        timeout=timeout,
        interval=interval,
    )


def wait_for_state(
    instance: SpxClient,
    expected: Union[str, Iterable[str], Callable[[Optional[str]], bool]],
    *,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> bool:
    """Wait until an instance reaches one of the expected states."""
    if callable(expected):
        state_predicate = expected
    else:
        states = {expected} if isinstance(expected, str) else set(expected)

        def state_predicate(value: Optional[str]) -> bool:
            return value in states

    def _wrapped() -> bool:
        try:
            state = instance.state
        except Exception:
            return False
        return state_predicate(state)

    return wait_for_condition(_wrapped, timeout=timeout, interval=interval)
