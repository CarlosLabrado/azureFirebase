import serial

port = serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=1)
port.bytesize = 8
port.parity = serial.PARITY_NONE
port.stopbits = 1

address = '01'
command = 'S?1'

port.write("00S?1\x0D\x0A")

rx = port.readline()
if rx == '':
    print "Timeout"
elif rx[3] == command[0]:
    to_return = rx[:-1]
    print ('Petrolog: __send_get_command - Success Rx: {0}'.format(to_return))
