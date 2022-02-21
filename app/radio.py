import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW



class Radio():
    def __init__(self,rx_channel, tx_channel):

        radio_number = 0
        address = [b"1Node", b"2Node"]

        # Transmitter radio
        radio_one = RF24(17, 0)
        if not radio_one.begin():
            raise RuntimeError("radio_one hardware is not responding")
        radio_one.setPALevel(RF24_PA_LOW)
        radio_one.setChannel(tx_channel)
        radio_one.openWritingPipe(address[radio_number])

        # Receiver radio
        radio_two = RF24(27, 10)
        if not radio_two.begin():
            raise RuntimeError("radio_two hardware is not responding")
        radio_two.setPALevel(RF24_PA_LOW)
        radio_two.setChannel(rx_channel)      
        radio_two.openReadingPipe(0,address[radio_number])
    
    def stopListening(self):
        self.radio_one.stopListening()
    
    def startListening(self):
        self.radio_two.startListening()


