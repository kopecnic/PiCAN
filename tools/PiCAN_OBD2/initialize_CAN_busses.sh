#!/bin/sh

echo Setting Up CAN Busses 

sudo ip link set can0 down
sudo ip link set can1 down

sudo ip link set can0 up type can bitrate 500000
sudo ip link set can1 up type can bitrate 500000

sudo ifconfig can0 txqueuelen 65536
sudo ifconfig can1 txqueuelen 65536

echo Done.