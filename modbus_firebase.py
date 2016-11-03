import config
import json
import time
import random
import minimalmodbus
import serial
import threading
import iothub_client
from iothub_client import *

"""
Implements serial communication and MQTT Client for Pacemaker Plunger Lift Controller
First Deployment: Trevor - Trinity River (Aug 2016)
"""

__author__ = 'Cesar'


class ModbusFirebase:

    instrument = None
    address = None
    usb_number = 0

    all_reg = None

    current_cycle = {"id": config.device_id,
                     "pc": 0,
                     "pt": 0,
                     "pl": 0,
                     "cc": 0,
                     "cm": 0,
                     "s": 0,
                     "csc": 0,
                     "at": 0,                # Average Travel Time
                     "t": 0,
                     "fb": 0
                     }

    history_cycle = {"id": config.device_id,
                     "off": {"pc": 0,
                             "pt": 0,
                             "pl": 0
                             },
                     "sales": {"pc": 0,
                               "pt": 0,
                               "pl": 0
                               },
                     "t": 1
                     }

    settings = {"id": config.device_id,
                "sh": 0,
                "on": 0,
                "sa": 0,
                "of": 0,
                "b": 0,
                "t": 2
                }

    error = {"id": config.device_id,
             "n": "",
             "m": "",
             "t": 3
             }

    error_counter = 0
    receive_context = 0
    status = None
    old_status = None
    modbus_lock = threading.Lock()
    live_data = False
    live_countdown = 60

    iotHubClient = None

    def __receive_message_callback(self, message, counter):
        """
        Callback function for Rx messages
        """
        b = message.get_bytearray()
        size = len(b)
        config.logging.warning('FirebaseTest: __receive_message_callback - Message Received: \n'
                               '    Data: [{0}]'.format(b[:size].decode('utf-8')))
        self._execute_commands(b[:size].decode('utf-8'))
        return IoTHubMessageDispositionResult.ACCEPTED

    def __send_confirmation_callback(self, message, result, user_contex):
        """
        Confirmation callback function for Tx messages
        """
        config.logging.debug('FirebaseTest: __send_confirmation_callback - Confirmation Received: \n'
                             '    Result: [{0}]'.format(result))

    def __init__(self, address=1):
        """
        Generates a new controller and it's azure client.
        :param address: Modbus slave address (default = 1)
        :return: FirebaseTest object
        """
        config.logging.debug('FirebaseTest: __init__ - Initializing FirebaseTest with address: {0}'
                             .format(address))
        # Init Azure client
        self.__iot_hub_client_init()

        # Init modbus instrument
        # self.__init_instrument(address)

    def __iot_hub_client_init(self):
        """
        Generates a new Azure IoT Client.
        :param address: Modbus slave address (default = 1)
        :return:
        """
        # prepare iothub client
        self.iotHubClient = IoTHubClient(config.connection_string, IoTHubTransportProvider.MQTT)
        # set the time until a message times out
        self.iotHubClient.set_option("messageTimeout", 10000)
        self.iotHubClient.set_option("logtrace", int(config.azure_iot_logs))
        self.iotHubClient.set_message_callback(self.__receive_message_callback, self.receive_context)

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
            config.logging.warning('FirebaseTest: _send_to_azure - Error sending: [{0}]'.format(e.message))

    # def __init_instrument(self, address=1):
    #     """
    #     Generates a new modbus instrument, searches for it in all USB ports.
    #     :param address: Modbus slave address (default = 1)
    #     :return:
    #     """
    #     while self.usb_number < 5:
    #         try:
    #             self.address = address
    #
    #             if True:
    #                 tty = '/dev/ttyUSB{0}'.format(self.usb_number)
    #                 config.logging.info('FirebaseTest: __init_instrument - Initializing: {0} USB-Serial'
    #                                     .format(tty))
    #             else:
    #                 tty = '/dev/{0}'.format(config.tty)
    #
    #             # Create Modbus Instrument (Defaults for Pacemaker: Pacemaker Controller Manual V460)
    #             self.instrument = minimalmodbus.Instrument('{0}'.format(tty), address, minimalmodbus.MODE_RTU)
    #             self.instrument.serial.baudrate = 9600
    #             self.instrument.serial.bytesize = 8
    #             self.instrument.serial.parity = serial.PARITY_NONE
    #             self.instrument.serial.stopbits = 1
    #             self.instrument.serial.timeout = 0.5
    #
    #         except Exception as e:
    #             self.usb_number += 1
    #             config.logging.error('FirebaseTest: Trying different USB Modbus test failed with error: {0}'
    #                                  .format(e.message))
    #             config.logging.debug("FirebaseTest: Publishing Unhandled exception data to Azure: {0}"
    #                                  .format(e.message))
    #             # publish error to azure
    #             self.error["n"] = 1
    #             self.error["m"] = "Trying different USB Modbus test failed with error: {0}".format(e.message)
    #             self._send_to_azure(self.error)
    #             time.sleep(3)
    #         else:
    #             config.logging.info('FirebaseTest: __init_instrument - Initialization successful @ {0}'
    #                                 .format(tty))
    #             return
    #     config.logging.error('FirebaseTest: Could not initialize in the first 4 USBs .. Dying')
    #     while True:
    #         # Wait for death!
    #         a = 0

    # def _cycle_completed(self):
    #     """
    #     Determine if a cycle completed
    #     :return: True / False
    #     """
    #     if self.old_status == 2:         # Sales Time
    #         if self.status == 1:         # Off Time
    #             return True
    #     return False

    def _get_pressure(self, plplates_input):
        """
        Gets tubing pressure from PiPlates
        :param piplates_input: Analog input
        :return: Pressure in psi
        """
        # volts = DAQC.getADC(0, plplates_input)
        # if plplates_input == 0:
        #     pressure = (750.0 * (volts - 1)) * config.pressure_factor_0
        #     print ('AI0 = [{0}] Volts -> Tubing Pressure = [{1}] PSI'.format(volts, pressure))
        # elif plplates_input == 1:
        #     pressure = (750.0 * (volts - 1)) * config.pressure_factor_1
        #     print ('AI1 = [{0}] Volts -> Casing Pressure = [{1}] PSI'.format(volts, pressure))
        # else:
        #     pressure = (750.0 * (volts - 1))
        # return pressure

    def _get_pacemaker_data(self):
        """
        Gets Pacemaker modbus data. Fills all_reg
        :return:
        """
        while True:
            with self.modbus_lock:
                try:
                    self.all_reg = self.instrument.read_registers(0, 74)  # Tries to get all the registries at once
                except Exception as e:
                    config.logging.warning('FirebaseTest: Error getting data from device: [{0}] - Retrying in 10 sec'
                                           .format(e.message))
                    time.sleep(10)
                else:
                    # Read register successful!!
                    return

    def _get_current_status_counter(self):
        """
        Gets Current Status Counter
        :return:
        """
        # get current status timers
        current_hr = self.all_reg[4]
        current_min = self.all_reg[5]
        current_sec = self.all_reg[6]
        current_status_counter = (current_hr * 3600) + (current_min * 60) + current_sec

        return current_status_counter

    def _get_minimal_travel_time(self):
        """
        Gets the minimum historical travel time
        :return:
        """
        # get current status timers
        min_min = self.all_reg[32]
        min_sec = self.all_reg[33]
        minimal_travel_time = (min_min * 60) + min_sec

        return minimal_travel_time

    def _get_state(self):
        """
        Gets well state
        :return:
        """
        well_state = self.all_reg[3]
        return well_state

    def _get_open_time(self):
        """
        Gets total open time setting
        :return:
        """
        open_hr = self.all_reg[4]
        open_min = self.all_reg[5]
        open_sec = self.all_reg[6]
        open_time = (open_hr * 3600) + (open_min * 60) + open_sec

        return open_time

    def get_current_data(self):
        """
        Gets the main readings from FirebaseTest
        :return: fill object attributes
        """
        if self.error_counter > 30:
            # Reset to try to recover
            config.logging.critical("FirebaseTest: > 30 consecutive modbus errors "
                                    "- Reset to try to recover")
            # publish error to azure
            self.error["n"] = 1
            self.error["m"] = "FirebaseTest: > 30 consecutive modbus errors - Reset to try to recover"
            self._send_to_azure(self.error)
            while True:
                # Wait for watchdog kill
                a = 0

        config.logging.debug("FirebaseTest: Getting Current: Starting ... Error Counter = {0}"
                             .format(self.error_counter))

        try:
            # get Pressures (Tubing and Casing. Line to be reported from Total Flow)
            pc = self._get_pressure(1)
            pt = self._get_pressure(0)

            # get cycles
            cycles_completed = self.all_reg[48]    # 40049 "Shut in well cycle"
            cycles_missed = self.all_reg[47]       # 40048 "Shut in count"

            # get status
            self.old_status = self.status
            self.status = self.all_reg[3]          # 40004

            # get average travel time
            average_travel_time_sec = self.all_reg[32]
            average_travel_time_min = self.all_reg[33]
            average_travel_time = (average_travel_time_min * 60) + average_travel_time_sec

            # determine if state changed to Sales (2) or Off (1)
            if self.status != self.old_status:
                if self.status == 2:
                    # store pressures for sales history
                    self.history_cycle["sales"]["pc"] = pc
                    self.history_cycle["sales"]["pt"] = pt
                elif self.status == 1:
                    # store pressures for off history
                    self.history_cycle["off"]["pc"] = pc
                    self.history_cycle["off"]["pt"] = pt

            if self._cycle_completed():
                try:
                    # Cycle ended. Save history to backend
                    config.logging.info("FirebaseTest: Started saving cycle")
                    config.logging.debug("FirebaseTest: History: \n{0}"
                                         .format(json.dumps(self.history_cycle, indent=4)))
                    # publish history to azure
                    self._send_to_azure(self.history_cycle)
                except Exception as e:
                    config.logging.error("FirebaseTest: Error in saving history {0}".format(e.message))

            self.current_cycle["pc"] = pc
            self.current_cycle["pt"] = pt

            self.current_cycle["cc"] = cycles_completed
            self.current_cycle["cm"] = cycles_missed

            self.current_cycle["s"] = self.status

            self.current_cycle["csc"] = self._get_current_status_counter()
            self.current_cycle["at"] = average_travel_time

            config.logging.debug('FirebaseTest: Current Cycle: \n{0}'
                                 .format(json.dumps(self.current_cycle, indent=4)))

            # publish current cycle to azure
            self._send_to_azure(self.current_cycle)

        except IOError as e:
            config.logging.error('Error reading modbus device: {0}'.format(e.message))
            if '[Errno 5]' in e.message:
                error = True
                while error:
                    try:
                        # USB changed tty?
                        config.logging.warning('Recover from error - Reinitializing Instrument in 10 sec')
                        time.sleep(10)
                        self.__init_instrument(self.address)
                    except Exception as e:
                        config.logging.error('Failed to recover - {0}'.format(e.message))
                        # publish error to azure
                        self.error["n"] = 1
                        self.error["m"] = "Failed to recover from initialization error: {0}".format(e.message)
                        self._send_to_azure(self.error)
                    else:
                        error = False
        except ValueError as e:
            config.logging.error('Error reading modbus device (ValueError): {0}'.format(e.message))
            config.logging.debug("Publishing Error data to MQTT Broker: {0}".format(e.message))
            # publish error to azure
            self.error["n"] = 1
            self.error["m"] = "Error reading modbus device (ValueError): {0}".format(e.message)
            self._send_to_azure(self.error)
            self.error_counter += 1
        except Exception as e:
            config.logging.error('Unhandled exception in get_current_date: {0}'.format(e.message))
            config.logging.debug("Publishing Unhandled exception in get_current_date to MQTT Broker: {0}"
                                 .format(e.message))
            # publish error to azure
            self.error["n"] = 1
            self.error["m"] = "Unhandled exception in get_current_date: {0}".format(e.message)
            self._send_to_azure(self.error)
            self.error_counter += 1
        else:
            config.logging.debug("FirebaseTest: Getting Current: End without error")
            self.error_counter = 0

        finally:
            if self.modbus_lock.locked():
                self.modbus_lock.release()

    def get_settings(self):
        """
        Gets the settings from FirebaseTest
        :return: fill object attributes
        """
        config.logging.debug("FirebaseTest: Getting Settings: Starting ...")
        try:

            # Read Words
            fall_time_hr = self.all_reg[22]      # Plunger Fall Time Hour
            fall_time_min = self.all_reg[23]     # Plunger Fall Time Minute
            fall_time_sec = self.all_reg[24]     # Plunger Fall Time Second
            shut_time_hr = self.all_reg[19]      # Shut-in Time Hour
            shut_time_min = self.all_reg[20]     # Shut-in Time Minute
            shut_time_sec = self.all_reg[21]     # Shut-in Time Second
            on_time_hr = self.all_reg[7]         # On Time Hour
            on_time_min = self.all_reg[8]        # On Time Minute
            on_time_sec = self.all_reg[9]        # On Time Second
            sales_time_hr = self.all_reg[16]     # Sale Time Hour
            sales_time_min = self.all_reg[17]    # Sale Time Minute
            sales_time_sec = self.all_reg[18]    # Sale Time Second
            off_time_hr = self.all_reg[13]       # Off Time Hour
            off_time_min = self.all_reg[14]      # Off Time Minute
            off_time_sec = self.all_reg[15]      # Off Time Second
            b_time_hr = self.all_reg[10]         # B On Time Hour
            b_time_min = self.all_reg[11]        # B On Time Minute
            b_time_sec = self.all_reg[12]        # B On Time Second

            # convert all times to seconds (settings)

            fall_time_setting = (fall_time_hr * 3600) + (fall_time_min * 60) + fall_time_sec
            shut_time_setting = (shut_time_hr * 3600) + (shut_time_min * 60) + shut_time_sec
            on_time_setting = (on_time_hr * 3600) + (on_time_min * 60) + on_time_sec
            sales_time_setting = (sales_time_hr * 3600) + (sales_time_min * 60) + sales_time_sec
            off_time_setting = (off_time_hr * 3600) + (off_time_min * 60) + off_time_sec
            b_time_setting = (b_time_hr * 3600) + (b_time_min * 60) + b_time_sec

            self.settings["fa"] = fall_time_setting
            self.settings["sh"] = shut_time_setting
            self.settings["on"] = on_time_setting
            self.settings["sa"] = sales_time_setting
            self.settings["of"] = off_time_setting
            self.settings["b"] = b_time_setting

            config.logging.debug('FirebaseTest: Settings: \n{0}'
                                 .format(json.dumps(self.settings, indent=4)))
            # publish settings to azure
            self._send_to_azure(self.settings)

        except IOError as e:
            config.logging.error('Error reading modbus device: {0}'.format(e.message))
            if '[Errno 5]' in e.message:
                error = True
                while error:
                    try:
                        # USB changed tty?
                        config.logging.warning('Recover from error - Reinitializing Instrument in 10 sec')
                        time.sleep(10)
                        self.__init_instrument(self.address)
                    except Exception as e:
                        config.logging.error('Failed to recover - {0}'.format(e.message))
                        # publish error to azure
                        self.error["n"] = 1
                        self.error["m"] = "Failed to recover error reading modbus device: {0}".format(e.message)
                        self._send_to_azure(self.error)
                    else:
                        error = False
        except ValueError as e:
            config.logging.error('Error reading modbus device (ValueError): {0}'.format(e.message))
            config.logging.debug("Publishing Error data to MQTT Broker: {0}".format(e.message))
            self.error_counter += 1
            # publish error to azure
            self.error["n"] = 1
            self.error["m"] = "Error reading modbus device (ValueError): {0}".format(e.message)
            self._send_to_azure(self.error)
        except Exception as e:
            config.logging.error('Unhandled exception in get_settings: {0}'.format(e.message))
            config.logging.debug("Publishing Unhandled exception in get_settings to MQTT Broker: {0}".format(e.message))
            self.error_counter += 1
            # publish error to azure
            self.error["n"] = 1
            self.error["m"] = "Unhandled exception in get_current_date: {0}".format(e.message)
            self._send_to_azure(self.error)
        else:
            config.logging.debug("FirebaseTest: Getting Settings: End without error")
            self.error_counter = 0

        finally:
            if self.modbus_lock.locked():
                self.modbus_lock.release()

    def polling_loop(self, rate):
        """
        Daemon to update FirebaseTest data. Each data gathering method is responsible of publishing its
        data.
        :param rate: Amount of seconds between polling
        """
        config.logging.info("Firebase Test: polling_loop Thread Running ...")

        normal_rate = rate  # save initial rate

        seconds = 0

        seconds = 0
        while True:
            if self.live_data:
                self.live_countdown -= 1
                time.sleep(1)
                if self.live_countdown == 0:
                    config.logging.warning("Firebase Test: stopping live data! ")
                    self.live_data = False
                rate = 1
            else:
                rate = normal_rate
            try:
                if seconds < rate:
                    time.sleep(1)
                    seconds += 1
                else:
                    seconds = 0
                    self.get_test_data()
            except IoTHubError as e:
                config.logging.warning('Firebase Test: polling_loop: IoT Hub Error- {0}'.format(e.message))
            except Exception as e:
                config.logging.warning("Firebase Test: polling_loop (Unknown, don't die!): {0}".format(e.message))

    def get_test_data(self):

        self.current_cycle["pc"] = random.randint(1,11)*50
        self.current_cycle["pt"] = random.randint(1,11)*50
        self.current_cycle["pl"] = random.randint(1,11)*50


        self.current_cycle["cc"] = 1
        self.current_cycle["cm"] = 0

        self.current_cycle["s"] = 1

        self.current_cycle["csc"] = 1
        self.current_cycle["at"] = 0

        if self.live_data:
            self.current_cycle["fb"] = 1
        else :
            self.current_cycle["fb"] = 0

        config.logging.debug('FirebaseTest: Current Cycle: \n{0}'
                             .format(json.dumps(self.current_cycle, indent=4)))

        # publish current cycle to azure
        self._send_to_azure(self.current_cycle)

    def liveDataInitiateCounter(self, timer):
        """
        Initializes a countdown counter of 60 seconds, this will be the time the live data will be active
        meaning a 1 second polling rate
        :return:
        """
        while True:
            self.live_countdown -= 1
            time.sleep(1)
            if self.live_countdown == 0:
                config.logging.warning("Firebase Test: stopping live data! ")
                self.live_data = False
                break

    def _execute_commands(self, command):
        """
        Execute commands Rx from Azure IoT Client
        :param command:
        :return:
        """
        try:
            # Got a command to send to modbus device [variable_name]=[value]
            data = command.split('=')
            variable_name = data[0]
            try:
                value = int(data[1])
            except ValueError as e:
                config.logging.error('FirebaseTest: ValueError executing command!! - {0}'.format(e.message))

            with self.modbus_lock:
                if variable_name == 'fa':
                    error = True
                    while error:
                        try:
                            config.logging.warning("FirebaseTest: New Fall Time = {0}".format(value))
                            # Hours
                            memory_address = 22
                            data_to_write = int(value / 3600)
                            minutes = int(value % 3600)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Minutes
                            memory_address = 23
                            data_to_write = int(minutes / 60)
                            seconds = int(value % 60)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Seconds
                            memory_address = 24
                            data_to_write = seconds
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                        except IOError as e:
                            config.logging.warning("FirebaseTest: No response from instrument")
                        else:
                            error = False

                elif variable_name == 'sh':
                    error = True
                    while error:
                        try:
                            config.logging.warning("FirebaseTest: New Shut-in Time= {0}".format(value))
                            # Hours
                            memory_address = 19
                            data_to_write = int(value / 3600)
                            minutes = int(value % 3600)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Minutes
                            memory_address = 20
                            data_to_write = int(minutes / 60)
                            seconds = int(value % 60)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Seconds
                            memory_address = 21
                            data_to_write = seconds
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                        except IOError as e:
                            config.logging.warning("FirebaseTest: No response from instrument")
                        else:
                            error = False

                elif variable_name == 'on':
                    error = True
                    while error:
                        try:
                            config.logging.warning("FirebaseTest: New On Time = {0}".format(value))
                            # Hours
                            memory_address = 7
                            data_to_write = int(value / 3600)
                            minutes = int(value % 3600)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Minutes
                            memory_address = 8
                            data_to_write = int(minutes / 60)
                            seconds = int(value % 60)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Seconds
                            memory_address = 9
                            data_to_write = seconds
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                        except IOError as e:
                            config.logging.warning("FirebaseTest: No response from instrument")
                        else:
                            error = False

                elif variable_name == 'sa':
                    error = True
                    while error:
                        try:
                            config.logging.warning("FirebaseTest: New Sale Time = {0}".format(value))
                            # Hours
                            memory_address = 16
                            data_to_write = int(value / 3600)
                            minutes = int(value % 3600)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Minutes
                            memory_address = 17
                            data_to_write = int(minutes / 60)
                            seconds = int(value % 60)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Seconds
                            memory_address = 18
                            data_to_write = seconds
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                        except IOError as e:
                            config.logging.warning("FirebaseTest: No response from instrument")
                        else:
                            error = False

                elif variable_name == 'of':
                    error = True
                    while error:
                        try:
                            config.logging.warning("FirebaseTest: New Off Time = {0}".format(value))
                            # Hours
                            memory_address = 13
                            data_to_write = int(value / 3600)
                            minutes = int(value % 3600)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Minutes
                            memory_address = 14
                            data_to_write = int(minutes / 60)
                            seconds = int(value % 60)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Seconds
                            memory_address = 15
                            data_to_write = seconds
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                        except IOError as e:
                            config.logging.warning("FirebaseTest: No response from instrument")
                        else:
                            error = False

                elif variable_name == 'b':
                    error = True
                    while error:
                        try:
                            config.logging.warning("FirebaseTest: New B Time = {0}".format(value))
                            # Hours
                            memory_address = 10
                            data_to_write = int(value / 3600)
                            minutes = int(value % 3600)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Minutes
                            memory_address = 11
                            data_to_write = int(minutes / 60)
                            seconds = int(value % 60)
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                            # Seconds
                            memory_address = 12
                            data_to_write = seconds
                            self.instrument.write_register(registeraddress=memory_address,
                                                           value=data_to_write,
                                                           functioncode=6)
                        except IOError as e:
                            config.logging.warning("FirebaseTest: No response from instrument")
                        else:
                            error = False
                elif variable_name == 'fb':
                    try:
                        config.logging.warning("Firebase Test: live data! = {0}".format(value))
                        if value == 1:
                            self.live_data = True
                            self.live_countdown = 60
                        elif value == 0:
                            self.live_data = False

                    except IOError as e:
                        config.logging.warning("Firebase Test: dunno what happened ")

                else:
                    raise Exception("Don't know that command!")

        except Exception as e:
            # Error
            config.logging.error('Error executing command!! - {0}'.format(e.message))

        finally:
            if self.modbus_lock.locked():
                self.modbus_lock.release()
            return