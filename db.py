import sqlite3

DATABASE = "database.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    ###########################################################
    # USERS
    ###########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        status TEXT NOT NULL DEFAULT 'pending'
    )
    """)

    ###########################################################
    # DEVICES
    ###########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT UNIQUE NOT NULL,
        ip TEXT,
        username TEXT,
        authenticated INTEGER DEFAULT 0,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    ###########################################################
    # LOGS
    ###########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        time TIMESTAMP
    )
    """)

    ###########################################################
    # Create default administrator
    ###########################################################

    c.execute("""
    SELECT id
    FROM users
    WHERE username='admin'
    """)

    if c.fetchone() is None:

        c.execute("""
        INSERT INTO users
        (
            username,
            password,
            role,
            status
        )
        VALUES
        (
            'admin',
            'admin123',
            'admin',
            'approved'
        )
        """)

    conn.commit()
    conn.close()