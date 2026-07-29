import time
import sqlite3
import subprocess

from nac.firewall import (
    block_device,
    allow_device
)

DATABASE = "database.db"


###############################################################
# Scan devices connected to the AP
###############################################################

def get_devices():

    output = subprocess.getoutput(
        "ip neigh show dev wlan0"
    )

    devices = []

    for line in output.splitlines():

        parts = line.split()

        if len(parts) < 5:
            continue

        ip = parts[0]
        mac = parts[4]

        if mac.lower() == "lladdr":
            continue

        devices.append({

            "ip": ip,
            "mac": mac.lower()

        })

    return devices


###############################################################
# Synchronize database
###############################################################

def sync_database():

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    devices = get_devices()

    for device in devices:

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
        # First time seeing device
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

                (
                    mac,
                    ip
                )

            )

            block_device(mac)

            print(f"[NEW] {mac}")

            continue

        ###################################################
        # Update IP
        ###################################################

        c.execute(

            """
            UPDATE devices
            SET
                ip=?,
                last_seen=CURRENT_TIMESTAMP
            WHERE mac=?
            """,

            (
                ip,
                mac
            )

        )

        ###################################################
        # Firewall
        ###################################################

        if row[0] == 1:

            allow_device(mac)

        else:

            block_device(mac)

    conn.commit()
    conn.close()


###############################################################
# Authenticate user
###############################################################

def authenticate_user(username):

    conn = sqlite3.connect(DATABASE)
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

        print(f"[ALLOW] {mac}")

    conn.close()


###############################################################
# Logout
###############################################################

def logout_user(username):

    conn = sqlite3.connect(DATABASE)
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
            SET authenticated=0
            WHERE mac=?
            """,

            (mac,)

        )

        conn.commit()

        print(f"[BLOCK] {mac}")

    conn.close()


###############################################################
# Main controller loop
###############################################################

def controller():

    print("[+] Eden NAC Controller Started")

    while True:

        try:

            sync_database()

        except Exception as e:

            print(e)

        time.sleep(3)