# cache_util.py (Refactored for consistency with session-based user ID)
import redis
import uuid
from flask import session

r = redis.Redis()

USER_KEY_PREFIX = "downloads:"


def get_user_id_from_cookie():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


def has_user_downloaded(user_id, video_id):
    key = f"{USER_KEY_PREFIX}{user_id}"
    return r.sismember(key, video_id)


def mark_user_downloaded(user_id, video_id):
    key = f"{USER_KEY_PREFIX}{user_id}"
    r.sadd(key, video_id)


import json

def cache_search_results(query, results, ttl=3600):
    r.setex(f"cache:search:{query}", ttl, json.dumps(results))

def get_cached_search_results(query):
    cached = r.get(f"cache:search:{query}")
    return json.loads(cached) if cached else None
