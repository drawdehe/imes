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
    service_times = open("output/service_times.txt", "w")
    delays = open("output/delays.txt", "w")
    throughput = open("output/throughput.txt", "w")
    count = 0
    while failures < 10:
        count+=1
        condition.acquire()
        while queue.empty():
            print("Queue empty. Waiting...")
            condition.wait()
        start_timer = time.monotonic_ns() 
        payload = queue.get(False)
        buffer = struct.pack("<d", payload)
        # print("payload:", payload)
        # print("buffer", struct.unpack("<d", buffer))
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
            # print("buffer size:", sys.getsizeof(payload))
            service_times.write(str(end_timer-start_timer) + "\n")
            delays.write(str(end_timer - int(payload)) + "\n")
            # print("payload size:", sys.getsizeof(payload), " timer:", (end_timer-start_timer)/1000000000)
            # print("Throughput:", (sys.getsizeof(payload)/((end_timer-start_timer)/1000000000))*8/1000, "kbit/s")
            throughput.write(str((sys.getsizeof(payload)/((end_timer-start_timer)/1000000000))*8) + "\n")
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
            queue_sizes = open("output/queue_size.txt", "w")
            count = 0
            lbda = 1
            while count < 10000:
                cond.acquire()
                payload[0] = time.monotonic_ns()
                queue.put(payload[0])
                cond.notify_all()
                # print("Queued\t {} \t\tQueue size: {}. \tLambda: {}".format(payload[0], queue.qsize(), lbda))
                queue_sizes.write(str(queue.qsize()) + "\n")
                time.sleep(0.01)
                lbda += 1
                # payload[0] += 0.01
                if(lbda % 1000 == 0):
                    print("count: ", lbda)
                count += 1
                cond.release()
            print("Simulation completed")
            queue_sizes.close()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected")      
        
        ttt.join()

    radio_tx.powerDown()
    radio_rx.powerDown()
    sys.exit()
    print("Program exiting.")
    tun.close()