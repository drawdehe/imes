import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW
from tuntap import TunTap

radio = RF24(17, 0)
payload = [0.0]

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0", gateway="192.168.2.2")
size = 4

def master(count=0):
    radio.stopListening()
    while count < 5:
        buffer = tun.read(size) # Makes the transmission slow right now
        buffer = struct.pack("<f", payload[0])
        result = radio.write(buffer)
        if not result:
            print("Transmission failed or timed out")
        else:
            print("Transmission successful! Sent:", payload[0])
            payload[0] += 0.01
        count += 1
        #time.sleep(1)

def slave():
    radio.startListening()
    while True:
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            buffer = radio.read(radio.payloadSize)
            tun.write(buffer)
            payload[0] = struct.unpack("<f", buffer[:4])[0]
            print(
                "Received {} bytes on pipe {}: {}".format(
                    radio.payloadSize,
                    pipe_number,
                    payload[0]
                )
            )

def set_role():
    return 0

if __name__ == "__main__":
    radio_number = 1 # Should probably be 1 for one device and 0 for the other device
    if not radio.begin():
        raise RuntimeError("radio hardware is not responding")
    address = [b"1Node", b"2Node"]
    radio.setPALevel(RF24_PA_LOW)
    radio.openWritingPipe(address[radio_number])
    radio.openReadingPipe(1, address[not radio_number])
    radio.payloadSize = len(struct.pack("<f", payload[0]))
    master()
    tun.close()