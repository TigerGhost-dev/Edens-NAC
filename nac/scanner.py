import sqlite3
import subprocess

from nac.firewall import block_device


def scan_network():

    output = subprocess.getoutput(
        "sudo arp-scan --interface=wlan0 --localnet"
    )

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    lines = output.splitlines()

    for line in lines:

        parts = line.split()

        if len(parts) < 2:
            continue

        ip = parts[0]
        mac = parts[1]

        c.execute(
            "SELECT authenticated FROM devices WHERE mac=?",
            (mac,)
        )

        row = c.fetchone()

        if row is None:

            c.execute("""
            INSERT OR IGNORE INTO devices
            (mac, ip, authenticated)
            VALUES (?, ?, 0)
            """, (mac, ip))

            block_device(mac)

        elif row[0] == 0:

            block_device(mac)

    conn.commit()
    conn.close()