#!/bin/bash

echo "Deleting TUN interface tun0"
sudo ip link del dev tun0
sudo ip tuntap del dev tun0 mode tun