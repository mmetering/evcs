from django.core.management.base import BaseCommand, CommandError
from evcs.serial_listener import EVCS
import serial
import logging

logger = logging.getLogger(__name__)

PORT = '/dev/ttyUSB1'


class Command(BaseCommand):
    help = 'Starts the EVCS process'

    def handle(self, *args, **options):
        try:
            evcs = EVCS(PORT)
        except serial.SerialException as e:
            logger.exception('Could not open port %s in MMetering EVCS' % PORT)
            return

        logger.info('Starting EVCS now...')
        evcs.start()
        logger.info('EVCS process ended...')
