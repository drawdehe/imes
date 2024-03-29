import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_250KBPS, RF24_CRC_8, RF24_CRC_DISABLED
from tuntap import TunTap
from multiprocessing import Process, Queue, Condition, Manager
import math
import codecs

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0")
size = 2 ** 16 - 1

def tx(queue, cond, count=0):
    radio_tx.stopListening()
    print("Running tx")
    #sf = open("service_times.txt", "a")
    while True:
        #cond.acquire()
        #while queue.empty():
         #   print("Queue empty. Waiting...")
          #  cond.wait()
        packet = queue.get(False)
        #cond.release()
        fragments = fragment(packet)
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
        fragment_payload = packet[lower:upper]
        final_fragment = (header + fragment_payload)
        final_fragment = final_fragment[::-1].zfill(32)[::-1] 
        fragments.append(bytes(final_fragment, "utf-8"))
    return fragments

def rx(timeout=10000):
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
                    tun.write(codecs.decode(pkt,"hex")) # codecs.decode() gör om till samma typ av format som när man läser buffern i tx
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
    
        tt = Process(target = tx, args=(queue, cond,))
        rt = Process(target = rx, args=())

        tt.start()
        time.sleep(1)
        rt.start()
        time.sleep(1)
        try:
            print("Running receive_from_internet")
            while True:
                #cond.acquire()
                packet = tun.read(size)
                #print("Received {} bytes from the  internet: {}".format(len(packet), packet.hex()))
                queue.put(packet.hex())
                print("Queue size:", queue.qsize())
                #cond.notify_all()
                #cond.release()
            print("leaving receive_from_internet")
        except KeyboardInterrupt:
            print("Keyboard Interrupt detected.")
            radio_tx.powerDown()
            radio_rx.powerDown()
            tun.close()
            sys.exit()
        tt.join()
        rt.join()
        

    print("Program exiting.")
    tun.close()
