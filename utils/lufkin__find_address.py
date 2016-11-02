import minimalmodbus
minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL
import serial
import time


address = 1

while True:

    instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address, minimalmodbus.MODE_RTU)
    instrument.serial.baudrate = 19200
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 1.5
    instrument.serial.timeout = 0.5

    try:
        year = instrument.read_register(1424)
    except ValueError as e:
        print "ValueError: {0}".format(e.message)
        break
    except IOError as e:
        print "IOError: {0}".format(e.message)
        address += 1
    else:
        print "Address Found!!  = {0}".format(address)
        break
