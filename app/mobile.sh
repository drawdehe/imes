#!/bin/bash
sudo ip route del default via 192.168.0.1 dev eth0
sudo ip route add default via 192.168.1.10 dev tun0
