import sqlite3
import bcrypt

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
CREATE TABLE IF NOT EXISTS Clips (
    clip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    clip_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES Users(username)
)
""")

# Seed the 'public' user if it doesn't exist
cursor.execute("SELECT * FROM Users WHERE username = 'public'")
if cursor.fetchone() is None:
    # Hash a 1 space character password for the public user
    empty_password_hash = bcrypt.hashpw(" ".encode(), bcrypt.gensalt())
    cursor.execute(
        "INSERT INTO Users (username, password_hash) VALUES (?, ?)",
        ("public", empty_password_hash)
    )
    print("Public user created")

conn.commit()
conn.close()

print("Tables created successfully")