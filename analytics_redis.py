# analytics_redis.py
import redis

r = redis.Redis()

def increment_search(query):
    r.zincrby("analytics:searches", 1, query)

def increment_download(video_id):
    r.zincrby("analytics:downloads", 1, video_id)

def is_video_downloaded(video_id):
    return r.sismember("downloaded_videos", video_id)

def mark_video_as_downloaded(video_id):
    r.sadd("downloaded_videos", video_id)

def get_top_searches(n=10):
    return r.zrevrange("analytics:searches", 0, n - 1, withscores=True)

def get_top_downloads(n=10):
    return r.zrevrange("analytics:downloads", 0, n - 1, withscores=True)

def log_search_redis(query):
    r.zincrby("analytics:searches", 1, query)

def log_download_redis(video_id):
    r.zincrby("analytics:downloads", 1, video_id)
