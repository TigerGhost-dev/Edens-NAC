import subprocess

###############################################################
# Helper
###############################################################

def run(cmd):

    subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

###############################################################
# Remove all rules for a MAC
###############################################################

def clear_device(mac):

    while True:

        result = subprocess.run(

            f"iptables -D FORWARD -m mac --mac-source {mac} -j DROP",

            shell=True,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL

        )

        if result.returncode != 0:

            break

###############################################################
# Block Internet ONLY
###############################################################

def block_device(mac):

    clear_device(mac)

    run(

        f"iptables -I FORWARD 1 "
        f"-m mac --mac-source {mac} "
        f"-i wlan0 "
        f"-o wlan1 "
        f"-j DROP"

    )

###############################################################
# Allow Internet
###############################################################

def allow_device(mac):

    clear_device(mac)

###############################################################
# Flush everything
###############################################################

def reset_firewall():

    run("iptables -F")

    run("iptables -t nat -F")