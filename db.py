import sqlite3

DATABASE = "database.db"


def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()
    c = conn.cursor()

    #########################################################
    # USERS
    #########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        role TEXT DEFAULT 'user',

        status TEXT DEFAULT 'pending',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    #########################################################
    # DEVICES
    #########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS devices (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        mac TEXT UNIQUE,

        ip TEXT,

        hostname TEXT,

        os TEXT,

        authenticated INTEGER DEFAULT 0,

        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(username)
        REFERENCES users(username)

    )
    """)

    #########################################################
    # ACTIVE SESSIONS
    #########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        mac TEXT,

        ip TEXT,

        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        logout_time TIMESTAMP,

        active INTEGER DEFAULT 1

    )
    """)

    #########################################################
    # LOGS
    #########################################################

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        action TEXT,

        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()