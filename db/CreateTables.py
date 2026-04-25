import sqlite3

# Connect to SQLite database
conn = sqlite3.connect("xclipboard.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS CLIPS (
    clip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    clip_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES Users(username)
)
""")

conn.commit()
conn.close()

print("Tables created successfully")