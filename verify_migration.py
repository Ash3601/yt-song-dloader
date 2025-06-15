import sqlite3

conn = sqlite3.connect("analytics.db")
cursor = conn.cursor()

print("Total Records:", cursor.execute("SELECT COUNT(*) FROM analytics").fetchone()[0])

print("\nTop Searches:")
for row in cursor.execute("""
    SELECT query, COUNT(*) FROM analytics
    WHERE event_type = 'search'
    GROUP BY query
    ORDER BY COUNT(*) DESC
    LIMIT 10
"""):
    print(f"- {row[0]}: {row[1]} times")

print("\nTop Downloads:")
for row in cursor.execute("""
    SELECT video_id, COUNT(*) FROM analytics
    WHERE event_type = 'download'
    GROUP BY video_id
    ORDER BY COUNT(*) DESC
    LIMIT 10
"""):
    print(f"- {row[0]}: {row[1]} times")

conn.close()
