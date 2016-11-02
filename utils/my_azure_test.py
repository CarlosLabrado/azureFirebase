import json
import time
import iothub_client
from iothub_client import *

connection_string = "HostName=petrolog.azure-devices.net;DeviceId=crimson-surf;SharedAccessSignature=SharedAccessSignature sr=petrolog.azure-devices.net%2Fdevices%2Fcrimson-surf&sig=OOScbvgwFrvfAs8wG%2BbbHx9c5le3oDqGvgeZZa9htVg%3D&se=1502841383"

receive_context = 0


current_cycle = {"pc": 1,
                 "pt": 2,
                 "pl": 3,
                 "cc": 4,
                 "cm": 5,
                 "s": 6
                 }

history_cycle = {"off": {"pc": 1,
                         "pt": 2,
                         "pl": 3
                         },
                 "sales": {"pc": 1,
                           "pt": 2,
                           "pl": 3
                           }
                 }

settings = {"fa": 123456,
            "sh": 123456,
            "on": 123456,
            "sa": 123456,
            "of": 123456,
            "b": 123456,
            }

error = {"n": 1,
         "m": "Algo salio mal"}


def set_certificates(iotHubClient):
    from iothub_client_cert import certificates
    try:
        iotHubClient.set_option("TrustedCerts", certificates)
        print("set_option TrustedCerts successful")
    except IoTHubClientError as e:
        print("set_option TrustedCerts failed (%s)" % e)


def __receive_message_callback(message, counter):
    """
    Callback function for Rx messages
    """
    b = message.get_bytearray()
    size = len(b)
    print('ModbusPacemaker: __receive_message_callback - Message Received: \n'
                  '    Data: [{0}]'.format(b[:size].decode('utf-8')))
    return IoTHubMessageDispositionResult.ACCEPTED


def __send_confirmation_callback(message, result, user_contex):
    """
    Confirmation callback function for Tx messages
    """
    print('ModbusPacemaker: __send_confirmation_callback - Confirmation Received: \n'
                         '    Result: [{0}]'.format(result))


iotHubClient = IoTHubClient(connection_string, IoTHubTransportProvider.MQTT)
iotHubClient.set_option("messageTimeout", 10000)
set_certificates(iotHubClient)
iotHubClient.set_option("logtrace", 1)
iotHubClient.set_message_callback(__receive_message_callback, receive_context)


while True:
    try:
        print("ModbusPacemaker: Current: \n{0}".format(json.dumps(current_cycle, indent=4)))
        iotHubClient.send_event_async(IoTHubMessage(json.dumps(current_cycle)), __send_confirmation_callback, 0)

        print("ModbusPacemaker: History: \n{0}".format(json.dumps(history_cycle, indent=4)))
        iotHubClient.send_event_async(IoTHubMessage(json.dumps(history_cycle)), __send_confirmation_callback, 1)

        print("ModbusPacemaker: Settings: \n{0}".format(json.dumps(history_cycle, indent=4)))
        iotHubClient.send_event_async(IoTHubMessage(json.dumps(settings)), __send_confirmation_callback, 2)
    except Exception as e:
        print e.message
    time.sleep(10)

