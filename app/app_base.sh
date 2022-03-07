#!/bin/bash

#echo "Setting up TUN interface with IP-address 192.168.1.10/24"
#sudo ip tuntap add mode tun dev tun0
#sudo ip addr add 192.168.1.10/24 dev tun0
#sudo ip link set dev tun0 up

echo "Clearing router table"
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
sudo iptables -F
sudo iptables -X
sudo iptables -t nat -F
sudo iptables -t nat -X
sudo iptables -t mangle -F
sudo iptables -t mangle -X

echo "Setting up router table"
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i tun0 -o eth0 -j ACCEPT

#echo "Setting rate limit"
#sudo iptables -A FORWARD -i eth0 -o tun0 -m state --state RELATED,ESTABLISHED -m limit --limit 10/sec -j ACCEPT

echo "Running base program"
sudo python3 app_base.py