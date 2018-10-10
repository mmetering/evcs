import unittest
import os, pty
from evcs.serial_listener import EVCS
import logging
from time import sleep


class ChargingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_log_name = 'serial_test.log'
        cls._temp_log = open(cls._temp_log_name, 'w+')
        cls._temp_path = os.path.abspath(cls._temp_log_name)

        cls._master, slave = pty.openpty()
        s_name = os.ttyname(slave)
        cls._evcs = EVCS(s_name, logfile=cls._temp_path, loglevel=logging.INFO, logformat='%(message)s')
        cls._evcs.start()

    @classmethod
    def tearDownClass(cls):
        cls._evcs.stop()
        os.remove(cls._temp_path)

    @staticmethod
    def flush_file(filename):
        with open(filename, 'w') as f:
            f.seek(0)
            f.truncate()
            f.close()

    @staticmethod
    def check_log():
        with open(ChargingTest._temp_log_name, 'r') as f:
            content = f.read()
            f.close()

        ChargingTest.flush_file(ChargingTest._temp_log_name)
        return content

    def test_charger_alive(self):
        os.write(ChargingTest._master, b'LADER 1 lebt\r\n')
        sleep(0.2)

        self.assertEqual('Charger 1 is alive\n', ChargingTest.check_log())

    def test_charging_start(self):
        os.write(ChargingTest._master, b'Abrechnung auf\r\n')
        os.write(ChargingTest._master, b'Tag ID = D6 4F C9 3B\r\n')
        sleep(0.3)
        self.assertEqual('Ready for charging on station with tag D6 4F C9 3B\n', ChargingTest.check_log())

        os.write(ChargingTest._master, b'Verstanden\r\n')
        sleep(0.3)

        self.assertEqual('Charging has been started with tag D6 4F C9 3B\n', ChargingTest.check_log())

    @unittest.expectedFailure
    def test_charging_end_fail(self):
        os.write(ChargingTest._master, b'Tag ID = D6 4F C9 3B\r\n')
        os.write(ChargingTest._master, b'total FERTIG\r\n')
        sleep(0.3)

        self.assertEqual('Could not found session initiated with tag D6 4F C9 3B\n', ChargingTest.check_log())
        self.assertRaises(KeyError, ChargingTest._evcs.sessions['D6 4F C9 3B'])

    def test_charging_end(self):
        os.write(ChargingTest._master, b'Abrechnung auf\r\n')
        os.write(ChargingTest._master, b'Tag ID = D6 4F C9 3B\r\n')
        os.write(ChargingTest._master, b'Verstanden\r\n')
        sleep(0.3)

        ChargingTest.check_log()
        self.assertTrue(ChargingTest._evcs.sessions['D6 4F C9 3B'].is_open())

        os.write(ChargingTest._master, b'Tag ID = D6 4F C9 3B\r\n')
        os.write(ChargingTest._master, b'total FERTIG\r\n')
        sleep(0.3)

        self.assertEqual('Charging has been stopped with tag D6 4F C9 3B\n', ChargingTest.check_log())
        self.assertDictEqual(ChargingTest._evcs.sessions, {})


if __name__ == "__main__":
    unittest.main()
