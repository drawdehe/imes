import sys
import time
import struct
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_CRC_8, RF24_CRC_DISABLED, RF24_250KBPS
from multiprocessing import Process, Queue, Condition, Manager
import math
import codecs
import os

size = 2**16-1

payload = [0.0]


def test_tx(queue, condition):
    """Transmits an incrementing float every second"""
    radio_tx.stopListening()  # put radio in TX mode
    failures = 0
    while True:
        # Generate tx data (32 bytes?)
        buffer = struct.pack("<f", payload[0])
        start_timer = time.monotonic_ns()  # start timer
        result = radio_tx.write(buffer)
        end_timer = time.monotonic_ns()  # end timer
        if not result:
            print("Transmission failed or timed out")
            failures += 1
        else:
            print(
                "Transmission successful! Time to Transmit: "
                "{} ms. Sent: {}".format(
                    (end_timer - start_timer) / 1000000,
                    payload[0]
                )
            )
            payload[0] += 0.01
        time.sleep(1)
    print(failures, "failures detected. Leaving TX role.")


def test_rx(queue, condition, timeout=6):
    """Listen for any payloads and print the transaction

    :param int timeout: The number of seconds to wait (with no transmission)
        until exiting function.
    """
    radio_rx.startListening()  # put radio in RX mode

    start_timer = time.monotonic()
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = radio_rx.available_pipe()
        if has_payload:
            # fetch 1 payload from RX FIFO
            buffer = radio_rx.read(radio.payloadSize)
            # use struct.unpack() to convert the buffer into usable data
            # expecting a little endian float, thus the format string "<f"
            # buffer[:4] truncates padded 0s in case payloadSize was not set
            payload[0] = struct.unpack("<f", buffer[:4])[0]
            # print details about the received packet
            print(
                "Received {} bytes on pipe {}: {}".format(
                    radio_rx.payloadSize,
                    pipe_number,
                    payload[0]
                )
            )
            start_timer = time.monotonic()  # reset the timeout timer

    print("Nothing received in", timeout, "seconds. Leaving RX role")
    # recommended behavior is to keep in TX mode while idle
    radio_rx.stopListening()  # put the radio in TX mode

if __name__ == "__main__":
    radio_number = 0 
    address = [b"1Node", b"2Node"]

    # Transmitter radio
    radio_tx = RF24(27, 10, 400000)
    if not radio_tx.begin():
        raise RuntimeError("radio_tx hardware is not responding")
    radio_tx.setPALevel(RF24_PA_LOW)
    radio_tx.setChannel(77)
    radio_tx.openWritingPipe(address[radio_number])
    radio_tx.setAddressWidth(3)
    radio_tx.setDataRate(RF24_250KBPS)
    radio_tx.setAutoAck(False)
    radio_tx.disableDynamicPayloads()
    radio_tx.setPayloadSize(32)
    radio_tx.setCRCLength(RF24_CRC_DISABLED)

    # Receiver radio
    radio_rx = RF24(17, 0, 400000)
    if not radio_rx.begin():
        raise RuntimeError("radio_rx hardware is not responding")
    radio_rx.setPALevel(RF24_PA_LOW)
    radio_rx.setChannel(76)      
    radio_rx.openReadingPipe(0, address[radio_number])
    radio_rx.setAddressWidth(3)
    radio_rx.setDataRate(RF24_250KBPS)
    radio_rx.setAutoAck(False)
    radio_rx.disableDynamicPayloads()
    radio_rx.setPayloadSize(32)
    radio_rx.setCRCLength(RF24_CRC_DISABLED)

    with Manager() as manager:
        queue = manager.Queue()
        cond = manager.Condition()
        ttt = Process(target=test_tx, args=(queue, cond,))
        trt = Process(target=test_rx, args=(queue, cond,))

        ttt.start()
        time.sleep(1)
        trt.start()
        
        ttt.join()
        trt.join()

    radio_tx.powerDown()
    radio_rx.powerDown()
    sys.exit()
    print("Program exiting.")
    tun.close()
