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
    service_times = open("service_times.txt", "w")
    delays = open("delays.txt", "w")
    count = 0
    while failures < 10:
        count+=1
        condition.acquire()
        while queue.empty():
            print("Queue empty. Waiting...")
            condition.wait()
        start_timer = time.monotonic_ns() 
        payload = queue.get(False)
        buffer = struct.pack("<f", payload)
        result = radio_tx.write(buffer)
        end_timer = time.monotonic_ns()
        if not result:
            print("Transmission failed or timed out")
            failures += 1
        else:
            # print(
            #     "Transmission successful! Time to Transmit: "
            #     "{} ms. Sent: {}".format(
            #         (end_timer - start_timer) / 1000000,
            #         payload
            #     )
            # )
            service_times.write(str(end_timer-start_timer) + "\n")
            delays.write(str(count) + "\t" + str(end_timer - int(payload)) + "\t" + str(queue.qsize()) +  "\n")
        # Decreasing sleep time
        condition.release()
    service_times.close()
    delays.close()

if __name__ == "__main__":
    radio_number = 0 
    address = [b"1Node", b"2Node"]

    # Transmitter radio
    radio_tx = RF24(17, 0, 400000)
    if not radio_tx.begin():
        raise RuntimeError("radio_tx hardware is not responding")
    radio_tx.setPALevel(RF24_PA_LOW)
    radio_tx.setChannel(76)
    radio_tx.openWritingPipe(address[radio_number])
    radio_tx.setAddressWidth(3)
    radio_tx.setDataRate(RF24_250KBPS)
    radio_tx.setAutoAck(False)
    radio_tx.disableDynamicPayloads()
    radio_tx.setPayloadSize(32)
    radio_tx.setCRCLength(RF24_CRC_DISABLED)

    # Receiver radio
    radio_rx = RF24(27, 10, 400000)
    if not radio_rx.begin():
        raise RuntimeError("radio_rx hardware is not responding")
    radio_rx.setPALevel(RF24_PA_LOW)
    radio_rx.setChannel(77)      
    radio_rx.openReadingPipe(0,address[radio_number])
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

        ttt.start()
        time.sleep(1)
        
        payload = [0.0]

        try:
            queue_sizes = open("queue_size.txt", "w")
            count = 0
            lbda = 1
            while count < 100000:
                cond.acquire()
                # print("payload: ", payload[0])
                payload[0] = time.monotonic_ns()
                queue.put(payload[0])
                cond.notify_all()
                print("Queued\t {} \t\tQueue size: {}. \tLambda: {}".format(payload[0], queue.qsize(), lbda))
                queue_sizes.write(str(lbda) + " " + str(queue.qsize()) + "\n")
                time.sleep(1/lbda)
                lbda *= 1.01
                payload[0] += 0.01
                count += 1
                cond.release()
            queue_sizes.close()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected")      
        
        ttt.join()

    radio_tx.powerDown()
    radio_rx.powerDown()
    sys.exit()
    print("Program exiting.")
    tun.close()

# def test_rx(queue, condition, timeout=10):
#     radio_rx.startListening()  # put radio in RX mode
#     start_timer = time.monotonic()
#     while (time.monotonic() - start_timer) < timeout:
#         condition.acquire()
#         has_payload, pipe_number = radio_rx.available_pipe()
#         if has_payload:
#             buffer = radio_rx.read(radio_rx.payloadSize)
#             payload[0] = struct.unpack("<f", buffer[:4])[0]
#             queue.put(payload[0])
#             condition.notify_all()
#             print(
#                 "Received {} bytes on pipe {}: {}".format(
#                     radio_rx.payloadSize,
#                     pipe_number,
#                     payload[0]
#                 )
#             )
#             start_timer = time.monotonic()  # reset the timeout timer
#         condition.release()
#     print("Nothing received in", timeout, "seconds. Leaving RX role")
#     # recommended behavior is to keep in TX mode while idle
#     radio_rx.stopListening()  # put the radio in TX mode