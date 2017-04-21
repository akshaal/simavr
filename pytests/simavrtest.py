from simavr import *
import sys

class SimavrTest (AVRTestCase):
    def init_avr (self, freq = 8000000, mcu = 'attiny85'):
        avr = AVR (filename = sys.argv[0].replace(".py", ".hex"), freq = freq, mcu = mcu)

        self.use_avr (avr)
