import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW

radio = RF24(22,0)

if __name__ == "__main__":
    radio.printDetails()