# user_session.py
import uuid
from flask import session

SESSION_KEY = 'user_id'

def get_or_create_user_id():
    """Ensure each user has a unique session-based ID."""
    if SESSION_KEY not in session:
        session[SESSION_KEY] = str(uuid.uuid4())
    return session[SESSION_KEY]

def mark_downloaded(video_id, redis_instance):
    user_id = get_or_create_user_id()
    redis_instance.sadd(f"downloads:{user_id}", video_id)

def has_downloaded(video_id, redis_instance):
    user_id = get_or_create_user_id()
    return redis_instance.sismember(f"downloads:{user_id}", video_id)