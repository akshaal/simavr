#!/usr/bin/env python

import simavr

avr = simavr.AVR (filename = "atmega48_ledramp.axf")

def my_timer (arg):
    avr.info ("Wheee: " + arg + "\n")

avr.add_timer_us (100, my_timer, "Hi1")
avr.add_timer_us (200, my_timer, "Hi2")

def on_b_irq (value, i):
    avr.info ("IRQ" + str(i) + " = " + str(value) + "\n")

vcd = simavr.VCD (avr, "signals.vcd")

for i in range (0, 8):
    avr.get_ioport_irq ('B', i).register_notify (on_b_irq, i)
    vcd.add_ioport_signal ("B", i)

button = simavr.PinButton (avr)
button.connect_ioport ("C", 0)
vcd.add_ioport_signal ("C", 0)

vcd.start ()

avr.run_cycles (4000000)
button.set_on (4000000)
avr.run_us (8000000)

vcd.stop
