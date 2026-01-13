"""
Caching Layer for API Responses
Think of this as a "memory cushion" - we remember what we just looked up
so we don't keep pestering the API like an overeager student asking 
the same question 47 times in a row.

Why? Alpha Vantage gives you 5 calls per minute. That's like having
5 bathroom passes for the whole day. Use them wisely!
"""

from functools import wraps
import json
import time
import os
from datetime import datetime, timedelta

# Simple in-memory cache (production would use Redis)
_CACHE = {}
_CACHE_TIMESTAMPS = {}


def cache_response(expire_minutes=1440):  # Default: 24 hours
    """
    Decorator to cache API responses
    
    This is like taking notes in class - you don't re-read the entire 
    textbook every time you need a fact, you just check your notes first.
    
    Args:
        expire_minutes: How long to keep the cached data (default 24 hours)
                       Financial data doesn't change by the second, so we
                       can safely cache it for a day.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            # Think of this as writing "Chapter 5, Page 42" in the margin
            # so you know exactly where you found this fact
            cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"
            
            # Check if we have this in cache and it's still fresh
            if cache_key in _CACHE and cache_key in _CACHE_TIMESTAMPS:
                cache_age = (datetime.now() - _CACHE_TIMESTAMPS[cache_key]).total_seconds() / 60
                
                if cache_age < expire_minutes:
                    print(f"  💾 Cache HIT for {func.__name__} (age: {cache_age:.1f} min)")
                    return _CACHE[cache_key]
                else:
                    print(f"  ⏰ Cache EXPIRED for {func.__name__} (age: {cache_age:.1f} min)")
                    # Remove expired entry
                    del _CACHE[cache_key]
                    del _CACHE_TIMESTAMPS[cache_key]
            else:
                print(f"  🔍 Cache MISS for {func.__name__}")
            
            # Not in cache or expired - call the actual function
            result = func(*args, **kwargs)
            
            # Store in cache with timestamp
            _CACHE[cache_key] = result
            _CACHE_TIMESTAMPS[cache_key] = datetime.now()
            
            return result
        
        return wrapper
    return decorator


def clear_cache():
    """
    Clear all cached data
    Like pressing the "reset" button on your coffee order memory
    """
    global _CACHE, _CACHE_TIMESTAMPS
    _CACHE = {}
    _CACHE_TIMESTAMPS = {}
    print("  🧹 Cache cleared")


def get_cache_stats():
    """
    Get statistics about cache usage
    Helpful for understanding if your caching is actually working
    """
    total_entries = len(_CACHE)
    total_size_bytes = sum(len(json.dumps(v)) for v in _CACHE.values())
    
    return {
        'total_entries': total_entries,
        'size_kb': total_size_bytes / 1024,
        'oldest_entry_age_minutes': min(
            [(datetime.now() - ts).total_seconds() / 60 
             for ts in _CACHE_TIMESTAMPS.values()],
            default=0
        )
    }


# Usage in dcf_model.py:
# 
# @cache_response(expire_minutes=1440)  # Cache for 24 hours
# def fetch_company_and_cashflows(ticker: str):
#     # ... existing code ...
#
# @cache_response(expire_minutes=1440)
# def fetch_esg_data(ticker: str):
#     # ... existing code ...
#
# This means if someone analyzes AAPL at 9am, and another student
# analyzes AAPL at 9:30am, the second request hits the cache instead
# of burning another API call. It's like carpooling to the API!


# Advanced: Redis-based cache for production (optional)
"""
For production with multiple server instances, use Redis:

import redis
from flask_caching import Cache

cache_config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 86400  # 24 hours
}

cache = Cache(config=cache_config)
cache.init_app(app)

# Then use Flask-Caching decorators:
@app.route('/api/analyze', methods=['POST'])
@cache.cached(timeout=86400, key_prefix=lambda: request.json['ticker'])
def analyze_ticker():
    # ... existing code ...
"""
