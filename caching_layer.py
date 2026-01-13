"""
Simple in-memory caching for API responses.
This reduces API calls and rate-limit errors by reusing recent data.
"""

from datetime import datetime
from functools import wraps
import json

try:
    from run_log import log_event
except Exception:  # pragma: no cover - optional dependency
    def log_event(*args, **kwargs):
        return

_CACHE = {}
_CACHE_TIMESTAMPS = {}


def _make_cache_key(func, args, kwargs):
    payload = {"args": args, "kwargs": kwargs}
    return f"{func.__name__}:{json.dumps(payload, sort_keys=True, default=str)}"


def cache_response(expire_minutes=1440):
    """Cache function results for expire_minutes (default: 24 hours)."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _make_cache_key(func, args, kwargs)

            if cache_key in _CACHE and cache_key in _CACHE_TIMESTAMPS:
                age_minutes = (datetime.utcnow() - _CACHE_TIMESTAMPS[cache_key]).total_seconds() / 60
                if age_minutes < expire_minutes:
                    print(f"  CACHE HIT for {func.__name__} (age: {age_minutes:.1f} min)")
                    log_event(
                        "info",
                        "CACHE",
                        f"Cache hit for {func.__name__}",
                        action="cache_hit",
                        meta={"age_minutes": round(age_minutes, 2)}
                    )
                    return _CACHE[cache_key]
                del _CACHE[cache_key]
                del _CACHE_TIMESTAMPS[cache_key]
                print(f"  CACHE EXPIRED for {func.__name__} (age: {age_minutes:.1f} min)")
                log_event(
                    "info",
                    "CACHE",
                    f"Cache expired for {func.__name__}",
                    action="cache_expired",
                    meta={"age_minutes": round(age_minutes, 2)}
                )
            else:
                print(f"  CACHE MISS for {func.__name__}")
                log_event(
                    "info",
                    "CACHE",
                    f"Cache miss for {func.__name__}",
                    action="cache_miss"
                )

            result = func(*args, **kwargs)
            _CACHE[cache_key] = result
            _CACHE_TIMESTAMPS[cache_key] = datetime.utcnow()
            return result

        return wrapper
    return decorator


def clear_cache():
    """Clear all cached data."""
    _CACHE.clear()
    _CACHE_TIMESTAMPS.clear()
    print("  Cache cleared")


def get_cache_stats():
    """Return a summary of cache usage."""
    total_entries = len(_CACHE)
    total_size_bytes = sum(len(json.dumps(v, default=str)) for v in _CACHE.values())
    oldest_age_minutes = 0

    if _CACHE_TIMESTAMPS:
        oldest_timestamp = min(_CACHE_TIMESTAMPS.values())
        oldest_age_minutes = (datetime.utcnow() - oldest_timestamp).total_seconds() / 60

    return {
        "total_entries": total_entries,
        "size_kb": total_size_bytes / 1024,
        "oldest_entry_age_minutes": oldest_age_minutes,
    }
