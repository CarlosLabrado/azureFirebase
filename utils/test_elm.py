__author__ = 'root'

import time

from devices.omnimeter import Omnimeter

o = Omnimeter("ttyUSB1", "000000014035")

while True:
    print '+++++++++++++++++++++++++++++++++++++++++++++++++++'
    o.get_data()
    time.sleep(10)