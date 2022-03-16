#!/bin/bash
#sudo ip route del default via 192.168.0.1 dev eth0 # Hemma hos Isak
sudo ip route del default via 130.235.200.1 dev eth0 # I skolan
sudo ip route add default via 192.168.1.10 dev tun0
