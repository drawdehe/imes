#!/bin/bash

echo "Setting up TUN interface with IP-address 192.168.1.16/24"
sudo ip tuntap add mode tun dev tun0
sudo ip addr add 192.168.1.16/24 dev tun0
sudo ip link set dev tun0 up