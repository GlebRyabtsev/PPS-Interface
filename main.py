import glob
import threading

import serial
import sys
import time

from ui_portselector import Ui_PortSelector
from ui_standardmode import Ui_StandardMode

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, \
    QGridLayout, QComboBox, \
    QVBoxLayout, QLCDNumber


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def serial_ports_fast_dummy():
    return ['a', 'b', 'c']


class SerialResponse:

    def __init__(self):
        self._data_bytes = None
        self._data_length = None
        self._valid = True
        self.received = False

    STARTING_BYTE = b'\xEE'

    def parse(self, b: bytes):
        # check the starting byte
        if bytes[0] != self.STARTING_BYTE:
            self._valid = False
            return

        # check response length
        self._data_length = bytes[1]
        if len(b) != self._data_length + 2:
            self._valid = False
            return

        # save data bytes
        self._data_bytes = b[1:-1]

        # verify checksum
        # if self.__compute_checksum() != self._data_bytes[-1]
        #     self._valid = False
        #     return

    def __compute_checksum(self):
        pass  # TODO: implement compute checksum

    def get_value(self):
        return None

    def is_valid(self):
        return self._valid


class SerialRequest:
    STARTING_BYTE = b'\xDD'

    def __init__(self, command, data_bytes: bytes, response):
        self._command = command
        self._data_bytes = data_bytes
        self._data_length = len(data_bytes)
        self._checksum = None
        self.response = response
        self.__compute_checksum()

    def __compute_checksum(self):
        self._checksum = 0  # todo: implement computing checksum

    def compile(self):  # return a concatenated byte string to be send to the device
        return b''.join([self.STARTING_BYTE, self._command, self._data_length, self._data_bytes, self._checksum])


class StandardAcknowledgement(SerialResponse):
    __ACK_BYTES = bytes.fromhex('41434B')  # b'ACK'

    def __init__(self):
        super(StandardAcknowledgement, self).__init__()

    def parse(self, b: bytes):
        super(StandardAcknowledgement, self).parse(b)
        if self._data_bytes != self.__ACK_BYTES:
            self._valid = False
            return

    def get_value(self):
        return self._valid


class ReadVoltageResponse(SerialResponse):
    def __init__(self):
        super(ReadVoltageResponse, self).__init__()
        self.voltage = None  # in millivolts

    def parse(self, b: bytes):
        super(ReadVoltageResponse, self).parse(b)
        if self._data_length != 2:
            self._valid = False
            return
        self.voltage = int.from_bytes(self._data_bytes, 'big', signed=False)


class ConnectionRequest(SerialRequest):
    __CONNECTION_REQUEST_COMMAND = b'\x00'

    def __init__(self):
        super(ConnectionRequest, self).__init__(self.__CONNECTION_REQUEST_COMMAND, bytes(0), StandardAcknowledgement())


class SetVoltageRequest(SerialRequest):
    __SET_VOLTAGE_REQUEST_COMMAND = b'\x01'

    def __init__(self, voltage: int, channel: int):
        channel_byte = bytes([channel])
        super(SetVoltageRequest, self).__init__(self.__SET_VOLTAGE_REQUEST_COMMAND,
                                                b''.join([channel_byte,
                                                          voltage.to_bytes(2, byteorder='big', signed=False)]),
                                                StandardAcknowledgement())


class ReadVoltageRequest(SerialRequest):
    __READ_VOLTAGE_REQUEST_COMMAND = b'\x02'

    def __init__(self, channel: int):
        channel_byte = bytes([channel])
        super(ReadVoltageRequest, self).__init__(self.__READ_VOLTAGE_REQUEST_COMMAND,
                                                 channel_byte,
                                                 ReadVoltageResponse())


class SerialConnection:
    __TIMEOUT = 5  # timeout in seconds

    __port = serial.Serial()
    __current_request = None
    __timeout = True
    __connected = False

    @classmethod
    def __listener(cls):
        if cls.__current_request is None:
            raise RuntimeError('No request')
        timeout = time.time() + cls.__TIMEOUT
        timeout_occurred = True  # separate variable since __listener can be run in a different thread
        while time.time() < timeout:
            if cls.__port.in_waiting == 0:
                time.sleep(0.1)
                continue
            current_starting_byte = cls.__port.read()
            if current_starting_byte != SerialResponse.STARTING_BYTE:  # sth has gone wrong so flush everything
                cls.__port.flush()
                cls.send_request(cls.__current_request)
                continue
            data_length = cls.__port.read()
            data_and_checksum = cls.__port.read(data_length + 1)
            # response receiving finished - flush the buffer just in case
            cls.__port.flush()
            cls.__current_request.response.parse(b''.join([current_starting_byte, data_length, data_and_checksum]))
            if cls.__current_request.response.is_valid():
                timeout_occurred = False
                break
            else:
                cls.send_request(cls.__current_request)

        cls.__timeout = timeout_occurred  # main timeout flag updated
        if timeout_occurred:
            return

        cls.__current_request.response.received = True

        cls.__current_request = None

    __listener_thread = threading.Thread(target=__listener)

    @classmethod
    def send_request_and_listen(cls, request: SerialRequest, synchronous=True) -> bool:
        # sending the request
        cls.send_request(request)
        # start the listener process
        cls.__port.flush()
        cls.__listener_thread.start()
        if synchronous:
            cls.__listener_thread.join()
        if cls.__timeout:
            cls.__connected = False
        return not cls.__timeout

    @classmethod
    def send_request(cls, request: SerialRequest):
        cls.__port.write(request.compile())
        cls.__current_request = request

    @classmethod
    def connect(cls, port: str) -> bool:
        cls.__port = serial.Serial(port)
        cls.__port.baudrate = 115200
        cls.__port.timeout = 1

        ack = StandardAcknowledgement()
        cls.send_request_and_listen(ConnectionRequest())
        cls.__connected = ack.get_value()

        return cls.__connected

    @classmethod
    def is_connected(cls) -> bool:
        return cls.__connected


class PortSelector(QWidget):

    def __init__(self):
        super(PortSelector, self).__init__()
        # uic.loadUi("port_selector.ui", self)
        self.ui = Ui_PortSelector()
        self.ui.setupUi(self)
        self.ui.refreshButton.clicked.connect(self.refresh_button_clicked)
        self.ui.connectButton.clicked.connect(self.connect_button_clicked)
        self.ui.connectButton.setDisabled(True)
        self.ui.portSelectorComboBox.currentTextChanged.connect(self.port_selected)
        self.refresh_button_clicked()

    def refresh_button_clicked(self):
        ports = serial_ports()
        for p in ports:
            self.ui.portSelectorComboBox.addItem(p)

    def port_selected(self):
        self.ui.connectButton.setEnabled(True)

    def connect_button_clicked(self):
        SerialConnection.connect(self.ui.portSelectorComboBox.currentText())


def lcd_display(lcd: QLCDNumber, value: float):
    lcd.display('{:5.3f}'.format(value))


class StandardMode(QWidget):
    def __init__(self, channel_number):
        super(StandardMode, self).__init__()
        # uic.loadUi('standard_mode.ui', self)
        self.ui = Ui_StandardMode()
        self.ui.setupUi(self)
        self.ui.dial.valueChanged.connect(self.dial_value_changed)
        self.previous_dial_value = 0
        self.target_voltage = 0
        self.coarse_increment = 100
        self.fine_increment = 1
        self.min_voltage = 0
        self.max_voltage = 12000

        self.channel_number = channel_number

        self.__zero_lcds()

    def dial_value_changed(self):
        val = self.ui.dial.value()
        increase = True
        if self.previous_dial_value >= 9 and val <= 1:
            increase = True
        elif self.previous_dial_value <= 1 and val >= 9:
            increase = False
        else:
            increase = val > self.previous_dial_value

        self.previous_dial_value = self.ui.dial.value()

        if increase:
            if self.ui.coarse_radio_button.isChecked():
                self.target_voltage -= self.target_voltage % self.coarse_increment
                self.target_voltage += self.coarse_increment
            else:
                self.target_voltage += self.fine_increment
            if self.target_voltage > self.max_voltage:
                self.target_voltage = self.max_voltage
        else:
            if self.ui.coarse_radio_button.isChecked():
                self.target_voltage += self.target_voltage % self.coarse_increment
                self.target_voltage -= self.coarse_increment
            else:
                self.target_voltage -= self.fine_increment
            if self.target_voltage < self.min_voltage:
                self.target_voltage = self.min_voltage

        self.set_voltage()

    def set_voltage(self):
        lcd_display(self.ui.set_voltage_lcd, self.target_voltage / 1000.0)
        if self.ui.change_voltage_check_box.isChecked() and SerialConnection.is_connected():
            req = SetVoltageRequest(self.target_voltage, self.channel_number)
            success = SerialConnection.send_request_and_listen(req)
            # todo: async call better?

    def read_voltage(self):
        if not SerialConnection.is_connected():
            return
        req = ReadVoltageRequest(self.channel_number)
        success = SerialConnection.send_request_and_listen(req)
        if success:
            lcd_display(self.ui.real_voltage_lcd, req.response.voltage / 1000.0)
        else:
            pass  # todo: handle this

    def __zero_lcds(self):
        lcd_display(self.ui.set_voltage_lcd, 0.0)
        lcd_display(self.ui.real_voltage_lcd, 0.0)
        lcd_display(self.ui.current_lcd, 0.0)


class Channel(QWidget):
    def __init__(self, channel_number: int, *args, **kwargs):
        super(Channel, self).__init__(*args, **kwargs)
        self.vbox_layout = QVBoxLayout()
        self.setLayout(self.vbox_layout)
        self.mode_combo_box = QComboBox(self)
        self.vbox_layout.addWidget(self.mode_combo_box)

        self.channel_number = channel_number

        self.standard_mode = StandardMode(channel_number)

        self.modes = {
            'Standard': self.load_standard_mode,
            'PWM': self.load_pwm_mode
        }

        for m in self.modes:
            self.mode_combo_box.addItem(m)

        self.load_standard_mode()

    def load_standard_mode(self):
        #self.standard_mode.__init__(self.channel_number)
        self.vbox_layout.insertWidget(1, self.standard_mode)

    def load_pwm_mode(self):
        pass


class MainWindow(QWidget):

    def __init__(self, n_channels, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.n_channels = n_channels
        self.setWindowTitle("Spannungsquelle")
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.port_selector = PortSelector()
        self.grid.addWidget(self.port_selector, 0, 0, 0, n_channels, Qt.AlignTop)
        self.channels = []
        for ch in range(1, n_channels+1):
            print("Main window for loop, channel " + str(ch))
            self.channels.append(Channel(ch))
            self.grid.addWidget(self.channels[ch-1], 1, ch-1)


app = QApplication(sys.argv)

main_window = MainWindow(n_channels=2)
main_window.show()

app.exec()
