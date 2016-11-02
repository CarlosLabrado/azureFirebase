import config
import json
import time
import datetime
import calendar
import serial
import bitState
import minimalmodbus
import threading
from iothub_client import *
from collections import deque
import cycle

"""
Handles the serial communications to Lufkin POC via modbus.
"""
__author__ = 'Cesar'


class ModbusLufkin:

    current = {"id": config.device_id,      # Device Id
               "a": 0,                      # Automatic
               "e": 0,                      # Efficiency
               "nl": 0,                     # No Load
               "np": 0,                     # No Position
               "pf": 0,                     # Percent Fillage
               "ns": 0,                     # Seconds to Next Start
               "lc": 0,                     # Strokes last cycle
               "tc": 0,                     # Strokes this cycle
               "ws": 0,                     # Well Status
               "t": 0
               }

    settings = {"id": config.device_id,     # Device Id
                "c": 0,                     # Clock
                "fs": 0,                    # Fillage setting
                "pu": 0,                    # Pump Up Strokes
                "po": 0,                    # Pump Off Strokes
                "to": 0,                    # Time Out
                "at": 0,                    # Auto Time Out
                "fv": 0,                    # Firmware Version
                "t": 1
                }

    dyna = {"id": config.device_id,         # Device Id
            "p": [(0, 0)],                  # (Position, Load) Point Array
            "t": 2
            }

    downhole = {"id": config.device_id,     # Device Id
                "p": [(0, 0)],              # (Position, Load) Point Array
                "t": 3
                }

    error = {"n": 0,
             "m": 0,
             "t": 4
             }

    # Find message type 5 in cycle.py

    # FIFO of 100 cycles
    cycles = deque(maxlen=100)

    receive_context = 0
    usb_number = 0

    instrument = None

    modbus_lock = threading.Lock()
    all_reg = None

    strokes_this_cycle = 0
    well_status_old = 0

    def __receive_message_callback(self, message, counter):
        """
        Callback function for Rx messages
        """
        b = message.get_bytearray()
        size = len(b)
        config.logging.warning('Lufkin: __receive_message_callback - Message Received: \n'
                               '    Data: [{0}]'.format(b[:size].decode('utf-8')))

        exe = threading.Thread(target=self._execute_commands,
                               args=[b[:size].decode('utf-8')])
        exe.daemon = True
        exe.start()

        return IoTHubMessageDispositionResult.ACCEPTED

    def __send_confirmation_callback(self, message, result, user_contex):
        """
        Confirmation callback function for Tx messages
        """
        config.logging.debug('Lufkin: __send_confirmation_callback - Confirmation Received: \n'
                             '    Result: [{0}]'.format(result))

    def __init__(self, address=1):
        """
        Generates a new controller and it's azure client.
        :param address: Modbus slave address (default = 1)
        :return: ModbusLufkin object
        """
        config.logging.debug('Lufkin: __init__ - Initializing Lufkin')
        # Init Azure client
        self.__iot_hub_client_init()

        # Init modbus instrument
        self.__init_instrument(address)

    def __iot_hub_client_init(self):
        """
        Generates a new Azure IoT Client.
            :return:
        """
        # prepare iothub client
        self.iotHubClient = IoTHubClient(config.connection_string, IoTHubTransportProvider.MQTT)
        # set the time until a message times out
        self.iotHubClient.set_option("messageTimeout", 10000)
        self.iotHubClient.set_option("logtrace", config.azure_iot_logs)
        self.iotHubClient.set_message_callback(self.__receive_message_callback, self.receive_context)

    def __init_instrument(self, address=1):
        """
        Generates a new Lufkin instrument, searches for it in all USB ports.
        :param address: Lufkin slave address (default = 1)
        :return:
        """
        while self.usb_number < 5:
            try:
                self.address = address
                tty = '/dev/ttyUSB{0}'.format(self.usb_number)
                config.logging.info('Lufkin: __init_instrument - Initializing Port: {0} USB-Serial'
                                    .format(tty))
                # Create Modbus Instrument 
                self.instrument = minimalmodbus.Instrument('{0}'.format(tty), address, minimalmodbus.MODE_RTU)
                self.instrument.serial.baudrate = 19200
                self.instrument.serial.bytesize = 8
                self.instrument.serial.parity = serial.PARITY_NONE
                self.instrument.serial.stopbits = 1.5
                self.instrument.serial.timeout = 0.5

            except Exception as e:
                self.usb_number += 1
                config.logging.error('Lufkin: Trying different USB, Lufkin test failed with error: {0}'
                                     .format(e.message))
                config.logging.debug("Lufkin: Publishing Unhandled exception data to Azure: {0}"
                                     .format(e.message))
                # publish error to azure
                self.error["n"] = 1
                self.error["m"] = "Trying different USB, Lufkin test failed with error: {0}".format(e.message)
                self.iotHubClient.send_event_async(IoTHubMessage(json.dumps(self.error)),
                                                   self.__send_confirmation_callback, 1)
                time.sleep(3)
            else:
                config.logging.info('Lufkin: __init_instrument - Initialization successful @ {0}'
                                    .format(tty))
                return
        config.logging.error('Lufkin: Could not initialize in the first 4 USBs =( .. Dying')
        while True:
            # Wait for death!
            a = 0

    def _send_to_azure(self, to_send):
        """
        Sends data to current Azure IoT client.
        :param to_send: Dictionary to send
        :return:
        """
        try:
            json_to_send = json.dumps(to_send)
            self.iotHubClient.send_event_async(IoTHubMessage(json_to_send),
                                               self.__send_confirmation_callback, 1)
        except Exception as e:
            config.logging.warning('ModbusLufkin: _send_to_azure - Error sending: [{0}]'.format(e.message))
            config.logging.warning('ModbusLufkin: _send_to_azure - Reinitializing Azure IoT Client')

    def get_current_data(self):
        """
        Gets the main readings from Lufkin
        :return: fill object attributes
        """
        with self.modbus_lock:
            try:
                # Assume everything is alright
                self.current["nl"] = 0
                self.current["np"] = 0
                self.current["po"] = 0

                # Current      ==============================================================

                # Operation mode
                # 0 Normal Mode
                # 1 Timed Mode
                # 2 Host Mode
                self.current["a"] = self.instrument.read_register(2195)

                # calculate seconds in current state
                elapsed_minutes_seconds_hex = self.instrument.read_register(2502, functioncode=4)
                elapsed_minutes = elapsed_minutes_seconds_hex / 256
                elapsed_seconds = elapsed_minutes_seconds_hex % 256

                elapsed_hours = self.instrument.read_register(2501, functioncode=4)
                seconds_in_current_state = elapsed_hours * 3600 + elapsed_minutes * 60 + elapsed_seconds

                # get well status
                well_status = self.instrument.read_register(2500, functioncode=4)
                if well_status == 12:
                    # no load
                    self.current["nl"] = 1
                elif well_status == 13:
                    # no position
                    self.current["np"] = 1
                elif well_status == 31:
                    # pump off
                    self.current["po"] = 1

                stroke_period_sec = self.instrument.read_register(2505, functioncode=4) / 100

                # well status OFF
                if well_status > 30:
                    self.current["ws"] = 0
                    time_on_hours = self.instrument.read_register(2205)
                    time_on_minutes = self.instrument.read_register(2206)
                    time_on_seconds = time_on_hours * 3600 + time_on_minutes * 60
                    time_to_next_start = time_on_seconds - seconds_in_current_state
                    self.current["ns"] = time_to_next_start

                # well status ON
                else:
                    self.current["ns"] = seconds_in_current_state
                    self.current["po"] = 0
                    self.current["ws"] = 1

                # Cycle      ==============================================================
                # change in well_status?
                if well_status != self.well_status_old:

                    # Well Stopped?
                    if well_status > 30:
                        if self.well_status_old < 30:
                            config.logging.warning("ModbusLufkin: --------- Well Stopped ---------")
                            try:
                                # position 0 always have the most resent cycle (appendleft)
                                self.cycles[0].well_stopped()
                            except IndexError:
                                config.logging.warning("No Cycles in yet!")

                    # Well Started?
                    elif well_status < 30:
                        if self.well_status_old > 30:
                            config.logging.warning("ModbusLufkin: --------- Well Started ---------")
                            try:
                                self.cycles[0].cycle_ended()
                                self._send_to_azure(self.cycles[0].get_dictionary_to_send())
                            except IndexError:
                                config.logging.warning("No Cycles in yet!")
                            # new cycle starts!
                            new_cycle = cycle.Cycle(config.device_id)
                            # append left ensures that position 0 always have the most resent cycle
                            self.cycles.appendleft(new_cycle)

                self.well_status_old = well_status

                # percent fillage
                self.current["pf"] = self.instrument.read_register(2613, functioncode=4) / 100

                # Send to Azure
                self._send_to_azure(self.current)

                # Settings      ==============================================================
                # clock in seconds
                year = self.instrument.read_register(1424)
                month = self.instrument.read_register(1425)
                day = self.instrument.read_register(1426)
                hour = self.instrument.read_register(1427)
                minute = self.instrument.read_register(1428)
                second = self.instrument.read_register(1429)

                current_clock = datetime.datetime(year=year, month=month, day=day,
                                                  hour=hour, minute=minute, second=second)
                time_tuple = datetime.datetime.timetuple(current_clock)
                clock_in_seconds = calendar.timegm(time_tuple)
                self.settings["c"] = clock_in_seconds

                # fillage settings
                self.settings["fs"] = self.instrument.read_float(2263)

                self.settings["pu"] = self.instrument.read_register(2203)
                self.settings["po"] = self.instrument.read_register(2242)
                self.settings["to"] = self.instrument.read_register(2205) * 3600 + \
                                      self.instrument.read_register(2206) * 60

                # TODO: this setting is internal to the RPi
                # self.settings["at"] =

                self.settings["fv"] = self.instrument.read_register(0, functioncode=4) % 256

                self._send_to_azure(self.settings)

                # Dyna
                self._get_dynagraph()

                self._send_to_azure(self.dyna)
                # Downhole
                self._get_downhole()

                self._send_to_azure(self.downhole)

            except Exception as e:
                config.logging.error('Lufkin Send error: {0}'.format(e.message))
                if self.modbus_lock.locked():
                    self.modbus_lock.release()

    def _get_dynagraph(self):
        """
        Gets the surface card
        :return:
        """
        try:
            # Write register 109 to load last stroke into Single Card Buffer (Sam Modbus Map, page 11)
            self.instrument.write_bit(9, 1, functioncode=5)
            # Read dyna, max block size 125
            position_load = self.instrument.read_registers(5755, 125, functioncode=4)
            position_load += self.instrument.read_registers(5755+125, 125, functioncode=4)
            position_load += self.instrument.read_registers(5755+250, 125, functioncode=4)
            position_load += self.instrument.read_registers(5755+375, 25, functioncode=4)

            dyna = []
            for i, pos in enumerate(position_load):
                if i % 2:
                    pass
                else:
                    try:
                        load = position_load[i+1]
                        point = (pos, load)
                        dyna.append(point)
                    except Exception as e:
                        config.logging.error('ModbusLufkin: _get_dynagraph - Fail @ Point ({0},{1})'.format(pos, load))
                        config.logging.error('ModbusLufkin: _get_dynagraph - Fail @ Message {0}'.format(e.message))
                        break

        except Exception as e:
            config.logging.error('Lufkin Dyna error: {0}'.format(e.message))
        else:
            config.logging.debug('ModbusLufkin: _get_dynagraph - Dyna: [{0}]'.format(dyna))
            self.dyna["p"] = dyna

    def _get_downhole(self):
        """
        Gets the downhole card
        :return:
        """
        try:
            # Write register 109 to load last stroke into Single Card Buffer (Sam Modbus Map, page 11)
            self.instrument.write_bit(108, 1, functioncode=5)
            # Read downhole, max block size 125
            position_load = self.instrument.read_registers(6164, 125, functioncode=4)
            position_load += self.instrument.read_registers(6164+125, 75, functioncode=4)

            downhole = []
            for i, pos in enumerate(position_load):
                if i % 2:
                    pass
                else:
                    try:
                        load = position_load[i+1]
                        point = (pos, load)
                        downhole.append(point)
                    except Exception as e:
                        config.logging.error('ModbusLufkin: _get_downhole - Fail @ Point ({0},{1})'.format(pos, load))
                        config.logging.error('ModbusLufkin: _get_downhole - Fail @ Message {0}'.format(e.message))
                        break

        except Exception as e:
            config.logging.error('Lufkin Dyna error: {0}'.format(e.message))
        else:
            config.logging.debug('ModbusLufkin: _get_downhole - Downhole: [{0}]'.format(downhole))
            self.downhole["p"] = downhole

    def _execute_commands(self, payload):
        """
        Execute commands received from Azure IoT
        """
        # Got a command to send to modbus device [variable_name]=[value]
        data = payload.split('=')
        variable_name = data[0]
        try:
            value = int(data[1])
        except ValueError:
            value = data[1]

        config.logging.warning("ModbusLufkin: Modbus Lock = {0}".format(self.modbus_lock.locked))
        with self.modbus_lock:
            config.logging.warning("ModbusLufkin: Command = {0}, Data = {1}".format(variable_name, value))
            try:
                if variable_name == 'pu':
                    config.logging.warning("ModbusLufkin: Pump Up = {0}".format(value))
                    memory_address = 2203
                    data_to_write = int(value)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)
                elif variable_name == 'po':
                    config.logging.warning("ModbusLufkin: Pump Off = {0}".format(value))
                    memory_address = 2242
                    data_to_write = int(value)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)
                elif variable_name == 'c':
                    config.logging.warning("ModbusLufkin: Lufkin Clock = {0}".format(value))

                    # Convert Epoch to:
                    year = int(time.strftime('%Y', time.localtime(value)))
                    memory_address = 1424
                    data_to_write = int(year)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)

                    month = int(time.strftime('%m', time.localtime(value)))
                    memory_address = 1425
                    data_to_write = int(month)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)

                    day = int(time.strftime('%d', time.localtime(value)))
                    memory_address = 1426
                    data_to_write = int(day)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)
                    hour = int(time.strftime('%H', time.localtime(value)))
                    memory_address = 1427
                    data_to_write = int(hour)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)

                    minute = int(time.strftime('%M', time.localtime(value)))
                    memory_address = 1428
                    data_to_write = int(minute)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)

                    second = int(time.strftime('%S', time.localtime(value)))
                    memory_address = 1429
                    data_to_write = int(second)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)

                elif variable_name == 'fs':
                    config.logging.warning("ModbusLufkin: Fillage Setting = {0}".format(value))
                    memory_address = 2263
                    data_to_write = float(value)
                    self.instrument.write_float(registeraddress=memory_address,
                                                value=data_to_write)

                elif variable_name == 'at':
                    config.logging.warning("ModbusLufkin: Automatic Time Out = {0}".format(value))
                    # TODO: this setting is internal to the RPi

                elif variable_name == 'to':
                    config.logging.warning("ModbusLufkin: Time Out = {0}".format(value))
                    # Hours
                    hours = int(value / 3600)
                    memory_address = 2205
                    data_to_write = int(hours)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)
                    # Minutes
                    minutes = int(value % 3600)/60
                    memory_address = 2206
                    data_to_write = int(minutes)
                    self.instrument.write_register(registeraddress=memory_address,
                                                   value=data_to_write,
                                                   functioncode=6)
                else:
                    config.logging.warning("ModbusLufkin: Execute Commands: Command unknown")

            except Exception as e:
                config.logging.error("ModbusLufkin: Writing Settings: {0}".format(e.message))
                if self.modbus_lock.locked():
                    self.modbus_lock.release()

    def polling_loop(self, rate):
        """
        Daemon to update ModbusLufkin data. Each data gathering method is responsible of publishing its
        data.
        :param rate: Amount of seconds between polling
        """
        config.logging.warning("ModbusLufkin: polling_loop Thread Running ...")
        seconds = 0
        while True:
            try:
                if seconds < rate:
                    time.sleep(1)
                    seconds += 1
                else:
                    seconds = 0
                    self.get_current_data()
            except Exception as e:
                config.logging.warning("ModbusLufkin: polling_loop (Unknown, don't die!): {0}".format(e.message))
