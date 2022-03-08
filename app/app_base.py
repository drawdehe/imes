import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_250KBPS, RF24_CRC_8, RF24_CRC_DISABLED
from tuntap import TunTap
from multiprocessing import Process
import wget
import math
from scapy.all import *
import codecs

iface = 'LongGe'
tun = TunTap(nic_type="Tun", nic_name="tun0")
tun.config(ip="192.168.1.10", mask="255.255.255.0")
size = 2 ** 16 - 1

def tx(count=0):
    radio_tx.stopListening()
    nbr_transmitted = 0
    while count < 1000:
        packet = tun.read(size)

        # print("Packet before fragmentation: ", packet.hex())

        # Fragmentation
        fragments = fragment(packet)

        for f in fragments:
            start_timer = time.monotonic_ns()
            result = radio_tx.write(f)
            end_timer = time.monotonic_ns()
            if not result:
                print("Transmission failed or timed out")
            else:
                print(
                    "Transmission successful! Packet number: {}. Time to Transmit: "
                    "{} ms. Sent: {}. Size: {}".format(
                        count +1 ,
                        (end_timer - start_timer) / 1000000,
                        f,
                        len(f)
                    )
                )
        count += 1

def rx(timeout=10000):
    radio_rx.startListening()
    start_timer = time.monotonic()
    fragments = []
    while (time.monotonic() - start_timer) < timeout:
        has_payload, pipe_number = radio_rx.available_pipe()
        if has_payload:
            buffer = radio_rx.read(size)
            print("raw received data:", buffer)
            #print("isPv4: ", isIpv4(buffer))
            try:
                no_of_fragments = int(buffer[4:8].decode())

                print("NO OF FRAGMENTS?", no_of_fragments)
                #if (type(buffer) == )
                print("TYPE BUFFER", buffer)
                fragments.append(buffer)
                
                if len(fragments) == no_of_fragments:
                    pkt = defragment(fragments)
                    print(
                        "Received {} bytes on pipe {}: {}".format(
                            len(pkt),
                            pipe_number,
                            pkt
                        )
                    )
                    tun.write(codecs.decode(pkt,"hex")) # codecs.decode() gör om till samma typ av format som när man läser buffern i tx
                    fragments = []

            except UnicodeDecodeError:
                print("Error, but ignore it")
            
            start_timer = time.monotonic()

def fragment(packet):
    # 4 byte header
    header_size = 4
    payload_size = 16 - header_size
    no_of_fragments = math.ceil(len(packet)/payload_size)
    fragments = []
    for nbr in range(no_of_fragments):
        lower = payload_size * nbr
        upper = payload_size * (nbr + 1)
        nbr = nbr + 1
        header = hex(nbr)[2:].zfill(4) + hex(no_of_fragments)[2:].zfill(4) 
        fragment_payload = packet[lower:upper]
        final_fragment = (header + fragment_payload.hex())
        final_fragment = final_fragment[::-1].zfill(32)[::-1] 
        fragments.append(bytes(final_fragment, "utf-8"))
        # print("Fragment no. {}:\t {}".format(nbr, final_fragment))
    return fragments

def defragment(fragments):
    pkt = bytearray(0)
    for frg in fragments:
        # print("fragment: ", frg[8:])
        pkt = pkt + frg[8:]
    return bytes(pkt)

#def isIpv4(packet): #not working atm
 #   return packet[0:1].hex()[1] == '4'

def get_image_from_the_internet():
    url = "https://cdn.pixabay.com/photo/2020/02/06/09/39/summer-4823612_960_720.jpg"
    image = wget.download(url)
    return image

def transmit_image_to_mobile():
    image = get_image_from_the_internet()
    return 0

"""
def defragment(fragment):
    if (defragment_buffer == None):
        defragment_buffer = [None] * total_fragment_nbr
    fragment_nbr = int(fragment[:4])
    total_fragment_nbr = int(fragment[4:8])
    payload = 0
    defragment_buffer[fragment_nbr - 1] = fragment[8:]
    if None not in defragment_buffer:
        for f in defragment_buffer:
            payload = payload + f
        defragment_buffer = None
        print("Payload after defragmentation: ", payload)
        return payload
"""

"""
def fragment(packet):
    fragments = []

    if packet[0:1].hex()[1] == '4': # IPv4
        ihl = packet[1:2].hex()[1]
        ihl = int(ihl)
        header = packet[0:ihl*8]
        print("Header: ", header)
        payload = packet[ihl*8:]       
        
        nbr_fragments = 0
        max_payload_size = 12 #in bytes
        print("Payload before split: ", payload)
        while len(payload) > 0:
            print("\nFragment no.", nbr_fragments+1)
            if(len(payload) <= max_payload_size*2): 
                # Add header w/ offset + no more fragments

                x = header[:13]
                y = header[16:]

                o = nbr_fragments * max_payload_size # payload is 12
                o_hex = hex(o)
                z_o_hex = o_hex[2:].zfill(3)

                h = x + bytes(z_o_hex, 'utf-8') + y
                f = h + payload[:]

                fragments.append(f)
                print("Fragment header:\t", h)
                print("Fragment with payload:\t", f)
                payload = 0
                break
            else:
                # Add header w/ or without offset + more fragments
                temp = list(header)

                # Set more fragments flag
                temp[12] = 50

                # Offset field

                offset = nbr_fragments * max_payload_size # payload is 12
                offset_hex = hex(offset)
                zoffset_hex = offset_hex[2:].zfill(3)

                # Convert new header to bytes, append fragmented payload

                new_header = bytes(temp)

                first_part_header = new_header[:13]
                last_part_header = new_header[16:]

                final_header = first_part_header + bytes(zoffset_hex, 'utf-8') + last_part_header
                print("Fragment header:\t", final_header)

                fragment = final_header + payload[:max_payload_size*2]
                fragments.append(fragment)
                print("Fragment with payload:\t", fragment)

                payload = payload[max_payload_size*2:]
            nbr_fragments = nbr_fragments + 1
    return fragments
"""

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

    try:
        tt = Process(target = tx)
        rt = Process(target = rx)
        time.sleep(1)
        tt.start()
        rt.start()
        tt.join()
        rt.join()
    except KeyboardInterrupt:
        print("Keyboard Interrupt detected. Exiting...")
        radio_tx.powerDown()
        radio_rx.powerDown()
        tun.close()
        sys.exit()
    print("Program exiting.")
    tun.close()