#!/usr/bin/env python

from simavr import *
import unittest

avr = AVR (filename = "atmega48_ledramp.axf")

class Test (AVRTestCase):
    def test_workflow (self):
        # Prepare test
        self.use_avr (avr)

        bs = [avr.get_ioport_irq ('B', i) for i in range(0, 8)]
        c = avr.get_ioport_irq ('C', 0)

        self.register_irqs (c, *bs)

        # Expect no IRQs for the first 50us
        self.expect_irqs_for_us (50)

        # Expect B0 -> 1 for next 10us
        self.expect_irqs_for_us (10, StopOnFirst, (bs[0], 1))

        # Expect nothing for the next 15ms
        self.expect_irqs_for_ms (15)

        # Expect B0 -> 0, B1 -> 1 for next 10us
        self.expect_irqs_for_us (10, StopWhenAll, (bs[0], 0), (bs[1], 1))

        # ... and so on ...

        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[1], 0), (bs[2], 1))
        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[2], 0), (bs[3], 1))
        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[3], 0), (bs[4], 1))
        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[4], 0), (bs[5], 1))
        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[5], 0), (bs[6], 1))
        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[6], 0), (bs[7], 1))
        self.expect_irqs_for_ms (15)
        self.expect_irqs_for_us (10, StopWhenAll, (bs[7], 0), (bs[0], 1))

        # Lets press the button
        c.raise_irq (0)

        # B0 is already in 1, so it is not supposed to be changed
        self.expect_irqs_for_ms (16, (c, 0),
                                 (bs[1], 1), (bs[2], 1), (bs[3], 1),
                                 (bs[4], 1), (bs[5], 1), (bs[6], 1), (bs[7], 1))

# Run test
unittest.main ()
