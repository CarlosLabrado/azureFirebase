import minimalmodbus
import serial
import time

address = 169

instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address, minimalmodbus.MODE_RTU)
instrument.serial.baudrate = 19200
instrument.serial.bytesize = 8
instrument.serial.parity = serial.PARITY_NONE
instrument.serial.stopbits = 1.5
instrument.serial.timeout = 0.5

while True:
    try:
        year = instrument.read_register(1424)
        print year
        elapsed_time = instrument.read_register(2502, functioncode=4)
        minutes = int(elapsed_time / 256)
        sec = int(elapsed_time % 256)
        print "min = {0}".format(minutes)
        print "sec = {0}".format(sec)
    except ValueError as e:
        print "ValueError: {0}".format(e.message)
    except IOError as e:
        print "IOError: {0}".format(e.message)
    time.sleep(1)
