#!/usr/bin/env python
# Akshaal (C) 2010, GNU GPL. http://akshaal.info

from csimavr import *
import _csimavr
import unittest

# - - - - Global state - - -

# We need to keep timer from being garbage collected while it is scheduled. This is an easiest way to do it.
active_timers = set ()
registered_irq_notifiers = set ()
connected_irqs = set ()
active_vcds = set ()

StopOnFirst = "StopOnFirst"
StopWhenAll = "StopWhenAll"

# - - - - Classes - - - - -

class AVRException(Exception):
    """AVR exception."""

    def __init__ (self, msg):
        self.msg = msg

    def __str__ (self):
        return self.msg


class AVR (avr_t):
    """Main class. Represents an AVR instance."""

    def __init__(self,
                 filename,
                 mcu = None,
                 freq = None,
                 gdb = False,
                 trace = False,
                 gdb_port = 1234,
                 load_base = AVR_SEGMENT_OFFSET_FLASH,
                 quiet = False):
        """Initializer for AVR class."""

        self.__quiet = quiet

        self._firmware = elf_firmware_t ()

        self._prepare_firmware (filename)

        # Override some firmware options
        if mcu != None:   self._firmware.mmcu = mcu
        if freq != None:  self._firmware.frequency = freq

        # Checks
        if self._firmware.mmcu == None:
            raise AVRException ("mcu is not defined")

        if self._firmware.frequency == None:
            raise AVRException ("frequency is not defined")

        # Create AVR
        super (AVR, self).__init__ (self._firmware.mmcu)

        if self.this == None:
            raise AVRException ("AVR " + str(mcu) + " is not known")

        # Initializing
        self._init ()

        # Loading firmware
        self._load_firmware ()

        # Take care of bootloader
        if self._firmware.flashbase > 0:
            if not self.__quiet: print "Attempted to load a bootloader at %04x" % self._firmware.flashbase
            self.pc = self._firmware.flashbase

        # Setup gdb in case of crash or explicit activation
        self.gdb_port = gdb_port
        if gdb:
            self.gdb_init ()

        # Enable or disable trace
        self.trace = trace

    def _prepare_firmware (self, filename):
        """Prepare firmware from filename."""

        if filename.lower().endswith (".hex"):
            self.__chunks = ihex_chunk_t_array (4)
            chunks_count = read_ihex_chunks (filename, self.__chunks, 4)
            if chunks_count < 0:
                raise AVRException ("Unable to load IHEX file: " + filename)

            if not self.__quiet: print "Loaded", chunks_count, "sections of IHEX"

            for ci in range (chunks_count):
                chunk = self.__chunks [ci]

                if chunk.baseaddr < 1 * 1024 * 1024:
                    self._firmware.flash = chunk.data
                    self._firmware.flashsize = chunk.size
                    self._firmware.flashbase = chunk.baseaddr

                    flash_info = {'base': self._firmware.flashbase, 'size': self._firmware.flashsize}
                    if not self.__quiet: print "Load HEX flash base=%(base)08x size=%(size)d" % flash_info
                elif (chunk.baseaddr >= AVR_SEGMENT_OFFSET_EEPROM or
                            chunk.baseaddr + loadBase >= AVR_SEGMENT_OFFSET_EEPROM):
                    self._firmware.eeprom = chunk.data;
                    self._firmware.eesize = chunk.size;

                    eeprom_info = {'base': self._firmware.eeprom, 'size': self._firmware.eesize}
                    if not self.__quiet: print "Load HEX eeprom base=%(base)08x size=%(size)d" % eeprom_info
        else:
            elf_read_firmware (filename, self._firmware)

    def _init (self):
        """Initialize AVR."""

        avr_init (self)

    def _load_firmware (self):
        """Load prepared firmware into the AVR."""

        avr_load_firmware (self, self._firmware)

    def gdb_init (self):
        """Initialize GDB. This sets AVR into Stopped state."""

        self.state = cpu_Stopped
        avr_gdb_init (self)

    def terminate (self):
        """Terminate AVR."""

        avr_terminate (self)

    def run (self):
        """Run AVR."""

        while True:
            self.run_cycles ()

    def run_one (self):
        """Run one instruction."""

        avr_run_one (self)

    def run_cycles (self, cycles = 1):
        """Run cycles."""

        end_cycle = self.cycle + cycles

        while self.cycle < end_cycle:
            avr_run (self)

    def run_us (self, us):
        """Run given number of useconds"""

        self.run_cycles (self.usec_to_cycles (us))

    def reset (self):
        """Resets the AVR, and the IO modules."""

        avr_reset (self)

    def info (self, *args):
        """Write formatted information (printf like)."""

        avr_info (self, *args)

    def sadly_crashed (self, signal):
        """Called when the core has detected a crash somehow.
           This might activate gdb server.
        """

        avr_sadly_crashed (self, signal)

    def usec_to_cycles (self, usecs):
        """Converts a number of usec to a number of machine cycles, at current speed."""

        return avr_usec_to_cycles (self, usecs)

    def cycles_to_usec (self, cycles):
        """Converts back a number of cycles to usecs (for usleep)."""

        return avr_cycles_to_usec (self, cycles)

    def hz_to_cycles (self, hz):
        """Converts a number of hz to a number of cycles."""

        return avr_hz_to_cycles (self, hz)

    def add_timer (self, in_cycles, callback, callback_arg = None):
        """Create a new timer. The given callback will be invoked with the given callback argument in the given cycles."""

        return Timer (self, in_cycles, callback, callback_arg)

    def add_timer_us (self, in_us, callback, callback_arg = None):
        """Create a new timer. The given callback will be invoked with the given callback argument in the given us."""

        return Timer (self, self.usec_to_cycles (in_us), callback, callback_arg)

    def get_io_irq (self, ctl, index, name = None):
        """Get the specific irq for a module."""

        irq = IRQ (pool = None, _free = False, _instance = avr_io_getirq (self, ctl, index))
        if name == None:
            irq.set_name ("ctl" + str(ctl) + "-" + str(index))
        else:
            irq.set_name (name)

        return irq

    def get_ioport_irq (self, letter, index, name = None):
        """Get IRQ of the given ioport (by letter like A, B, C...)."""

        irq = self.get_io_irq (avr_ioctl_ioport_getirq (letter.upper()), index)
        if name == None:
            irq.set_name ("ioport_" + letter + str(index))
        else:
            irq.set_name (name)

        return irq

    def get_iomem_irq (self, register, index, name = None):
        """Get IRQ of for the given io memory register."""

        irq = IRQ (pool = None, _free = False, _instance = avr_iomem_getirq (self, register, index))
        if name == None:
            irq.set_name ("iomem_0x" + hex(register) + "_" + str(index))
        else:
            irq.set_name (name)

        return irq

class Timer:
    """Timer that can be triggered by AVR's cycles."""

    def __init__ (self, avr, in_cycles, callback, callback_arg = None):
        """Create a new timer. The given callback will be invoked with the given callback argument in the given cycles."""

        self.__callback = callback
        self.__callback_arg = callback_arg
        self.__avr = avr

        self.set_cycles (in_cycles)

    def set_cycles (self, in_cycles):
        """Changes in what number cycles timer will be triggered."""

        avr_cycle_timer_register_py (self.__avr, in_cycles, self)
        active_timers.add (self)

    def cancel (self):
        """Cancel timer."""

        avr_cycle_timer_cancel_py (self.__avr, self)

        # Because it is called from __del__, it well can be that globar var is unavailable
        if active_timers != None:
            active_timers.discard (self)

    def _timer_handler (self):
        """This method is called by C code."""

        in_cycles = self.__callback (self.__callback_arg)

        if in_cycles == None or in_cycles == 0:
            active_timers.discard (self)
            in_cycles = 0
        else:
            in_cycles += self.__avr.cycle

        return in_cycles

    def __del__ (self):
        """Destructor."""

        self.cancel ()


class IRQ (avr_irq_t):
    """IRQ"""

    def __init__ (self, pool, base = 0, count = 1, _free = True, _instance = None):
        """Constructor."""

        # This object can be created from scratch or it can be create from
        # existing instance of avr_irq_t
        if _instance == None:
            super (IRQ, self).__init__ (pool, base, count)
        else:
            _csimavr.avr_irq_t_swiginit (self, _instance)

        self.__count = count
        self.__free = _free
        self.__name = "UnnamedIRQ"

    def set_name (self, name):
        """Set human readable name for IRQ"""

        self.__name = name

    def __repr__ (self):
        """Representation."""

        return "<IRQ " + self.__name + ">"

    def __del__ (self):
        """Destructor."""

        if self.__free and avr_free_irq != None:
            avr_free_irq (self, self.__count)

    def __len__ (self):
        """Length."""

        return self.__count

    def __getitem__ (self, key):
        """Support for indexed access."""

        if key in range (0, self.__count):
            return IRQ (pool = None, _free = False, _instance = _get_by_index (key))
        else:
            raise IndexError ()

    def raise_irq (self, value):
        """Raise an IRQ. I.e. call their 'hooks', and raise any chained IRQs, and set the new 'value'."""

        if value == True:
            value = 1
        elif value == False:
            value = 0

        avr_raise_irq (self, value)

    def connect_source (self, source):
        """Let this IRQ be a destination for the given source IRQ."""

        source.connect_destination (self)

    def connect_destination (self, destination):
        """Let this IRQ be a source for the given destination IRQ."""

        avr_connect_irq (self, destination)
        connected_irqs.add ((self, destination))

    def register_notify (self, callback, callback_arg = None):
        """Register a notification hook for the irq."""

        # Prevent from being GCed
        param = (self, callback, callback_arg)

        if not (param in registered_irq_notifiers):
            registered_irq_notifiers.add (param)
            avr_irq_register_notify_py (self, param)

    def _notify_handler (self, param, value):
        """Called on notification from C code. Used to dispatch to python method."""

        (_, callback, callback_arg) = param
        callback (value, callback_arg)


class PinButton:
    """Button connected to a pin"""

    def __init__ (self, avr, pullup = True):
        """Construct."""

        self.__avr = avr
        self.__irq = IRQ (pool = avr.irq_pool)
        self.__on = not pullup
        self.__off = pullup
        self.__timer = None

    def connect_ioport (self, portname, index):
        """Connect to named io port of the given AVR. Pin of port is selected by index."""

        self.__avr.get_ioport_irq (portname, index).connect_source (self.__irq)

    def set_on (self, timeout_us = None):
        """Set button to On state"""

        self.__set_value (self.__on, timeout_us)

    def set_off (self, timeout_us = None):
        """Set button to On state"""

        self.__set_value (self.__off, timeout_us)

    def __set_value (self, value, timeout_us):
        self.__disable_timer ()
        self.__irq.raise_irq (value)

        if timeout_us != None:
            def handler (param):
                self.__set_value (not value, None)

            self.__timer = self.__avr.add_timer_us (timeout_us, handler)

    def __disable_timer (self):
        if self.__timer != None:
            self.__timer.cancel ()
            self.__timer = None

class VCD:
    def __init__ (self, avr, filename, flush_period=100000):
        """Construct new VCD file writer."""

        self.__avr = avr
        self.__vcd = avr_vcd_t ()
        avr_vcd_init (avr, filename, self.__vcd, flush_period)

    def start (self):
        """Start writing to file."""

        avr_vcd_start (self.__vcd)

    def stop (self):
        """Stop writing to file."""

        avr_vcd_stop (self.__vcd)

    def add_signal (self, irq, bit_size, name):
        """Add signal to watch."""

        avr_vcd_add_signal (self.__vcd, irq, bit_size, name)
        active_vcds.add (self) # Don't let to GC us

    def add_ioport_signal (self, name, index, bit_size = 1):
        """Add signal for ioport pin."""

        self.add_signal (self.__avr.get_ioport_irq (name, index), bit_size, name + "-" + str(index))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Testing

class AVRTestCase (unittest.TestCase):
    """Class to help testing of AVR's firmware."""

    def use_avr (self, avr):
        """Called to specify AVR to test."""

        self.__avr = avr

    def setUp (self):
        """Clear state."""

        self.__registered_irqs = list ()
        self.__display_irqs = list ()
        self.__ignore_irqs = list ()
        self.__irq_handler = None
        self.__events = list ()

    def register_irqs (self, *irqs):
        """Reqister possible irqs that will controlled in tests."""

        for irq in irqs:
            irq.register_notify (self.__on_irq, irq)
            self.__registered_irqs.append (irq)

    def display_irqs (self, *irqs):
        """Reqister possible irqs that will controlled in tests."""

        for irq in irqs:
            self.__display_irqs.append (irq)

    def ignore_irqs (self, *irqs):
        """Ignore the given irqs. That means that they only will be displayed
           (if this is requested). But ignore irqs do not affect expectances."""

        for irq in irqs:
            self.__ignore_irqs.append (irq)

    def __on_irq (self, value, irq):
        """Called when irq occurs."""

        if self.__irq_handler != None:
            self.__irq_handler (value, irq)

    def expect_irqs_for_ms (self, ms, *irq_pairs):
        """Expect the following irq to happen for the given ms."""

        self.expect_irqs_for_us (ms * 1000, *irq_pairs)

    def expect_irqs_for_us (self, usecs, *irq_pairs):
        """Expect the following irq to happen for the given us."""

        self.expect_irqs_for_cycles (self.__avr.usec_to_cycles (usecs), *irq_pairs)

    def expect_irqs_for_cycles (self, cycles, *irq_pairs):
        """Expect the following irq to happen for the given us."""

        # Setup
        expectings = list (irq_pairs)
        problems = list()
        stop_on_first = False
        stop_when_all = False

        if StopOnFirst in expectings:
            expectings.remove (StopOnFirst)
            stop_on_first = True

        if StopWhenAll in expectings:
            expectings.remove (StopWhenAll)
            stop_when_all = True

        def irq_handler (value, irq):
            if not (irq in self.__registered_irqs):
                return

            if not (irq in self.__ignore_irqs):
                pair = (irq, value)
                self.__events.append ((self.__avr.cycle, pair))

            if irq in self.__display_irqs:
                self.__avr.info (str(irq) + " changed to " + str(value) + "\n")

        self.__irq_handler = irq_handler

        # Run
        end_cycle = self.__avr.cycle + cycles

        while self.__avr.cycle < end_cycle:
            # Run
            self.__avr.run_cycles ()

            # Handle events that occured during cycle
            stop = False
            for event in list(self.__events):
                (cycle, pair) = event

                if cycle > end_cycle:
                    break
                self.__events.remove (event)

                if pair in expectings:
                    expectings.remove (pair)

                    if stop_on_first:
                        stop = True

                    if stop_when_all and len(expectings) == 0:
                        stop = True
                else:
                    (irq, value) = pair
                    problems.append ("Unexpected " + str(irq) + " with value " + str(value))

            # Check current state
            self.failIf (len (problems) > 0, problems)

            if stop:
                return

        # Check if everything that we expected has occured
        for (irq, value) in expectings:
            problems.append ("Expected but not occured: " + str(irq) + " with value " + str(value))

        self.failIf (len (problems) > 0, problems)

    def debug (self):
        """Run AVR but show irqs if asked to."""

        def irq_handler (value, irq):
            if not (irq in self.__registered_irqs):
                return

            if irq in self.__display_irqs:
                self.__avr.info (str(irq) + " changed to " + str(value) + "\n")

        self.__irq_handler = irq_handler

        self.__avr.run ()

    def register_irq (self, irq, name = None, display = True, display_only = False):
        """Register and configure given irq."""

        self.register_irqs (irq)
        if display_only:
            display = True
            self.ignore_irqs (irq)

        if display: self.display_irqs (irq)

    def register_io_irq (self, ctl, index, name = None, display = True, display_only = False):
        """Get the specific irq for a module."""

        irq = self.__avr.get_io_irq (ctl, index, name)
        self.register_irq (irq, name, display, display_only)
        return irq

    def register_ioport_irq (self, letter, index, name = None, display = True, display_only = False):
        """Get IRQ of the given ioport (by letter like A, B, C...)."""

        irq = self.__avr.get_ioport_irq (letter, index, name)
        self.register_irq (irq, name, display, display_only)
        return irq

    def register_iomem_irq (self, register, index, name = None, display = True, display_only = False):
        """Get IRQ of for the given io memory register."""

        irq = self.__avr.get_iomem_irq (register, index, name)
        self.register_irq (irq, name, display, display_only)
        return irq

