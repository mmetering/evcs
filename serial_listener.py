import serial
import re
from datetime import datetime
from evcs.models import ChargingValue
from mmetering.models import Flat, Meter
from backend.eastronSDM630 import EastronSDM630
import backend.serial as be
import logging
import threading
from queue import Queue

logger = logging.getLogger(__name__)

_FINISH = False


class Session:
    """
    Represents a charging session from START to END, instantiated
    by the charging station.
    """

    def __init__(self, charging_station, tag):
        self.charging_station = Flat.objects.get(name=charging_station)
        self.meter = Meter.objects.get(flat=self.charging_station, active=True)

        self.tag = tag
        self.start_time = None
        self.end_time = None

        model = ChargingValue(
            rfid=self.tag,
            charging_station=self.charging_station.pk
        )
        model.save()
        self.id = model.pk

    def is_open(self):
        return self.start_time is not None and self.end_time is None

    def open(self):
        self.start_time = datetime.today()
        val = ChargingValue.objects.get(pk=self.id)
        val.start_time = self.start_time
        try:
            # TODO: Save L1, L2, L3 here according to issue #1.
            start_value = EastronSDM630(be.choose_port(be.PORTS_LIST), self.meter.addresse).read_total_import()
            val.start_value = start_value

            # Adding start_time only if meter value could have been read.
            val.save()

            return True
        except (IOError, ValueError) as e:
            logger.exception('MMetering EVCS: Could not reach meter with address %d' % self.meter.addresse)
            return False

    def close(self):
        self.end_time = datetime.today()
        val = ChargingValue.objects.get(pk=self.id)
        val.end_time = self.end_time
        try:
            # TODO: Save L1, L2, L3 here according to issue #1.
            end_value = EastronSDM630(be.choose_port(be.PORTS_LIST), self.meter.addresse).read_total_import()
            val.end_value = end_value

            # Adding end_time only if meter value could have been read.
            val.save()

            return True
        except (IOError, ValueError) as e:
            logger.exception('MMetering EVCS: Could not reach meter with address %d' % self.meter.addresse)
            return False

    def get_charging_station(self):
        return self.charging_station.name

    def get_tag(self):
        return self.tag

    def get_session_id(self):
        return self.id


class SerialListener(threading.Thread):
    def __init__(self, port, serial_in: Queue, serial_out: Queue,
                 baud=19200,
                 bytesize=serial.EIGHTBITS,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE):
        threading.Thread.__init__(self, name='SerialListenerThread')
        self.ser = serial.Serial(port, baud, bytesize, parity, stopbits)
        self.serial_in = serial_in
        self.serial_out = serial_out

    def run(self):
        self.ser.flushInput()
        self.ser.flushOutput()

        while True:
            if _FINISH:
                self.ser.close()
                break

            # read data from the bus
            res = b''
            if self.ser.inWaiting() > 0:
                res = self.ser.readline()
            line = str(res, 'ascii')

            if len(line) > 0 and line != ' ':
                logger.debug('INCOMING>' + line.replace('\n', ''))
                self.serial_in.put_nowait(line)

            # write data to the bus
            if not self.serial_out.empty():
                data = self.serial_out.get_nowait()
                logger.debug('OUTGOING>' + data)
                data += '\r\n'
                self.ser.write(data.encode())


class SerialHandler(threading.Thread):
    def __init__(self, serial_in: Queue, serial_out: Queue, sessions):
        threading.Thread.__init__(self, name='SerialHandlerThread')
        self.sessions = sessions
        self.serial_in = serial_in
        self.serial_out = serial_out
        self.regexp = {
            'alive': 'LADER ([0-9]+) lebt',
            'start': '(Abrechnung auf)',
            'rfid': 'Tag\s?ID\s?=\s?((?:(?:[0-9A-F|A-F0-9]{2}\s?))+)',
            'check': '(Verstanden)',
            'end': '(total FERTIG)',
        }

    def run(self):
        while True:
            if _FINISH:
                break

            if not self.serial_in.empty():
                data = self.serial_in.get_nowait()
                logger.debug('PROCESS>' + data.replace('\r\n', ''))
                alive_match = re.match(self.regexp['alive'], data)
                start_match = re.match(self.regexp['start'], data)
                tag_match = re.match(self.regexp['rfid'], data)
                if alive_match:
                    logger.info('Charger %s is alive' % alive_match.group(1))
                elif start_match:
                    logger.debug('PROCESS>Wait for Tag ID')
                    # TODO: Check queue.Empty exception where block==True
                    rfid_line = self.serial_in.get(block=True, timeout=3)
                    rfid_match = re.match(self.regexp['rfid'], rfid_line)
                    if rfid_match:
                        tag_id = rfid_match.group(1).replace('\r', '')
                        self.start_loading(tag_id)
                elif tag_match:
                    end_line = self.serial_in.get(block=True, timeout=3)
                    end_match = re.match(self.regexp['end'], end_line)
                    if end_match:
                        tag_id = tag_match.group(1).replace('\r', '')
                        self.stop_loading(tag_id)

    def start_loading(self, tag_id):
        # TODO: Replace static charging station name
        charging_station = 'Lader 1'
        logger.info('Ready for charging on station %s with tag %s' % (charging_station, tag_id))
        try:
            session = Session('Lader 1', tag_id)
            self.serial_out.put_nowait('OK_Lader1!')
        except Meter.DoesNotExist or Flat.DoesNotExist:
            logger.exception('There is no registered meter for %s.' % charging_station)

            # TODO: Implement error handling on the hardware side
            self.serial_out.put_nowait('ERROR_Lader1!')
            return

        self.sessions[tag_id] = session

        check_line = self.serial_in.get(block=True, timeout=3)
        check_match = re.match(self.regexp['check'], check_line)
        if check_match:
            if session.open():
                logger.info('Charging has been started with tag %s' % tag_id)
            else:
                logger.error('Starting the charging process failed on opening the session with tag %s' % tag_id)

    def stop_loading(self, tag_id):
        try:
            session = self.sessions[tag_id]

            if session.close():
                logger.info('Charging has been stopped with tag %s' % tag_id)
                del self.sessions[session.get_tag()]
            else:
                logger.error('Stopping the charging process failed on closing the session with tag %s' % tag_id)
        except KeyError:
            logger.error('Could not found session initiated with tag %s' % tag_id)


class EVCS:
    in_queue = Queue()
    out_queue = Queue()
    sessions = dict()

    def __init__(self, port, **kwargs):
        if kwargs.get('logfile'):
            logging.basicConfig(
                filename=kwargs.get('logfile'),
                level=kwargs.get('loglevel'),
                format=kwargs.get('logformat')
            )

        self.listener = SerialListener(port, EVCS.in_queue, EVCS.out_queue)
        self.handler = SerialHandler(EVCS.in_queue, EVCS.out_queue, EVCS.sessions)

    def start(self):
        self.listener.start()
        self.handler.start()

    def stop(self):
        global _FINISH
        _FINISH = True
        self.handler.join()
        self.listener.join()



