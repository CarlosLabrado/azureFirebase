import minimalmodbus
import serial
import time

instrument = minimalmodbus.Instrument('/dev/ttyUSB4', 1, minimalmodbus.MODE_RTU)


instrument.serial.baudrate = 19200
instrument.serial.bytesize = 8
instrument.serial.parity = serial.PARITY_NONE
instrument.serial.stopbits = 2
instrument.serial.timeout = 0.5

instrument.debug = True

# set speed S01:
instrument.write_register(functioncode=6, registeraddress=1793, value=5000)

# set run S06 set to 1:
instrument.write_register(functioncode=6, registeraddress=1798, value=1)

while True:
    try:
        print instrument.read_registers(registeraddress=2054, numberOfRegisters=1)
    except ValueError as e:
        print "ValueError: {0}".format(e.message)
    except IOError as e:
        print "IOError: {0}".format(e.message)
    time.sleep(1)
