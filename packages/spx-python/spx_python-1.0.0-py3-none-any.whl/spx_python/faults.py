# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Hammerheads Engineers
"""
Helpers for formatting and logging SPX fault responses in a coder-friendly way.
Used by spx_python.client but kept separate to keep the client lean.
"""
from __future__ import annotations

import os
import json
import re
from collections import OrderedDict

__all__ = [
    "get_global_pretty_errors",
    "get_global_fault_verbose",
    "summarize_validator_message",
    "format_pretty_fault",
    "emit_fault_log",
]


# ---------------------------------------------------------------------------
# Global toggles
# ---------------------------------------------------------------------------
def get_global_pretty_errors() -> bool:
    """Return default pretty-errors setting from env (SPX_PRETTY_ERRORS). Defaults to True."""
    env = os.getenv("SPX_PRETTY_ERRORS")
    if env is None:
        return True
    return env.strip().lower() in {"1", "true", "yes", "on"}


def get_global_fault_verbose() -> bool:
    """Return whether client should log full fault JSON to console (SPX_CLIENT_FAULT_VERBOSE). Defaults to False."""
    env = os.getenv("SPX_CLIENT_FAULT_VERBOSE")
    if env is None:
        return False
    return env.strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Pretty formatting helpers
# ---------------------------------------------------------------------------
_VALIDATION_RE = re.compile(
    r"Template '([^']+)'\s+schema validation failed:\s*(\d+) errors?:\s*(.*)"
)


def summarize_validator_message(msg: str) -> str:
    """Make a compact, human-readable summary from a long validator message.

    Collapses duplicate entries and preserves the readable " at " delimiter.
    Output example:
        "Template 'pt_100': schema_violation at templates.pt_100.actions[0] ×2; missing_required at templates.pt_100.attr.x"
    """
    if not isinstance(msg, str) or not msg:
        return "validation failed"

    m = _VALIDATION_RE.search(msg)
    if m:
        name = m.group(1)
        tail = m.group(3)
        raw_parts = [p.strip() for p in tail.split(',') if p.strip()]
        counts: "OrderedDict[str, int]" = OrderedDict()
        for p in raw_parts:  # keep readable ' at ' delimiter
            counts[p] = counts.get(p, 0) + 1
        if counts:
            items = list(counts.items())
            head_items = items[:3]
            rest_unique = max(0, len(items) - len(head_items))
            head = [f"{text} ×{n}" if n > 1 else text for text, n in head_items]
            suffix = f"; +{rest_unique} more" if rest_unique > 0 else ""
            return f"Template '{name}': " + "; ".join(head) + suffix
        return f"Template '{name}': validation failed"

    first = msg.splitlines()[0]
    return (first[:300] + "…") if len(first) > 300 else first


def format_pretty_fault(fault: dict, where: str) -> str:
    """Compose a one-line summary of a fault suitable for console and exceptions."""
    status = fault.get("http_status")
    event = fault.get("event") or "error"
    cid = fault.get("correlation_id") or ""
    comp = fault.get("component") or {}
    comp_path = comp.get("path") or comp.get("name") or ""
    action = fault.get("action") or ""
    err = (fault.get("error") or {}).get("message") or ""
    core = summarize_validator_message(err)

    bits = []
    if status is not None:
        bits.append(str(status))
    if event:
        bits.append(event)
    if core:
        bits.append(core)
    summary = ": ".join(bits)

    meta = []
    if comp_path:
        meta.append(f"component={comp_path}")
    if action:
        meta.append(f"action={action}")
    if cid:
        meta.append(f"cid={cid}")
    if meta:
        summary += " (" + ", ".join(meta) + ")"
    return summary


def emit_fault_log(logger, fault: dict, where: str, *, pretty: bool, verbose: bool, payload: dict) -> None:
    """Emit fault logs using either compact or verbose shape.

    - If pretty==True and verbose==False → error: compact summary; debug: full payload JSON
    - Otherwise → error: full payload JSON (legacy behavior)
    """
    try:
        if pretty and not verbose:
            summary = format_pretty_fault(fault, where=where)
            logger.error("CLIENT_FAULT %s", summary)
            try:
                logger.debug("CLIENT_FAULT_FULL %s", json.dumps(payload, ensure_ascii=False))
            except Exception:
                logger.debug("CLIENT_FAULT_FULL %r", payload)
        else:
            logger.error("CLIENT_FAULT %s", json.dumps(payload, ensure_ascii=False))
    except Exception:
        logger.error("CLIENT_FAULT %r", payload)
