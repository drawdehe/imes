# How to run the program

## On the base station (inuti38)
Navigate to the app/ directory and execute the following command.

> ./app_base.sh

This script clears any existing routing tables and sets up the appropriate new tables. 
The script then executes the app_base.py program, allowing the raspberry pi to act as a base station.
When the program is interrupted, the TUN interface that was created in the app_base.py program is deleted.

## On the mobile unit (inuti37)

Navigate to the app/ directory and execute the following command.

> sudo python3 app_mobile.py

This will prompt the password for inutiuser.

In another terminal, run the mobile.sh script to set the tun0 interface as default.

> ./mobile.sh

Beware that this might terminate your ssh connection if your computer and your raspberry pi are on different subnets.
Now you can ping an internet server from any free terminal on the mobile unit.
