import redis
import json

r = redis.Redis()
for key in r.scan_iter("search:*"):
    data = r.get(key)
    if not data:
        continue
    try:
        results = json.loads(data)
        cleaned = []
        for item in results:
            # Remove the 'downloaded' key if it exists
            item.pop("downloaded", None)
            cleaned.append(item)
        r.setex(key, 3600, json.dumps(cleaned))
        print(f"✅ Cleaned key: {key.decode()}")
    except Exception as e:
        print(f"⚠️ Failed to clean key {key.decode()}: {e}")
