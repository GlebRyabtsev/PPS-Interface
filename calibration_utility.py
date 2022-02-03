from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal
from threading import Event

from serial_connection import *


class InterfaceThread(QThread):
    finished_signal = Signal()
    sc: SerialConnection = None

    connected = False
    sc_signal_value = None
    sc_signal_arrived = Event()

    def __init__(self, sc):
        super(InterfaceThread, self).__init__()
        self.sc = sc

    # SC signal handlers

    def signal_handler(self, value):
        self.sc_signal_value = value
        self.sc_signal_arrived.set()

    def connection_status_change_signal_handler(self, status):
        self.connected = status
        self.sc_signal_arrived.set()

    def wait_for_response(self):
        self.sc_signal_arrived.wait()
        self.sc_signal_arrived.clear()

    def run(self):
        while True:
            self.connect_to_device()
            if not self.connected:
                continue
            for ch_id in range(2):
                a = input('Do you want to calibrate channel '.join([str(ch_id+1), '? [y/n]']))
                if a[0] != 'y':
                    continue
                print('Calibrating voltage sensor')
                self.sc.send_request(ChangeChannelModeRequest(ch_id, 'disabled'), self.sc.general_signal)
                self.wait_for_response()
                if not self.connected:
                    self.print_connection_failure()
                    break
                input('Setting zero point. Please ensure that the output voltage is zero. When ready, press ENTER.')
                self.sc.send_request(ReadVoltageRequest(ch_id), self.sc.general_signal)
                self.wait_for_response()
                if not self.connected:
                    self.print_connection_failure()
                    break
                v0 = self.sc_signal_value.voltage
                input('Please ensure that the output is disconnected from ground. When ready, press ENTER.')
                v_test = 5000
                self.sc.send_request(SetVoltageRequest(ch_id, v_test), self.sc.general_signal)
                self.wait_for_response()
                if not self.connected:
                    self.print_connection_failure()
                    break
                v_real = int(input('Please measure the output voltage and enter it in mV (eg. 4568):'))
                # todo: send DAC/DigiPot values instead; calibrate both SMPS and LDO

            if not self.connected:
                continue

    def print_connection_failure(self):
        print('Connection failure.')

    def connect_to_device(self):
        print('Please select serial port')
        self.connected = False
        ports = serial_ports()
        i = 0
        for port in ports:
            print('[', i, '] ', port)
            i += 1
        p = int(input('Port: '))
        self.sc.connect_serial(ports[p])
        print('Connecting...')
        self.wait_for_response()
        if self.connected:
            print('Connected.')
        else:
            print('Connection failure.')



class CalibrationUtility(QApplication):
    disconnect_pending = False
    sc = SerialConnection(2)
    it = InterfaceThread(sc)

    def __init__(self):
        super(CalibrationUtility, self).__init__()
        self.it.finished_signal.connect(self.interface_finished_handler)
        self.it.start()
        self.sc.start()
        self.exec()

    def interface_finished_handler(self):
        self.sc.set_exit()
        self.sc.wait()
        quit()




app = CalibrationUtility()
