#!/bin/bash

PROJECT_DIR="/home/eden/Edens-NAC/backend/conf"

echo "[+] Starting Eden's NAC..."

# Stop conflicting services
systemctl stop hostapd 2>/dev/null
systemctl stop dnsmasq 2>/dev/null

# Configure AP interface
ip link set wlan0 down

ip addr flush dev wlan0

ip addr add 192.168.50.1/24 dev wlan0

ip link set wlan0 up

# Enable forwarding
sysctl -p $PROJECT_DIR/sysctl/eden-nac.conf

# Clear old firewall rules
iptables -F
iptables -t nat -F

# NAT from clients -> MiFi
iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE

iptables -A FORWARD -i wlan0 -o wlan1 -j ACCEPT

iptables -A FORWARD \
-i wlan1 \
-o wlan0 \
-m state \
--state RELATED,ESTABLISHED \
-j ACCEPT

# Save current rules
iptables-save > $PROJECT_DIR/firewall/nat.rules

echo "[+] Starting hostapd..."
hostapd $PROJECT_DIR/hostapd/hostapd.conf -B

sleep 2

echo "[+] Starting dnsmasq..."
dnsmasq -C $PROJECT_DIR/dnsmasq/eden-nac.conf

echo "[+] Eden's NAC Started"

echo ""
echo "SSID: Eden-NAC"
echo "Gateway: 192.168.50.1"
echo "DHCP Range: 192.168.50.10 - 192.168.50.100"
echo ""
