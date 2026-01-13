"""
Structured run log for per-request diagnostics.
"""

from contextvars import ContextVar
from datetime import datetime
import json

_RUN_LOG = ContextVar("run_log", default=None)


def start_run():
    """Initialize the run log for the current request."""
    log = []
    _RUN_LOG.set(log)
    return log


def _sanitize_meta(meta):
    if meta is None:
        return None
    try:
        json.dumps(meta, default=str)
        return meta
    except (TypeError, ValueError):
        return {"value": str(meta)}


def log_event(
    level,
    subsystem,
    message,
    *,
    code=None,
    source=None,
    meta=None,
    exception=None,
    action=None,
    fatal=False
):
    """Append a structured event to the current run log."""
    log = _RUN_LOG.get()
    if log is None:
        return

    payload = _sanitize_meta(meta) or {}
    if exception:
        payload = dict(payload)
        payload["exception"] = str(exception)

    event = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "subsystem": subsystem,
        "message": message,
        "code": code,
        "source": source,
        "action": action,
        "fatal": bool(fatal),
        "meta": payload if payload else None,
    }
    log.append(event)


def get_run_log():
    """Return the current run log list."""
    log = _RUN_LOG.get()
    return list(log) if log else []


def summarize_run_log(max_items=5):
    """Return a summary of the run log by level and top items."""
    log = get_run_log()
    counts = {"info": 0, "warning": 0, "error": 0}
    for entry in log:
        level = entry.get("level")
        if level in counts:
            counts[level] += 1

    important = [e for e in log if e.get("level") in ("error", "warning")]
    summary = {
        "counts": counts,
        "total": len(log),
        "important": important[:max_items],
    }
    return summary
