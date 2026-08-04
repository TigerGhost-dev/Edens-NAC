#!/bin/bash

set -e

PROJECT_DIR="/home/eden/Edens-NAC"

LAN_IFACE="wlan0"

echo "======================================="
echo "      Stopping Eden NAC"
echo "======================================="

#############################################
# Stop Flask Portal
#############################################

echo "[1/8] Stopping captive portal..."

if [ -f /tmp/eden-nac.pid ]; then

    PID=$(cat /tmp/eden-nac.pid)

    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        echo "    Flask stopped."
    fi

    rm -f /tmp/eden-nac.pid

fi

#############################################
# Stop hostapd
#############################################

echo "[2/8] Stopping hostapd..."

pkill hostapd 2>/dev/null || true

#############################################
# Stop dnsmasq
#############################################

echo "[3/8] Stopping dnsmasq..."

pkill dnsmasq 2>/dev/null || true

#############################################
# Remove firewall
#############################################

echo "[4/8] Removing firewall..."

iptables -F
iptables -X

iptables -t nat -F
iptables -t nat -X

iptables -t mangle -F
iptables -t mangle -X

#############################################
# Disable forwarding
#############################################

echo "[5/8] Disabling IP forwarding..."

sysctl -w net.ipv4.ip_forward=0

#############################################
# Restore wireless interface
#############################################

echo "[6/8] Restoring wlan0..."

ip addr flush dev "$LAN_IFACE" || true

ip link set "$LAN_IFACE" down || true

iw dev "$LAN_IFACE" set type managed || true

ip link set "$LAN_IFACE" up || true

#############################################
# Return control to NetworkManager
#############################################

echo "[7/8] Returning wlan0 to NetworkManager..."

nmcli device set "$LAN_IFACE" managed yes || true

systemctl restart NetworkManager

#############################################
# Cleanup
#############################################

echo "[8/8] Cleanup..."

rm -f /tmp/eden-nac.log

echo
echo "======================================="
echo "      Eden NAC Stopped"
echo "======================================="