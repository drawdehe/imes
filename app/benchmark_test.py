import sys
import time
import struct
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_CRC_8, RF24_CRC_DISABLED, RF24_250KBPS
from multiprocessing import Process, Queue, Condition, Manager
import math
import codecs
import os

size = 2**16-1

# def test_tx():
#     radio_tx.stopListening()
#     while True:
#         cond.acquire()
#         while queue.empty():
#             print("Queue empty. Waiting...")
#             cond.wait()
#         start_time = time.monotonic_ns()
#         test_data = queue.get()
#         result = radio_tx.write(test_data)
#         if not result:
#             print("Transmission failed or timed out")
#         else:
#             end_time = time.monotonic_ns()
#             print(
#                 "Transmission successful! Size: {}. Time to Transmit: "
#                 "{} ms. Sent: {}".format(
#                     len(test_data),
#                     (end_timer - start_timer) / 1000000,
#                     test_data
#                 )
#             )
#         cond.release()

def test_tx(queue, cond, count=0):
    radio_tx.stopListening()
    print("Running tx")
    sf = open("service_times.txt", "a")
    while True:
        cond.acquire()
        while queue.empty():
            print("Queue empty. Waiting...")
            cond.wait()
        # Betjäning påbörjas
        start_timer = time.monotonic_ns()
        test_data = queue.get(False)
        fragments = fragment(test_data)
        for f in fragments:
            frag_start = time.monotonic_ns()
            result = radio_tx.write(f)
            frag_sent = time.monotonic_ns()
            if not result:
                print("Transmission failed or timed out")
            else:
                print(
                    "Transmission successful! Time to Transmit: "
                    "{} ms. Sent: {}. Size: {}.".format(
                        (frag_sent- frag_start) / 1000000,
                        f,
                        len(f)
                    )
                )
                # Betjäning avslutas
                end_timer = time.monotonic_ns()
                service_time = end_timer - start_timer
                # Print and write to file
                print("Service time:", service_time/1000000, " ms")
                sf.write(str(service_time) + "\n")
        cond.release()
    print("tx done")
    

def fragment(packet):
    # 4 byte header
    nbr_of_frags = 4
    frag_nbr = 4
    id_size = 0
    payload_size = 32 - nbr_of_frags - frag_nbr - id_size
    total_frags = math.ceil(len(packet)/payload_size)
    fragments = []
    for nbr in range(total_frags):
        lower = payload_size * nbr
        upper = payload_size * (nbr + 1)
        nbr = nbr + 1
        header = hex(nbr)[2:].zfill(4) + hex(total_frags)[2:].zfill(4)
        # header = hex(nbr)[2:].zfill(4) + hex(total_frags)[2:].zfill(4) + hex(id).zfill(2) #ifall vi kör id
        fragment_payload = packet[lower:upper]
        final_fragment = (header + fragment_payload)
        final_fragment = final_fragment[::-1].zfill(32)[::-1] 
        fragments.append(bytes(final_fragment, "utf-8"))
    return fragments

# def test_rx():
#     radio_rx.startListening()
#     while True:
#         cond.acquire()
#         has_payload, pipe_number = radio_rx.available_pipe()
#         if has_payload:
#             buffer = radio_rx.read(radio_rx.payloadSize)
#             queue.put(buffer)   
#         cond.release()

def test_rx(queue, cond, timeout=10000):
    radio_rx.startListening()
    start_timer = time.monotonic()
    fragments = []
    print("Running rx")
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = radio_rx.available_pipe()
        if has_payload:
            buffer = radio_rx.read(size)
            try:
                total_frags = int(buffer[4:8].decode())
                fragments.append(buffer)
                if len(fragments) == total_frags:
                    pkt = defragment(fragments)
                    print(
                        "Received {} bytes on pipe {}: {}".format(
                            math.ceil(len(pkt)/2),
                            pipe_number,
                            pkt
                        )
                    )
                    queue.put(pkt)
                    fragments = []
            except UnicodeDecodeError:
                print("Error, but ignore it")
                print("Errored packet:", buffer)
            start_timer = time.monotonic()
    print("leaving rx")

def defragment(fragments):
    pkt = bytearray(0)
    for frg in fragments:
        pkt = pkt + frg[8:]
    return bytes(pkt)

if __name__ == "__main__":
    radio_number = 0 
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
    radio_tx.setPayloadSize(64)
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
    radio_rx.setPayloadSize(64)
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
