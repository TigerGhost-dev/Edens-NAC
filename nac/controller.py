import sqlite3
import subprocess
import time

from nac.firewall import allow_device, block_device

DATABASE = "database.db"


###############################################################
# Database
###############################################################

def db():
    return sqlite3.connect(DATABASE)


###############################################################
# Discover devices
###############################################################

def get_devices():

    output = subprocess.getoutput(
        "ip neigh show dev wlan0"
    )

    devices = []

    for line in output.splitlines():

        parts = line.split()

        ###################################################
        # Ignore IPv6 neighbours
        ###################################################

        if ":" in parts[0]:
            continue

        ###################################################
        # Ignore incomplete entries
        ###################################################

        if "lladdr" not in parts:
            continue

        ip = parts[0]

        mac = parts[parts.index("lladdr") + 1].lower()

        if mac == "failed":
            continue

        devices.append({
            "ip": ip,
            "mac": mac
        })

    return devices


###############################################################
# Synchronize database
###############################################################

def sync_database():

    conn = db()
    c = conn.cursor()

    for device in get_devices():

        ip = device["ip"]
        mac = device["mac"]

        c.execute(
            """
            SELECT authenticated
            FROM devices
            WHERE mac=?
            """,
            (mac,)
        )

        row = c.fetchone()

        ###################################################
        # New device
        ###################################################

        if row is None:

            c.execute(
                """
                INSERT INTO devices
                (
                    mac,
                    ip,
                    authenticated
                )
                VALUES
                (
                    ?,?,0
                )
                """,
                (mac, ip)
            )

            print(f"[NEW DEVICE] {mac}")

        ###################################################
        # Existing device
        ###################################################

        else:

            c.execute(
                """
                UPDATE devices
                SET
                    ip=?,
                    last_seen=CURRENT_TIMESTAMP
                WHERE mac=?
                """,
                (ip, mac)
            )

    conn.commit()
    conn.close()


###############################################################
# Authenticate user
###############################################################

def authenticate_user(username):

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT mac
        FROM devices
        WHERE username=?
        """,
        (username,)
    )

    row = c.fetchone()

    if row:

        mac = row[0]

        allow_device(mac)

        c.execute(
            """
            UPDATE devices
            SET authenticated=1
            WHERE mac=?
            """,
            (mac,)
        )

        conn.commit()

        print(f"[AUTHORIZED] {mac}")

    conn.close()


###############################################################
# Logout user
###############################################################

def logout_user(username):

    conn = db()
    c = conn.cursor()

    c.execute(
        """
        SELECT mac
        FROM devices
        WHERE username=?
        """,
        (username,)
    )

    row = c.fetchone()

    if row:

        mac = row[0]

        block_device(mac)

        c.execute(
            """
            UPDATE devices
            SET
                authenticated=0,
                username=NULL
            WHERE mac=?
            """,
            (mac,)
        )

        conn.commit()

        print(f"[REVOKED] {mac}")

    conn.close()


###############################################################
# Background discovery
###############################################################

def controller():

    print("[+] Eden NAC Controller Running")

    while True:

        try:
            sync_database()

        except Exception as e:
            print(e)

        time.sleep(5)