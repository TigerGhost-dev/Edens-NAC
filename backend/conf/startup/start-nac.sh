#!/bin/bash

set -e

PROJECT_DIR="/home/eden/Edens-NAC"
CONF_DIR="$PROJECT_DIR/backend/conf"

LAN_IFACE="wlan0"
WAN_IFACE="wlan1"

LAN_IP="192.168.50.1"

echo "======================================="
echo "      Starting Eden NAC"
echo "======================================="

#############################################
# Stop previous instances
#############################################

pkill -f "python3 app.py" 2>/dev/null || true
pkill hostapd 2>/dev/null || true
pkill dnsmasq 2>/dev/null || true

#############################################
# Release wlan0 ONLY
#############################################

echo "[1/10] Releasing wlan0 from NetworkManager..."

nmcli device set $LAN_IFACE managed no || true

ip link set $LAN_IFACE down

sleep 1

#############################################
# Configure AP mode
#############################################

echo "[2/10] Configuring AP interface..."

iw dev $LAN_IFACE set type __ap

ip addr flush dev $LAN_IFACE

ip addr add ${LAN_IP}/24 dev $LAN_IFACE

ip link set $LAN_IFACE up

#############################################
# Enable routing
#############################################

echo "[3/10] Enabling IP forwarding..."

sysctl -w net.ipv4.ip_forward=1

#############################################
# Reset firewall
#############################################

echo "[4/10] Resetting firewall..."

iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

#############################################
# Create EDEN_NAC chain
#############################################

echo "[5/10] Building firewall..."

iptables -N EDEN_NAC

iptables -A FORWARD \
-i $LAN_IFACE \
-o $WAN_IFACE \
-j EDEN_NAC

iptables -A FORWARD \
-i $WAN_IFACE \
-o $LAN_IFACE \
-m conntrack \
--ctstate RELATED,ESTABLISHED \
-j ACCEPT

iptables -A EDEN_NAC \
-m conntrack \
--ctstate RELATED,ESTABLISHED \
-j ACCEPT

#
# DEFAULT:
# Nobody gets Internet.
#

iptables -A EDEN_NAC -j DROP

#############################################
# NAT
#############################################

iptables -t nat -A POSTROUTING \
-o $WAN_IFACE \
-j MASQUERADE

#############################################
# Captive Portal Redirect
#############################################

iptables -t nat -A PREROUTING \
-i $LAN_IFACE \
-p tcp \
--dport 80 \
-j REDIRECT \
--to-port 5000

#############################################
# Local Services
#############################################

iptables -A INPUT -i $LAN_IFACE -p udp --dport 67 -j ACCEPT
iptables -A INPUT -i $LAN_IFACE -p udp --dport 68 -j ACCEPT

iptables -A INPUT -i $LAN_IFACE -p udp --dport 53 -j ACCEPT
iptables -A INPUT -i $LAN_IFACE -p tcp --dport 53 -j ACCEPT

iptables -A INPUT -i $LAN_IFACE -p tcp --dport 5000 -j ACCEPT

#############################################
# Start Hostapd
#############################################

echo "[6/10] Starting hostapd..."

hostapd \
$CONF_DIR/hostapd/hostapd.conf \
-B

sleep 2

#############################################
# Start DNSMASQ
#############################################

echo "[7/10] Starting dnsmasq..."

dnsmasq \
-C $CONF_DIR/dnsmasq/eden-nac.conf

#############################################
# Start Flask
#############################################

echo "[8/10] Starting portal..."

cd "$PROJECT_DIR"

python3 app.py > /tmp/eden-nac.log 2>&1 &

FLASK_PID=$!

echo $FLASK_PID > /tmp/eden-nac.pid

echo "Waiting for portal..."

for i in {1..10}; do
    if ss -tln | grep -q ":5000"; then
        echo "[✓] Portal started."
        break
    fi
    sleep 1
done

if ! ss -tln | grep -q ":5000"; then
    echo
    echo "[ERROR] Flask failed to start."
    echo
    echo "===== Flask Log ====="
    cat /tmp/eden-nac.log
    exit 1
fi

#############################################
# Status
#############################################

echo

echo "SSID      : Eden-NAC"
echo "Gateway   : 192.168.50.1"
echo "Portal    : http://192.168.50.1:5000"

echo

echo "[✓] Eden NAC Running"