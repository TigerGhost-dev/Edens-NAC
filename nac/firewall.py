import subprocess

CHAIN = "EDEN_NAC"


###############################################################
# Helper
###############################################################

def run(cmd):

    return subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode == 0


###############################################################
# Remove ACCEPT rule for a MAC
###############################################################

def _remove_allow(mac):

    while True:

        result = subprocess.run(

            f"iptables -D {CHAIN} "
            f"-m mac --mac-source {mac} "
            "-j ACCEPT",

            shell=True,

            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL

        )

        if result.returncode != 0:
            break


###############################################################
# Allow Internet
###############################################################

def allow_device(mac):

    _remove_allow(mac)

    run(

        f"iptables -I {CHAIN} 1 "
        f"-m mac --mac-source {mac} "
        "-j ACCEPT"

    )

    print(f"[ALLOW] {mac}")


###############################################################
# Block Internet
###############################################################

def block_device(mac):

    _remove_allow(mac)

    print(f"[BLOCK] {mac}")


###############################################################
# Check authorization
###############################################################

def is_allowed(mac):

    result = subprocess.run(

        f"iptables -C {CHAIN} "
        f"-m mac --mac-source {mac} "
        "-j ACCEPT",

        shell=True,

        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL

    )

    return result.returncode == 0