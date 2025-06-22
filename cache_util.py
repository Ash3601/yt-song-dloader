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

def update_cached_downloaded_status(video_id, user_id):
    for key in r.scan_iter("search:*"):
        cached_data = r.get(key)
        if not cached_data:
            continue
        try:
            results = eval(cached_data.decode())  # Assuming cache was stored as str(list of dicts)
            modified = False
            for item in results:
                if item.get("video_id") == video_id:
                    item["downloaded"] = True
                    modified = True
            if modified:
                r.setex(key, 3600, str(results))  # Re-cache with 1-hour expiry
        except Exception as e:
            print(f"Cache update failed for {key}: {e}")


# cache_util.py  (add at bottom)

import json

SEARCH_PREFIX = "search:"          # key = search:<query>

def cache_search_results(query: str, results: list, ttl=3600):
    r.setex(f"{SEARCH_PREFIX}{query}", ttl, json.dumps(results))

def get_cached_search_results(query: str):
    raw = r.get(f"{SEARCH_PREFIX}{query}")
    return json.loads(raw) if raw else None

def update_cached_downloaded_status(video_id: str, user_id: str):
    """
    After a download succeeds, walk every cached search list and
    flip downloaded=True for this user/video combo.
    """
    pattern = f"{SEARCH_PREFIX}*"
    for key in r.scan_iter(pattern):
        data = r.get(key)
        print ('Checking inside the redis: ')
        print ("Data is: ", data)
        if not data:
            continue
        results = json.loads(data)
        changed = False
        for item in results:
            if item["video_id"] == video_id:
                item["downloaded"] = True   # ✅ mark
                changed = True
        print ("Value of changed: ", changed)
        print ("Results got: ", results)
        if changed:
            r.setex(key, 3600, json.dumps(results))
