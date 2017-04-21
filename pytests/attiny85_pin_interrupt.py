#!/usr/bin/env python

from simavr import *
from simavrtest import *
import unittest
import sys

class Test (SimavrTest):
    def test_it (self):
        self.init_avr ()

        pin = self.register_ioport_irq ('B', 0, name = "PIN")
        led = self.register_ioport_irq ('B', 3, name = "LED")

        self.expect_irqs_for_cycles (1000, (pin, 1), (led, 1))

# Run test
unittest.main ()
