# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers sp. z o.o.
# Author: Aleksander Stanik
"""
SPX Python Client

Dictionary-like interface to SPX Server API v3.
Supports GET and PUT for components and attributes under a named system.
"""
import requests
import json
import os
import threading
import contextlib
import logging
from collections.abc import MutableMapping
from typing import Optional, List, Any

from .faults import (
    get_global_pretty_errors,
    get_global_fault_verbose,
)
from .transport import perform_request

log = logging.getLogger("spx.client")

# ---------------------------------------------------------------------------
# Global / thread-local transparent mode controls
# ---------------------------------------------------------------------------
_GLOBAL_TRANSPARENT = False
_thread_local = threading.local()
_GET_SENTINEL = object()


def set_global_transparent(enabled: bool) -> None:
    """
    Set process-wide transparent mode for newly constructed SpxClient instances.
    Explicit SpxClient(transparent=...) always takes precedence.
    """
    global _GLOBAL_TRANSPARENT
    _GLOBAL_TRANSPARENT = bool(enabled)


def get_global_transparent() -> bool:
    """
    Return effective transparent mode from (in order of precedence):
      1) thread-local override set by `transparent_mode` context manager
      2) environment variable SPX_TRANSPARENT (1/true/yes/on)
      3) process-global flag set via set_global_transparent()
    """
    tl = getattr(_thread_local, "transparent", None)
    if tl is not None:
        return bool(tl)
    env = os.getenv("SPX_TRANSPARENT")
    if env is not None:
        return env.strip().lower() in {"1", "true", "yes", "on"}
    return _GLOBAL_TRANSPARENT


@contextlib.contextmanager
def transparent_mode(enabled: bool):
    """
    Temporarily set transparent mode for the current thread.
    Usage:
        with transparent_mode(True):
            # all new SpxClient() created here default to transparent=True
            ...
    """
    prev = getattr(_thread_local, "transparent", None)
    _thread_local.transparent = bool(enabled)
    try:
        yield
    finally:
        if prev is None:
            try:
                delattr(_thread_local, "transparent")
            except AttributeError:
                pass
        else:
            _thread_local.transparent = prev


class _TransparentSentinel:
    """
    No-op placeholder used when SpxClient runs in transparent mode.

    Behaves as:
    - callable: returns {"result": True}
    - attribute access: returns itself again (chaining-friendly)
    - setting attributes: ignored
    - numeric cast: 0 / 0.0
    - iteration: empty
    - truthiness: False
    """
    def __call__(self, *args, **kwargs):
        return {"result": True}

    def __getattr__(self, name: str):
        return self

    def __setattr__(self, name: str, value: Any):
        # ignore writes
        pass

    def __repr__(self):
        return "<transparent>"

    def __str__(self):
        return "<transparent>"

    def __bool__(self):
        return False

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __iter__(self):
        return iter(())


class SpxApiError(requests.HTTPError):
    """HTTP error raised by SpxClient with parsed fault payload attached.

    Attributes:
        fault: dict with fault projection (may be compact/full) or fallback info
        correlation_id: correlation id extracted from response headers if present
    """
    def __init__(self, message: str, response=None, fault: Optional[dict] = None):
        super().__init__(message, response=response)
        self.fault = fault or {}
        try:
            self.correlation_id = (response.headers.get("x-correlation-id") if response is not None else None)
        except Exception:
            self.correlation_id = None


class SpxClient(MutableMapping):
    """
    A client for SPX Server API v3 with dict-like access.

    Usage:
        client = SpxClient(
            base_url='http://127.0.0.1:8000',
            product_key='YOUR_PRODUCT_KEY',
            system_name='your_system'
        )
        # Read an attribute:
        temp = client['timer'].time
        # Set an attribute:
        client['timer'].time = 5.0
        # Get full component or root JSON:
        data = client ['timer'] # returns JSON at current path

        # Transparent mode (process-wide / thread-local / env):
        #   set_global_transparent(True)
        #   with transparent_mode(True):
        #       ...
        #   export SPX_TRANSPARENT=1
        # Or per-instance:
        #   SpxClient(..., transparent=True)
    """
    def __init__(self,
                 base_url: str,
                 product_key: str,
                 http_client=None,
                 path: Optional[List[str]] = None,
                 transparent: Optional[bool] = None,
                 on_fault: Optional[Any] = None,
                 pretty_errors: Optional[bool] = True,
                 client_fault_verbose: Optional[bool] = None,
                 ):
        self.base_url = base_url.rstrip('/')
        self.product_key = product_key
        self.path = path or []
        self.headers = {
            'Authorization': f'Bearer {self.product_key}',
            'Content-Type': 'application/json'
        }
        # allow injection of a custom HTTP client (e.g. FastAPI TestClient)
        self.http = http_client or requests
        # Determine effective transparent mode:
        # explicit arg > thread-local ctx > env var > module-global default
        effective_transparent = get_global_transparent() if transparent is None else bool(transparent)
        # set transparently via __dict__ to avoid __setattr__ side-effects during init
        self.__dict__["transparent"] = bool(effective_transparent)
        self.__dict__["_t"] = _TransparentSentinel() if self.__dict__["transparent"] else None
        self.__dict__["on_fault"] = on_fault
        eff_pretty = get_global_pretty_errors() if pretty_errors is None else bool(pretty_errors)
        self.__dict__["pretty_errors"] = eff_pretty
        eff_verbose = get_global_fault_verbose() if client_fault_verbose is None else bool(client_fault_verbose)
        self.__dict__["client_fault_verbose"] = eff_verbose

    def _build_url(self) -> str:
        if getattr(self, "transparent", False):
            # URL is irrelevant in transparent mode; return a stable pseudo-url
            return "transparent://"
        segments = [self.base_url, 'api', 'v3', 'system'] + self.path
        return '/'.join(segments)

    def _request(self, method: str, url: str, where: str, **kwargs):
        """Centralized HTTP request with fault capture; delegates to transport.perform_request."""
        if getattr(self, "transparent", False):
            class _Dummy:
                status_code = 200
                headers = {}

                def json(self):
                    return {}
            return _Dummy()

        # merge headers if caller provided extras
        headers = dict(self.headers)
        if "headers" in kwargs and isinstance(kwargs["headers"], dict):
            headers.update(kwargs.pop("headers"))
        return perform_request(
            self.http,
            method,
            url,
            headers=headers,
            where=where,
            pretty_errors=getattr(self, "pretty_errors", True),
            client_fault_verbose=getattr(self, "client_fault_verbose", False),
            on_fault=getattr(self, "on_fault", None),
            logger=log,
            api_error_cls=SpxApiError,
            **kwargs,
        )

    def __getitem__(self, key: str):
        if self.transparent:
            new_path = self.path + [key]
            return SpxClient(self.base_url, self.product_key, http_client=self.http, path=new_path, transparent=True, pretty_errors=self.pretty_errors, client_fault_verbose=self.client_fault_verbose)
        # Extend path and perform GET
        new_path = self.path + [key]
        url = '/'.join([self.base_url, 'api', 'v3', 'system'] + new_path)
        resp = self._request("GET", url, where="client.__getitem__")
        data = resp.json()
        # Leaf attribute returns {'value': ...}
        if isinstance(data, dict) and 'value' in data:
            return data['value']
        # Otherwise return a new client focused on the deeper path
        return SpxClient(self.base_url,
                         self.product_key,
                         http_client=self.http,
                         path=new_path,
                         transparent=self.transparent,
                         pretty_errors=self.pretty_errors,
                         client_fault_verbose=self.client_fault_verbose)

    def __setitem__(self, key: str, value):
        # Extend path and perform PUT
        url = '/'.join([self.base_url, 'api', 'v3', 'system'] + self.path)
        payload = {key: value}
        return self.put_item(url, payload)

    def put_item(self, path: str, payload: dict) -> Any:
        """
        Set a value at an arbitrary path under the current path.
        Example:
            client.put_item('sensor1/threshold', 42)
        """
        if self.transparent:
            return {}
        resp = self._request("PUT", path, where="client.put_item", json=payload)
        try:
            return resp.json()
        except ValueError:
            return {}

    def __delitem__(self, key: str):
        if self.transparent:
            return None
        # Extend path and perform DELETE
        new_path = self.path + [key]
        url = '/'.join([self.base_url, 'api', 'v3', 'system'] + new_path)
        self._request("DELETE", url, where="client.__delitem__")
        return None

    def __contains__(self, key: str) -> bool:
        """
        Dictionary-like membership test at the current path.
        Returns True if `key` exists in the JSON data returned by GET.
        """
        if self.transparent:
            return False
        data = self.get()
        children = data.get('children', [])
        return any(child.get('name') == key for child in children)

    def get(self, key=_GET_SENTINEL, default=None):
        """
        Dictionary-style helper:
            - client.get()              -> current node JSON (legacy behaviour)
            - client.get(key, default)  -> like __getitem__, returning default on failure
        """
        if key is _GET_SENTINEL:
            if self.transparent:
                return {}
            url = self._build_url()
            resp = self._request("GET", url, where="client.get")
            return resp.json()

        try:
            return self[key]
        except SpxApiError:
            return default
        except Exception:
            return default

    def to_dict(self) -> dict:
        """
        Return the current path's JSON as a pure Python dict.
        """
        return self.get()

    def __call__(self, *args, **kwargs):
        """Allow calling any SpxClient in transparent mode as a no-op.
        This keeps attribute-access chains usable for RPC-like calls
        (e.g., client.instances.sensor.reset()).
        """
        if getattr(self, "transparent", False):
            return {"result": True}
        raise TypeError(
            "SpxClient is not callable in non-transparent mode; "
            "use attribute access to obtain a method stub (e.g. client.reset(...))."
        )

    def __repr__(self):
        return f"<SpxClient path={'/'.join(self.path) or '<root>'}>"

    def __eq__(self, other):
        """
        Compare this client's data to another client or dict by comparing
        their JSON structures.
        """
        if isinstance(other, SpxClient):
            return self.to_dict() == other.to_dict()
        if isinstance(other, dict):
            return self.to_dict() == other
        return False

    def __ne__(self, other):
        """
        Inverse of __eq__ for inequality comparison.
        """
        return not (self == other)

    def __str__(self):
        """
        Return the full system structure from the current path
        as formatted JSON.
        """

        data = self.get()
        return json.dumps(data, indent=2)

    def _child_names(self, data: dict) -> list[str]:
        """Return child component names from a system JSON dict."""
        return [child.get('name') for child in data.get('children', []) if isinstance(child, dict) and 'name' in child]

    def _call_method(self, method_name, **kwargs):
        if self.transparent:
            return {"result": True}
        url = f"{self._build_url()}/method/{method_name}"
        resp = self._request("POST", url, where="client._call_method", json={"kwargs": kwargs})
        try:
            return resp.json()
        except ValueError:
            return None

    def __getattr__(self, key: str) -> Any:
        # never intercept private/special names
        if key.startswith("_"):
            error_msg = (
                f"{type(self).__name__!r} has no attribute "
                f"{key!r}"
            )
            raise AttributeError(error_msg)
        # In transparent mode, attribute-style traversal should return a new
        # SpxClient focused on the extended path, without performing any HTTP.
        if getattr(self, "transparent", False):
            new_path = self.path + [key]
            return SpxClient(
                self.base_url,
                self.product_key,
                http_client=self.http,
                path=new_path,
                transparent=True,
                pretty_errors=self.pretty_errors,
                client_fault_verbose=self.client_fault_verbose,
            )
        data = object.__getattribute__(self, "get")()
        # top-level simple values
        if key in data and not isinstance(data[key], dict):
            return data[key]

        # attributes under 'attr'
        attr_sec = data.get("attr", {})
        if key in attr_sec:
            return attr_sec[key].get("value")

        # child components -> return a deeper SpxClient wrapper
        if any(child_name == key for child_name in self._child_names(data)):
            new_path = self.path + [key]
            return SpxClient(
                self.base_url,
                self.product_key,
                http_client=self.http,
                path=new_path,
                transparent=self.transparent,
                pretty_errors=self.pretty_errors,
                client_fault_verbose=self.client_fault_verbose
            )

        # fallback: treat as RPC method
        return lambda **kwargs: self._call_method(key, **kwargs)

    def __setattr__(self, key: str, value) -> Any:
        if key == "transparent":
            self.__dict__["transparent"] = bool(value)
            # keep sentinel in sync
            if self.__dict__["transparent"]:
                self.__dict__["_t"] = _TransparentSentinel()
            else:
                # remove sentinel when leaving transparent mode
                self.__dict__["_t"] = None
            return {}

        # Attributes that belong to the client object itself and must never trigger HTTP calls
        internal_keys = ('base_url', 'product_key', 'http', 'path', 'headers', '_t')

        # If we are setting any internal attribute, store it directly
        if key in internal_keys:
            return super().__setattr__(key, value)

        # In transparent mode, ignore any mutations to remote attributes
        try:
            is_transparent = object.__getattribute__(self, "transparent")
        except AttributeError:
            is_transparent = False

        if is_transparent:
            # no-op in transparent mode
            return {}

        # Delegate to put_attr so path handling is uniform
        return self.put_attr(key, value)

    def put_attr(self, path: str, value) -> dict:
        """
        Set an attribute value at an arbitrary path under the current path.
        Example:
            client.put_attr('sensor1/threshold', 42)
        """
        if self.transparent:
            return {}
        # Interpret `path` as relative to current node; the **last** segment is the attribute name.
        segments = [seg for seg in path.strip('/').split('/') if seg]
        if not segments:
            raise ValueError("path must contain at least an attribute name")
        parent_segments = segments[:-1]
        attr_name = segments[-1]
        new_path = self.path + parent_segments + ['attr', attr_name]
        url = '/'.join([self.base_url, 'api', 'v3', 'system'] + new_path)
        payload = {'value': value}
        resp = self._request("PUT", url, where="client.put_attr", json=payload)
        try:
            return resp.json()
        except ValueError:
            return {}

    def __iter__(self):
        """
        Iterate over keys in the current mapping:
        attribute names and child component names.
        """
        if self.transparent:
            return iter([])
        data = self.get()
        # Only child component names from 'children' list
        child_keys = [child.get('name') for child in data.get('children', [])]
        for key in child_keys:
            yield key

    def __len__(self):
        """
        Return the total number of keys in the mapping.
        """
        if self.transparent:
            return 0
        data = self.get()
        return len(data.get('attr', {})) + len(data.get('children', []))

    def keys(self):
        if self.transparent:
            return []
        return list(self.__iter__())

    def items(self):
        if self.transparent:
            return []
        return [(key, self[key]) for key in self]

    def values(self):
        if self.transparent:
            return []
        return [self[key] for key in self]
