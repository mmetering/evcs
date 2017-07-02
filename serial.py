import serial
import re
from datetime import datetime
from evcs.models import RFID, ChargingValue, ChargingStation
import logging

logger = logging.getLogger(__name__)


class Session:
    """
    Represents a charging session from START to END, instantiated
    by the charging station.
    """

    def __init__(self, header):
        self.id = None
        self.charging_station = header['Name']
        self.key = header['Key']

    def open(self):
        # read start meter value
        # TODO: Implement
        meter_value = 1

        # create new chargingvalue
        value = ChargingValue(
            rfid=RFID.objects.get(serial=self.key),
            charging_station=ChargingStation.objects.get(name=self.charging_station),
            start_time=datetime.today(),
            start_value=meter_value
        )
        value.save()

        # set id
        self.set_session_id(value.pk)

    def close(self):
        # read end meter value
        # TODO: Implement
        meter_value = 1

        # update chargingvalue
        charging_value = ChargingValue.objects.get(pk=self.get_session_id())

        charging_value.end_time = datetime.today()
        charging_value.end_value = meter_value

        charging_value.save()

        return 'OK', self.get_session_id()

    def get_charging_station(self):
        return self.charging_station

    def get_rfid_key(self):
        return self.key

    def get_session_id(self):
        return self.id

    def set_session_id(self, session_id):
        self.id = session_id


class SessionHandler:
    """
    Handles communication according to the MMETERING/1.0 protocol.
    """

    def __init__(self):
        self.sessions = dict()

    def is_empty(self):
        return self.sessions == []

    def get(self, key):
        return self.sessions[key]

    def remove(self, key):
        logger.debug("Session will be closed.")

        session = self.sessions[key]
        del self.sessions[key]
        logger.debug(session)

        return session.close()

    def put(self, session):
        if self.is_valid(session.get_charging_station(), session.get_rfid_key()):
            session.open()
            self.sessions[session.get_session_id()] = session

            logger.debug("New header has been added.")
            logger.debug(session)
            return 'OK', session.get_session_id()
        else:
            logger.debug("Charging Station and/or RFID key is not registered")
            return 'ERROR', session.get_session_id()

    @staticmethod
    def is_valid(cs, rfid):
        return ChargingStation.objects.filter(name=cs).exists() and \
               RFID.objects.filter(serial=rfid).exists()


class SerialListener:
    """
    Listener class for a electrical charging station. Listens for a
    certain keyword on a given Port. The charging station sends the
    following header when it has been unlocked by a RFID chip.

    MMETERING/1.0 <ACTION>
    Name: <CHARGING STATION>
    Key: <RFID-KEY>

    where <ACTION> can be either START or END
    """

    def __init__(self, port, baud=9600):
        self.ser = serial.Serial(port, baud)
        self.handler = SessionHandler()
        self.key_value_pattern = '[\w\d]+: [\w\d]+'

    def listen(self):
        while True:
            line = str(self.ser.readline(), 'ascii')
            line_params = line.split(' ')

            if line_params[0].split('/')[0] == 'MMETERING':
                content_length = str(self.ser.readline(), 'ascii').split(": ")

                chunk = {
                    'Version': line_params[0].split("/")[1],
                    'Action': line_params[1].rstrip(),
                    'Content-Length': int(content_length[1].rstrip())
                }

                for i in range(0, chunk['Content-Length']):
                    header = str(self.ser.readline(), 'ascii')

                    kv = header.split(': ')
                    chunk[kv[0]] = kv[1].rstrip()

                print(chunk)
                self.handle(chunk)

    def handle(self, header):
        if header['Action'] == 'START':
            # new session will be started
            status, session_id = self.handler.put(Session(header))
        else:
            # closes a session
            try:
                status, session_id = self.handler.remove(header['Session-Id'])
            except KeyError:
                # couldn't find the session_id, maybe transmission error
                status = 'ERROR'

        if status is not 'ERROR':
            self.ser.write('MMETERING/1.0 OK\n'.encode())
            self.ser.write(('Session-Id: %d\n' % session_id).encode())
        else:
            self.ser.write('MMETERING/1.0 ERROR\n'.encode())
