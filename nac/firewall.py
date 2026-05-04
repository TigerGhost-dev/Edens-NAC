import os

def block_device(mac):
    os.system(f"sudo iptables -A FORWARD -m mac --mac-source {mac} -j DROP")

def allow_device(mac):
    os.system(f"sudo iptables -D FORWARD -m mac --mac-source {mac} -j DROP")