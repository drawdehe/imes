import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW
from tuntap import TunTap
from multiprocessing import Process
from radio import Radio

# radio = RF24(17, 0)
# radio2 = RF24(27, 10)

payload = [0.0]

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0", gateway="192.168.2.2")
size = 4

def tx(tx_radio, count=0):
    tx_radio.stopListening()
    while count < 20:
        start_timer = time.monotonic_ns()
        buffer = tun.read(size) # Seems to make it slow right now
        buffer = struct.pack("<f", payload[0])
        result = tx_radio.write(buffer)
        end_timer = time.monotonic_ns()
        if not result:
            print("Transmission failed or timed out")
        else:
            print(
                "Transmission successful! Time to Transmit: "
                "{} ms. Sent: {}".format(
                    (end_timer - start_timer) / 1000000,
                    payload[0]
                )
            )
            payload[0] += 0.01
            buffer = None # Does not seem to make any difference
        count += 1
        #time.sleep(1)

def rx(rx_radio, timeout=6):
    rx_radio.startListening()
    start_timer = time.monotonic()
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = rx_radio.available_pipe()
        if has_payload:
            buffer = rx_radio.read(rx_radio.payloadSize)
            tun.write(buffer)
            payload[0] = struct.unpack("<f", buffer[:4])[0]
            print(
                "Received {} bytes on pipe {}: {}".format(
                    rx_radio.payloadSize,
                    pipe_number,
                    payload[0]
                )
            )
            start_timer = time.monotonic()

def set_role():
    return 0


if __name__ == "__main__":
    # radio_number = 0 # Should probably be 1 for one device and 0 for the other device
    # if not radio.begin():
    #     raise RuntimeError("radio hardware is not responding")
    # if not radio2.begin():
    #     raise RuntimeError("radio hardware is not responding")
    # address = [b"1Node", b"2Node"]
    # radio.setPALevel(RF24_PA_LOW)
    # radio2.setPALevel(RF24_PA_LOW)

    # radio.setChannel(76)
    # radio2.setChannel(77)

    # radio.openWritingPipe(address[radio_number])
    # radio.openReadingPipe(1, address[not radio_number])

    # radio2.openWritingPipe(address[radio_number])
    # radio2.openReadingPipe(1, address[not radio_number])

    # radio.payloadSize = len(struct.pack("<f", payload[0]))
    # radio2.payloadSize = len(struct.pack("<f", payload[0]))
    channels = [76,77]
    mobile = Radio(channels[0], channels[1])
    base = Radio(channels[1], channels[0])

    tt = Process(target = tx(mobile))
    rt = Process(target = rx(base))
    time.sleep(1)
    tt.start()
    rt.start()
    tt.join()
    rt.join()

    tun.close()