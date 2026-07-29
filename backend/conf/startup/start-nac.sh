#!/bin/bash

##############################################
# Eden's NAC Startup Script
##############################################

set -e

PROJECT_DIR="/home/eden/Edens-NAC"
CONF_DIR="$PROJECT_DIR/backend/conf"

AP_IFACE="wlan0"
WAN_IFACE="wlan1"

AP_IP="192.168.50.1"
PORTAL_PORT="5000"

echo
echo "========================================"
echo "        Eden's NAC Starting"
echo "========================================"
echo

##############################################
# Stop old services
##############################################

echo "[1/10] Stopping old services..."

pkill -f "python3 app.py" 2>/dev/null || true
pkill hostapd 2>/dev/null || true
pkill dnsmasq 2>/dev/null || true

##############################################
# Release wlan0 from NetworkManager
##############################################

echo "[2/10] Releasing wlan0..."

systemctl stop wpa_supplicant@$AP_IFACE 2>/dev/null || true
killall wpa_supplicant 2>/dev/null || true

nmcli dev set $AP_IFACE managed no 2>/dev/null || true

rfkill unblock wifi

##############################################
# Configure AP Interface
##############################################

echo "[3/10] Configuring wlan0..."

ip link set $AP_IFACE down

ip addr flush dev $AP_IFACE

iw dev $AP_IFACE set type __ap

ip addr add $AP_IP/24 dev $AP_IFACE

ip link set $AP_IFACE up

##############################################
# Enable Routing
##############################################

echo "[4/10] Enabling IP Forwarding..."

sysctl -w net.ipv4.ip_forward=1

##############################################
# Firewall Reset
##############################################

echo "[5/10] Resetting firewall..."

iptables -F
iptables -X

iptables -t nat -F
iptables -t nat -X

##############################################
# Default Forward Policy
##############################################

iptables -P FORWARD ACCEPT

##############################################
# NAT
##############################################

echo "[6/10] Configuring NAT..."

iptables -t nat -A POSTROUTING \
-o $WAN_IFACE \
-j MASQUERADE

iptables -A FORWARD \
-i $WAN_IFACE \
-o $AP_IFACE \
-m state \
--state RELATED,ESTABLISHED \
-j ACCEPT

##############################################
# DNS
##############################################

iptables -A INPUT \
-i $AP_IFACE \
-p udp \
--dport 53 \
-j ACCEPT

iptables -A INPUT \
-i $AP_IFACE \
-p tcp \
--dport 53 \
-j ACCEPT

##############################################
# DHCP
##############################################

iptables -A INPUT \
-i $AP_IFACE \
-p udp \
--dport 67 \
-j ACCEPT

iptables -A INPUT \
-i $AP_IFACE \
-p udp \
--dport 68 \
-j ACCEPT

##############################################
# Portal
##############################################

iptables -A INPUT \
-i $AP_IFACE \
-p tcp \
--dport $PORTAL_PORT \
-j ACCEPT

##############################################
# Captive Portal Redirect
##############################################

echo "[7/10] Installing captive portal..."

iptables -t nat -A PREROUTING \
-i $AP_IFACE \
-p tcp \
--dport 80 \
-j REDIRECT \
--to-ports $PORTAL_PORT

##############################################
# Start hostapd
##############################################

echo "[8/10] Starting hostapd..."

hostapd \
$CONF_DIR/hostapd/hostapd.conf \
-B

sleep 2

##############################################
# Start dnsmasq
##############################################

echo "[9/10] Starting dnsmasq..."

dnsmasq \
-C $CONF_DIR/dnsmasq/eden-nac.conf

##############################################
# Start Flask + Controller
##############################################

echo "[10/10] Starting Eden Portal..."

cd "$PROJECT_DIR"

python3 app.py &

sleep 3

echo
echo "========================================"
echo " Eden's NAC Started Successfully"
echo "========================================"
echo
echo "SSID      : Eden-NAC"
echo "Gateway   : 192.168.50.1"
echo "Portal    : http://192.168.50.1:5000"
echo "WAN       : $WAN_IFACE"
echo