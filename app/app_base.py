import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW
from tuntap import TunTap
from multiprocessing import Process
# import wget

payload = [0.0]

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0", gateway="192.168.2.2")
size = 4

def tx(count=0):
    radio_one.stopListening()
    while count < 20:
        start_timer = time.monotonic_ns()
        #buffer = tun.read(size) # Seems to make it slow right now
        buffer = struct.pack("<f", payload[0])
        result = radio_one.write(buffer)
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

def rx(timeout=6):
    radio_two.startListening()
    start_timer = time.monotonic()
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = radio_two.available_pipe()
        if has_payload:
            buffer = radio.read(radio.payloadSize)
            tun.write(buffer)
            payload[0] = struct.unpack("<f", buffer[:4])[0]
            print(
                "Received {} bytes on pipe {}: {}".format(
                    radio_two.payloadSize,
                    pipe_number,
                    payload[0]
                )
            )
            start_timer = time.monotonic()

# def get_image_from_the_internet():
#     url = "https://cdn.pixabay.com/photo/2020/02/06/09/39/summer-4823612_960_720.jpg"
#     image = wget.download(url)
#     return image

# def transmit_image_to_mobile():
#     image = get_image_from_the_internet()
#     return 0

if __name__ == "__main__":
    radio_number = 0
    address = [b"1Node", b"2Node"]

    # Transmitter radio
    radio_one = RF24(27, 10)
    if not radio_one.begin():
        raise RuntimeError("radio_one hardware is not responding")
    radio_one.setPALevel(RF24_PA_LOW)
    radio_one.setChannel(77)
    radio_one.openWritingPipe(address[radio_number])

    # Receiver radio
    radio_two = RF24(17, 0)
    if not radio_two.begin():
        raise RuntimeError("radio_two hardware is not responding")
    radio_two.setPALevel(RF24_PA_LOW)
    radio_two.setChannel(76)      
    radio_two.openReadingPipe(0,address[radio_number])

    tt = Process(target = tx)
    rt = Process(target = rx)
    time.sleep(1)
    tt.start()
    rt.start()
    tt.join()
    rt.join()

    tun.close()