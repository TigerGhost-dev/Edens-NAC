import sqlite3

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # ---------- USERS TABLE ----------
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        mac TEXT,
        ip TEXT,
        os TEXT,
        status TEXT
    )
    """)

    # ---------- LOGS TABLE ----------
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()