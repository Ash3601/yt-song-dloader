# redis_to_sqlite_migration.py
import redis
import sqlite3
from datetime import datetime

# Connect to Redis
r = redis.Redis()

# Connect to SQLite
DB_FILE = "analytics.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Ensure analytics table exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        user_id TEXT,
        query TEXT,
        video_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Migrate top searches from Redis sorted set
if r.exists("analytics:searches") and r.type("analytics:searches") == b'zset':
    print("Migrating search data from zset...")
    search_data = r.zrange("analytics:searches", 0, -1, withscores=True)
    for raw_query, count in search_data:
        query = raw_query.decode()
        for _ in range(int(count)):
            cursor.execute('''
                INSERT INTO analytics (event_type, query, timestamp)
                VALUES (?, ?, ?)
            ''', ("search", query, datetime.now()))
else:
    print("❌ 'analytics:searches' not found or not a zset.")

# Migrate top downloads from Redis sorted set
if r.exists("analytics:downloads") and r.type("analytics:downloads") == b'zset':
    print("Migrating download data from zset...")
    download_data = r.zrange("analytics:downloads", 0, -1, withscores=True)
    for raw_vid, count in download_data:
        video_id = raw_vid.decode()
        for _ in range(int(count)):
            cursor.execute('''
                INSERT INTO analytics (event_type, video_id, timestamp)
                VALUES (?, ?, ?)
            ''', ("download", video_id, datetime.now()))
else:
    print("❌ 'analytics:downloads' not found or not a zset.")

# Finalize
conn.commit()
conn.close()
print("✅ Migration completed!")
