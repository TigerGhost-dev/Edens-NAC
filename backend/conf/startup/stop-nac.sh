#!/bin/bash

echo "[+] Stopping Eden's NAC..."

pkill hostapd
pkill dnsmasq

iptables -F
iptables -t nat -F

ip addr flush dev wlan0

ip link set wlan0 down

systemctl restart NetworkManager

echo "[+] Eden's NAC Stopped"
