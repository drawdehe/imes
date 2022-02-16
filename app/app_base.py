import sys
import argparse
import time
import struct
from RF24 import RF24, RF24_PA_LOW

radio = RF24(17, 0)

def master():
    return 0

def slave():
    return 0

def set_role():
    return 0

if __name__ == "__main__":
    print("main")