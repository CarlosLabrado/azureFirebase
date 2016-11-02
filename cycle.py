import config
import datetime
import uuid

"""
Handles cycle data and functions
"""
__author__ = 'Cesar'


class Cycle:

    to_send = {"id": 0,         # device id
               "st": 0,         # Start Timestamp
               "ot": 0,         # Off Timestamp
               "et": 0,         # End Timestamp
               "ns": 0,         # Number of Strokes
               "ce": 0,         # Calculated Efficiency
               "t": 5           # Message Type
               }

    device_id = None
    uuid = None

    start_timestamp = datetime.datetime
    off_timestamp = datetime.datetime
    end_timestamp = datetime.datetime

    calculated_efficiency = None

    number_of_strokes = 0

    def __init__(self, device_id):
        """
        Create cycle will stamp the start of cycle with the current system time.
        Generates a unique ID for the cycle.
        :return: Cycle object
        """
        self.device_id = device_id
        self.start_timestamp = datetime.datetime.now()
        self.uuid = uuid.uuid4()
        config.logging.warning('Cycle: __init__ - Creating new cycle with uuid: {0}'.format(self.uuid))

    def add_stroke(self):
        """
        Call this method to add a stroke to the cycle count
        """
        self.number_of_strokes += 1
        config.logging.warning('Cycle: add_stroke - Stroke added to cycle {0}: Total strokes: {1}'
                               .format(self.uuid, self.number_of_strokes))

    def well_stopped(self):
        """
        Call this method when the well stops. Will stamp the stop event with the current system time
        """
        self.off_timestamp = datetime.datetime.now()
        config.logging.warning('Cycle: well_stopped - Well stopped for cycle {0} @ {1}'
                               .format(self.uuid, self.off_timestamp))

    def cycle_ended(self):
        """
        Call this method when the end of the cycle occurred. Will stamp the end of cycle with the current system time
        """
        self.end_timestamp = datetime.datetime.now()
        config.logging.warning('Cycle: cycle_ended - Cycle {0} ended @ {1}'
                               .format(self.uuid, self.end_timestamp))

        total_time = (self.end_timestamp - self.start_timestamp).seconds
        on_time = (self.off_timestamp - self.start_timestamp).seconds
        config.logging.warning('Cycle: cycle_ended - Total Time (sec): {0} - On Time (sec): {1}'
                               .format(total_time, on_time))
        self.calculated_efficiency = float(on_time) / float(total_time) * 100.0
        config.logging.warning('Cycle: cycle_ended - Cycle {0} efficiency: {1} %'
                               .format(self.uuid, self.calculated_efficiency))

    def get_dictionary_to_send(self):
        """
        Returns string to be sent to Azure IoT
        :return: JSON string to send
        """
        self.to_send["id"] = self.device_id
        self.to_send["st"] = int(self.start_timestamp.strftime('%s'))
        self.to_send["ot"] = int(self.off_timestamp.strftime('%s'))
        self.to_send["et"] = int(self.end_timestamp.strftime('%s'))
        self.to_send["ns"] = self.number_of_strokes
        self.to_send["ce"] = self.calculated_efficiency
        return self.to_send
