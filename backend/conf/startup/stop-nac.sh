#!/bin/bash

LAN="wlan0"

echo "[+] Stopping Eden NAC..."

pkill hostapd
pkill dnsmasq
pkill python3

iptables -F
iptables -X

iptables -t nat -F
iptables -t nat -X

iptables -t mangle -F
iptables -t mangle -X

echo 0 > /proc/sys/net/ipv4/ip_forward

ip addr flush dev $LAN

ip link set $LAN down

nmcli dev set $LAN managed yes

systemctl restart NetworkManager

echo "[+] Eden NAC Stopped."