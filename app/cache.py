"""
Thin Redis cache helper — DB2 is reserved for app-layer caching.

Usage:
    from app.cache import cache_get, cache_set, cache_delete, cache_delete_prefix

Key conventions:
    ctx_globals:{user_id}           — inject_globals() badge counts, TTL 60s
    match_score:{uid}:{candidate}   — calculate_match_score result, TTL 3600s
"""
import json
import os

import redis

_client = None


def _get_client():
    global _client
    if _client is None:
        base = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        # swap DB suffix to 2
        if base.endswith('/0') or base.endswith('/1') or base.endswith('/4'):
            base = base.rsplit('/', 1)[0]
        url = base.rstrip('/') + '/2'
        _client = redis.from_url(url, decode_responses=True,
                                 socket_connect_timeout=1,
                                 socket_timeout=0.5)
    return _client


def cache_get(key):
    try:
        raw = _get_client().get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        return None


def cache_set(key, value, ttl=60):
    try:
        _get_client().setex(key, ttl, json.dumps(value))
    except Exception:
        pass


def cache_delete(*keys):
    try:
        if keys:
            _get_client().delete(*keys)
    except Exception:
        pass


def cache_delete_prefix(prefix):
    """Delete all keys matching prefix* — use sparingly (SCAN-based)."""
    try:
        client = _get_client()
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor, match=f'{prefix}*', count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass
