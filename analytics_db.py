# analytics_db.py
import sqlite3
from collections import Counter
from datetime import datetime


DB_NAME = DB_FILE = "analytics.db"

def get_total_event_count():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analytics")
        # print ("The value returned from fetchone is: ", cursor.fetchone()[0])
        # count = cursor.fetchone()[0]
        # return (180,)
        # return -1
        return cursor.fetchone()[0]

def get_top_searches(limit=10):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT query FROM analytics WHERE event_type='search'")
        queries = [row[0] for row in cursor.fetchall() if row[0]]
        return Counter(queries).most_common(limit)

def get_top_downloads(limit=10):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT video_id FROM analytics WHERE event_type='download'")
        video_ids = [row[0] for row in cursor.fetchall() if row[0]]
        return Counter(video_ids).most_common(limit)

def log_search_db(user_id, query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            query TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO search_logs (user_id, query, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, query, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def log_download_db(user_id, video_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            video_id TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO download_logs (user_id, video_id, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, video_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# analytics_db.py (append at bottom)

# import sqlite3

# DB_NAME = "analytics.db"

# def get_total_event_count():
#     with sqlite3.connect(DB_NAME) as conn:
#         cur = conn.cursor()
#         cur.execute("SELECT (SELECT COUNT(*) FROM searches) + (SELECT COUNT(*) FROM downloads)")
#         return cur.fetchone()[0]

# def get_top_searches(limit=10):
#     with sqlite3.connect(DB_NAME) as conn:
#         cur = conn.cursor()
#         cur.execute("""
#             SELECT query, COUNT(*) as count FROM searches
#             GROUP BY query ORDER BY count DESC LIMIT ?
#         """, (limit,))
#         return cur.fetchall()

# def get_top_downloads(limit=10):
#     with sqlite3.connect(DB_NAME) as conn:
#         cur = conn.cursor()
#         cur.execute("""
#             SELECT video_id, COUNT(*) as count FROM downloads
#             GROUP BY video_id ORDER BY count DESC LIMIT ?
#         """, (limit,))
#         return cur.fetchall()
