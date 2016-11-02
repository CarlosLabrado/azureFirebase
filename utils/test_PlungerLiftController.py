import minimalmodbus
import serial
import time

instrument = minimalmodbus.Instrument('/dev/ttyUSB4', 1, minimalmodbus.MODE_RTU)


instrument.serial.baudrate = 9600
instrument.serial.bytesize = 8
instrument.serial.parity = serial.PARITY_EVEN
instrument.serial.stopbits = 1
instrument.serial.timeout = 0.5

instrument.debug = True

current_cycle = ''

while True:
    try:
        # build date
        year = instrument.read_register(1)
        month = instrument.read_register(2)
        day = instrument.read_register(3)
        hour = instrument.read_register(5)
        minute = instrument.read_register(6)
        sec = instrument.read_register(7)

        # get Pressures
        pc = instrument.read_register(2492)                # $M492
        pt = instrument.read_register(2493)                # $M493
        pl = instrument.read_register(2494)                # $M494
        pd = instrument.read_register(2495)                # $M495

        # get cycles
        cycles_completed = instrument.read_register(2512)  # $M512
        cycles_missed = instrument.read_register(2513)     # $M513

        # get status
        status = instrument.read_register(2497)       # $M497
    except ValueError as e:
        print "ValueError: {0}".format(e.message)
    except IOError as e:
        print "IOError: {0}".format(e.message)
    time.sleep(2)
