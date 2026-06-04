import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
INSERT INTO users
(username, password, mac, ip, os, status)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    "admin",
    "admin123",
    "ADMIN",
    "127.0.0.1",
    "Linux",
    "approved"
))

conn.commit()
conn.close()

print("Admin user created successfully")