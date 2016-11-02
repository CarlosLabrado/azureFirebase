"""
Configuration file
"""
import logging
import os

"""
Console only access (via resin.io)
"""
__author__ = 'Cesar'

"""
Get config from resin.io
"""
uuid = os.environ['RESIN_DEVICE_UUID']

console_only = int(os.environ['console_only'])
logging.warning("Environment Variable: console_only = {0}".format(console_only))

if console_only == 1:
    connection_string = os.environ['connection_string']
    logging.warning("Environment Variable: connection_string = {0}".format(connection_string))
    pass

else:

    modbus_address = int(os.environ['modbus_address'])
    logging.warning("Environment Variable: modbus_address = {0}".format(modbus_address))

    azure_iot_logs = int(os.environ['azure_iot_logs'])
    logging.warning("Environment Variable: azure_iot_logs = {0}".format(azure_iot_logs))

    connection_string = os.environ['connection_string']
    logging.warning("Environment Variable: connection_string = {0}".format(connection_string))

    device_id = int(os.environ['device_id'])
    logging.warning("Environment Variable: device_id = {0}".format(device_id))

    logging_level = os.environ['logging']
    logging.warning("Environment Variable: logging_level = {0}".format(logging_level))

    polling_rate = int(os.environ['update_rate'])
    logging.warning("Environment Variable: polling_rate = {0}".format(polling_rate))

    if logging_level == "DEBUG":
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s',
                            filename='/home/logs/azure.log',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s',
                            filename='/home/logs/azure.log',
                            level=logging.WARNING)

    """
    Logging, external modules
    """
    logging.getLogger("requests").setLevel(logging.WARNING)

    """
    Internet Access Configuration
    """
    # internet_access:
    #   Defines the type of access to the mqtt broker. Supported types:
    #       local_network
    #       cel_modem
    internet_access = 'cel_modem'

    # Address to ping to validate internet connection
    resin = 'www.google.com.mx'

    # Delay to check connection with Broker
    delayPing = 60

    # Allowed time to get a valid ip after power up
    delayIP = 15
