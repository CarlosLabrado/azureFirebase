import minimalmodbus
import serial
import time

instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1, minimalmodbus.MODE_RTU)


instrument.serial.baudrate = 9600
instrument.serial.bytesize = 8
instrument.serial.parity = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 0.5


while True:
    try:
        # get Pressures
        pc = instrument.read_registers(0, 74)  # 40054
        print "Data: {0}".format(pc)
        # pl = instrument.read_register(54)  # 40055
        # pt = instrument.read_register(55)  # 40056
        #
        # # get cycles
        # cycles_completed = instrument.read_register(48)  # 40049 "Shut in well cycle"
        # cycles_missed = instrument.read_register(47)  # 40048 "Shut in count"
        #
        # # get status
        # status = instrument.read_register(3)
        #
        # # Read Words
        # fall_time_hr = instrument.read_register(22)
        # fall_time_min = instrument.read_register(23)
        # fall_time_sec = instrument.read_register(24)
        # shut_time_hr = instrument.read_register(19)
        # shut_time_min = instrument.read_register(20)
        # shut_time_sec = instrument.read_register(21)
        # on_time_hr = instrument.read_register(7)
        # on_time_min = instrument.read_register(8)
        # on_time_sec = instrument.read_register(9)
        # sales_time_hr = instrument.read_register(16)
        # sales_time_min = instrument.read_register(17)
        # sales_time_sec = instrument.read_register(18)
        # off_time_hr = instrument.read_register(13)
        # off_time_min = instrument.read_register(14)
        # off_time_sec = instrument.read_register(15)
        # b_time_hr = instrument.read_register(10)
        # b_time_min = instrument.read_register(11)
        # b_time_sec = instrument.read_register(12)
        #
        # # Current timer
        # curr_time_hr = instrument.read_register(4)
        # curr_time_min = instrument.read_register(5)
        # curr_time_sec = instrument.read_register(6)
        # curr_time_ = (curr_time_hr * 3600) + (curr_time_min * 60) + curr_time_sec
        #
        # fall_time_setting = (fall_time_hr * 3600) + (fall_time_min * 60) + fall_time_sec
        # shut_time_setting = (shut_time_hr * 3600) + (shut_time_min * 60) + shut_time_sec
        # on_time_setting = (on_time_hr * 3600) + (on_time_min * 60) + on_time_sec
        # sales_time_setting = (sales_time_hr * 3600) + (sales_time_min * 60) + sales_time_sec
        # off_time_setting = (off_time_hr * 3600) + (off_time_min * 60) + off_time_sec
        # b_time_setting = (b_time_hr * 3600) + (b_time_min * 60) + b_time_sec
        #
        # print "Current timer: {0}".format(curr_time_)
        # print "Current: PC = {0} .. PL = {1} .. PT = {2} .. Cycles Completed {3}" \
        #       " .. Cycles Missed {4} .. Status {5}"\
        #     .format(pc, pl, pt, cycles_completed, cycles_missed, status)
        # print "Settings: fall = {0} .. shut = {1} .. on = {2} .. sales = {3} .. off = {4} .. b = {5}"\
        #     .format(fall_time_setting,
        #             shut_time_setting,
        #             on_time_setting,
        #             sales_time_setting,
        #             off_time_setting,
        #             b_time_setting)
        #

    except ValueError as e:
        print "ValueError: {0}".format(e.message)
    except IOError as e:
        print "IOError: {0}".format(e.message)
    time.sleep(2)
