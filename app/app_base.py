import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW
from tuntap import TunTap
from multiprocessing import Process
import wget

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0")
size = 4

def tx(count=0):
    radio_tx.stopListening()
    while count < 10:
        time.sleep(1)
        start_timer = time.monotonic_ns()
        buffer = tun.read(size)
        result = radio_tx.write(buffer)
        end_timer = time.monotonic_ns()
        if not result:
            print("Transmission failed or timed out")
        else:
            print(
                "Transmission successful! Time to Transmit: "
                "{} ms. Sent: {}".format(
                    (end_timer - start_timer) / 1000000,
                    buffer
                )
            )
        count += 1

def rx(timeout=6):
    radio_rx.startListening()
    start_timer = time.monotonic()
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = radio_rx.available_pipe()
        if has_payload:
            buffer = radio_rx.read(radio_rx.payloadSize)
            tun.write(buffer)
            print(
                "Received {} bytes on pipe {}: {}".format(
                    radio_rx.payloadSize,
                    pipe_number,
                    buffer
                )
            )
            start_timer = time.monotonic()

def get_image_from_the_internet():
    url = "https://cdn.pixabay.com/photo/2020/02/06/09/39/summer-4823612_960_720.jpg"
    image = wget.download(url)
    return image

def transmit_image_to_mobile():
    image = get_image_from_the_internet()
    return 0

if __name__ == "__main__":
    radio_number = 0
    address = [b"1Node", b"2Node"]

    # Transmitter radio
    radio_tx = RF24(27, 10)
    if not radio_tx.begin():
        raise RuntimeError("radio_tx hardware is not responding")
    radio_tx.setPALevel(RF24_PA_LOW)
    radio_tx.setChannel(77)
    radio_tx.openWritingPipe(address[radio_number])

    # Receiver radio
    radio_rx = RF24(17, 0)
    if not radio_rx.begin():
        raise RuntimeError("radio_rx hardware is not responding")
    radio_rx.setPALevel(RF24_PA_LOW)
    radio_rx.setChannel(76)      
    radio_rx.openReadingPipe(0,address[radio_number])

    tt = Process(target = tx)
    #rt = Process(target = rx)
    time.sleep(1)
    tt.start()
    #rt.start()
    tt.join()
    #rt.join()

    tun.close()
