# analytics.py
import redis
from collections import Counter

r = redis.Redis()

SEARCH_KEY = "analytics:searches"
DOWNLOAD_KEY = "analytics:downloads"


def log_search(query: str):
    r.zincrby(SEARCH_KEY, 1, query)


def log_download(video_id: str):
    r.zincrby(DOWNLOAD_KEY, 1, video_id)


def safe_decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value

def get_top_searches(n=10):
    raw = r.zrevrange("analytics:searches", 0, n - 1, withscores=True)
    return [(safe_decode(term), int(score)) for term, score in raw]

def get_top_downloads(n=10):
    raw = r.zrevrange("analytics:downloads", 0, n - 1, withscores=True)
    return [(safe_decode(video_id), int(score)) for video_id, score in raw]



def clear_analytics():
    r.delete(SEARCH_KEY)
    r.delete(DOWNLOAD_KEY)
