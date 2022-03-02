import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_CRC_8, RF24_CRC_DISABLED, RF24_250KBPS
from tuntap import TunTap
from multiprocessing import Process


# payload = [0.0]

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.16", mask="255.255.255.0")
size = 2**16-1

def tx(count=0):
    radio_tx.stopListening()
    while count < 1000:        
        start_timer = time.monotonic_ns()
        buffer = tun.read(size) # Might need fragmentation
        # print(buffer)
        # buffer = struct.pack("<f", payload[0])

        result = radio_tx.write(buffer)
        end_timer = time.monotonic_ns()
        if not result:
            print("Transmission failed or timed out")
        else:
            print(
                "Transmission successful! Size: {}. Time to Transmit: "
                "{} ms. Sent: {}".format(
                    len(buffer),
                    (end_timer - start_timer) / 1000000,
                    buffer
                )
            )
            # payload[0] += 0.01
            # buffer = None # Does not seem to make any difference
            # print("Transmission successful")
        count += 1
        time.sleep(1)

def fragment(packet):
    # TODO
    # Kopiera header, lägg till fragflag och frag offset, dividera upp payload
    # returnera array
    return 

def rx(timeout=20):
    radio_rx.startListening()
    start_timer = time.monotonic()
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = radio_rx.available_pipe()
        if has_payload:
            buffer = radio_rx.read(radio_rx.payloadSize)
            tun.write(buffer)
            # payload[0] = struct.unpack("<f", buffer[:4])[0]
            print(
                "Received {} bytes on pipe {}: {}".format(
                    radio_rx.payloadSize,
                    pipe_number,
                    buffer
                )
            )
            start_timer = time.monotonic()

def request_image_from_base():
    return 0

def display_image():
    return 0

if __name__ == "__main__":
    radio_number = 0 # Should probably be 1 for one device and 0 for the other device
    address = [b"1Node", b"2Node"]

    # Transmitter radio
    radio_tx = RF24(17, 0, 4000000)
    if not radio_tx.begin():
        raise RuntimeError("radio_tx hardware is not responding")
    radio_tx.setPALevel(RF24_PA_LOW)
    radio_tx.setChannel(76)
    radio_tx.openWritingPipe(address[radio_number])
    radio_tx.setAddressWidth(3)
    radio_tx.setDataRate(RF24_250KBPS)
    radio_tx.setAutoAck(False)
    radio_tx.disableDynamicPayloads()
    radio_tx.setPayloadSize(84)
    radio_tx.setCRCLength(RF24_CRC_DISABLED)

    # Receiver radio
    radio_rx = RF24(27, 10, 4000000)
    if not radio_rx.begin():
        raise RuntimeError("radio_rx hardware is not responding")
    radio_rx.setPALevel(RF24_PA_LOW)
    radio_rx.setChannel(77)      
    radio_rx.openReadingPipe(0,address[radio_number])
    radio_rx.setAddressWidth(3)
    radio_rx.setDataRate(RF24_250KBPS)
    radio_rx.setAutoAck(False)
    radio_rx.disableDynamicPayloads()
    radio_rx.setPayloadSize(84)
    radio_rx.setCRCLength(RF24_CRC_DISABLED)

    try:
       # tt = Process(target = tx)
        rt = Process(target = rx)
        time.sleep(1)
       # tt.start()
        rt.start()
       # tt.join()
        rt.join()
    except KeyboardInterrupt:
        print(" Keyboard Interrupt detected. Exiting...")
        radio_tx.powerDown()
        radio_rx.powerDown()
        tun.close()
        sys.exit()
    print("Program exiting.")
    tun.close()
