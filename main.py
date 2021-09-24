import glob
import threading
from queue import SimpleQueue, Empty

import serial
import sys
import time

from ui_portselector import Ui_PortSelector
from ui_standardmode import Ui_StandardMode

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import QApplication, QWidget, \
    QGridLayout, QComboBox, \
    QVBoxLayout, QLCDNumber, QMessageBox

from datetime import datetime


def timestamp(i):
    print(str(i), " ", datetime.now().time())


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

    STARTING_BYTE = b'\xEE'

    def parse(self, b: bytes):
        # check the starting byte
        if b[0:1] != self.STARTING_BYTE:
            self._valid = False
            return

        # check response length
        self._data_length = int.from_bytes(b[1:2], byteorder="big", signed=False)
        if len(b) != self._data_length + 2:
            self._valid = False
            return

        # save data bytes
        self._data_bytes = b[2:]

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

    _checksum = None
    sent = False  # indicated whether the request has been sent
    _data_bytes: bytes = None

    def __init__(self, command, data_bytes: bytes, response):
        self._command = command
        self._data_bytes = data_bytes
        self._data_length = len(data_bytes).to_bytes(1, 'big')
        self.response = response
        self.__compute_checksum()

    def __compute_checksum(self):
        self._checksum = b'\x00'  # todo: implement computing checksum

    def compile(self):  # return a concatenated byte string to be send to the device
        compiled = b''.join([self.STARTING_BYTE, self._command, self._data_length, self._data_bytes, self._checksum])
        return compiled


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
        self.voltage = int.from_bytes(self._data_bytes, 'little', signed=True)


class ReadCurrentResponse(SerialResponse):
    def __init__(self):
        super(ReadCurrentResponse, self).__init__()
        self.current = None

    def parse(self, b: bytes):
        super(ReadCurrentResponse, self).parse(b)
        if self._data_length != 2:
            self._valid = False
            return
        self.current = int.from_bytes(self._data_bytes, 'little', signed=True)


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

    def update_value(self, voltage):
        self._data_bytes = b''.join([self._data_bytes[0:1], voltage.to_bytes(2, byteorder='big', signed=False)])


class ReadVoltageRequest(SerialRequest):
    __READ_VOLTAGE_REQUEST_COMMAND = b'\x02'

    def __init__(self, channel: int):
        channel_byte = bytes([channel])
        super(ReadVoltageRequest, self).__init__(self.__READ_VOLTAGE_REQUEST_COMMAND,
                                                 channel_byte,
                                                 ReadVoltageResponse())


class ReadCurrentRequest(SerialRequest):
    __READ_CURRENT_REQUEST_COMMAND = b'\x03'

    def __init__(self, channel: int):
        channel_byte = bytes([channel])
        super(ReadCurrentRequest, self).__init__(self.__READ_CURRENT_REQUEST_COMMAND,
                                                 channel_byte,
                                                 ReadCurrentResponse())


class SerialConnection(QThread):
    __TIMEOUT = 1  # timeout in seconds
    __port = serial.Serial()
    __timeout = True
    __connected = False
    __connection_pending = False
    __request_queue = SimpleQueue()
    __serial_lock = threading.Lock()
    __exit = False

    connection_status_change_signal = Signal(bool)
    read_voltage_signal_1 = Signal(ReadVoltageResponse)
    read_voltage_signal_2 = Signal(ReadVoltageResponse)
    read_current_signal_1 = Signal(ReadCurrentResponse)
    read_current_signal_2 = Signal(ReadCurrentResponse)

    def __init__(self, n_channels):
        super(SerialConnection, self).__init__()

    def run(self):
        while not self.__exit:  # and (self.__connected or self.__connection_pending)
            (request, signal) = self.__request_queue.get()
            if request is None:
                raise RuntimeError('No request')
            request.sent = True

            with self.__serial_lock:
                # sending the request
                self.__port.write(request.compile())

                timeout = time.time() + self.__TIMEOUT
                timeout_occurred = True  # separate variable since __listener can be run in a different thread
                while time.time() < timeout:
                    if self.__port.in_waiting == 0:
                        time.sleep(0.1)
                        continue
                    current_starting_byte = self.__port.read()
                    if current_starting_byte != SerialResponse.STARTING_BYTE:  # sth has gone wrong so flush everything
                        self.__port.flush()
                        self.__port.write(request.compile())
                        continue
                    data_length = self.__port.read()
                    data_and_checksum = self.__port.read(int.from_bytes(data_length, "big"))
                    # response receiving finished - flush the buffer just in case
                    self.__port.flush()
                    request.response.parse(
                        b''.join([current_starting_byte, data_length, data_and_checksum]))
                    if request.response.is_valid():
                        timeout_occurred = False
                        break
                    else:
                        self.__port.write(request.compile())
            self.__timeout = timeout_occurred  # main timeout flag updated

            if timeout_occurred:
                self.__connected = False
                self.connection_status_change_signal.emit(False)
                continue

            if signal is self.connection_status_change_signal:
                if isinstance(request, ConnectionRequest):
                    self.__connected = True
                    self.__connection_pending = False
                    signal.emit(True)
                else:
                    pass  # todo disconnect request
            elif signal is not None:
                signal.emit(request.response)

    def send_request(self, request: SerialRequest, signal: Signal = None):
        self.__request_queue.put((request, signal))

    def connect_serial(self, port: str):
        self.__connected = False
        self.__connection_pending = True
        while True:  # clear old items from the request queue
            try:
                self.__request_queue.get_nowait()
            except Empty:
                break

        with self.__serial_lock:  # try to open com port
            try:
                self.__port = serial.Serial(port)
                self.__port.baudrate = 115200
                self.__port.timeout = self.__TIMEOUT
            except serial.SerialException:
                try:
                    self.__port.close()
                except serial.SerialException:
                    pass
                self.connection_status_change_signal.emit(False)
                return

        self.send_request(ConnectionRequest(), self.connection_status_change_signal)  # send the request

    def disconnect_serial(self):
        self.__connected = False
        with self.__serial_lock:
            self.__port.close()
        self.connection_status_change_signal.emit(False)

    def is_connected(self):
        return self.__connected


class PortSelector(QWidget):
    __disconnect_pending = False

    def __init__(self, serial_connection: SerialConnection):
        super(PortSelector, self).__init__()
        # uic.loadUi("port_selector.ui", self)
        self.ui = Ui_PortSelector()
        self.ui.setupUi(self)
        self.ui.refreshButton.clicked.connect(self.refresh_button_clicked)
        self.ui.connectButton.clicked.connect(self.connect_button_clicked)
        self.ui.connectButton.setDisabled(True)
        self.ui.portSelectorComboBox.currentTextChanged.connect(self.port_selected)
        self.refresh_button_clicked()
        self.serial_connection = serial_connection

        self.serial_connection.connection_status_change_signal.connect(self.connection_status_changed_handler)

    def refresh_button_clicked(self):
        ports = serial_ports()
        self.ui.portSelectorComboBox.clear()
        for p in ports:
            self.ui.portSelectorComboBox.addItem(p)

    def port_selected(self):
        self.ui.connectButton.setEnabled(True)

    def __display_connection_status(self, status: str):
        text = None
        if status == 'not connected':
            text = 'Nicht verbunden'
        elif status == 'connecting':
            text = 'Verbindung wird aufgestellt...'
        elif status == 'connected':
            text = 'Verbunden'
        if text is not None:
            self.ui.connectedLabel.setText(text)

    def __display_connection_error(self):
        mb = QMessageBox()
        mb.setIcon(QMessageBox.Critical)
        mb.setText("Fehler bei der Kommunikation mit dem Gerät")
        mb.setWindowTitle("Fehler")
        mb.setStandardButtons(QMessageBox.Ok)
        mb.exec()

    def connection_status_changed_handler(self, status: bool):
        if status is True:
            self.update_ui_connected()
        else:
            self.update_ui_disconnected()
            if self.__disconnect_pending:
                self.__disconnect_pending = False
            else:  # unexpected disconnect
                self.__display_connection_error()

    def update_ui_disconnected(self):
        self.__display_connection_status('not connected')
        self.ui.connectButton.setEnabled(True)
        self.ui.connectButton.setText('Verbinden')

    def update_ui_connected(self):
        self.__display_connection_status('connected')
        self.ui.connectButton.setEnabled(True)
        self.ui.connectButton.setText('Trennen')

    def update_ui_connecting(self):
        self.__display_connection_status('connecting')
        self.ui.connectButton.setDisabled(True)

    def connect_button_clicked(self):
        if self.serial_connection.is_connected():
            self.__disconnect_pending = True
            self.serial_connection.disconnect_serial()
        else:
            self.update_ui_connecting()
            self.serial_connection.connect_serial(self.ui.portSelectorComboBox.currentText())


def lcd_display(lcd: QLCDNumber, value: float):
    lcd.display('{:5.3f}'.format(value))


class StandardMode(QWidget):
    __set_voltage_req_in_queue: SetVoltageRequest = None
    __read_voltage_req_in_queue: ReadVoltageRequest = None
    __read_current_req_in_queue: ReadCurrentRequest = None

    def __init__(self, channel_number, serial_connection: SerialConnection):
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

        self.serial_connection = serial_connection

        if channel_number == 1:
            sv = self.serial_connection.read_voltage_signal_1
            sc = self.serial_connection.read_current_signal_1
        else:
            sv = self.serial_connection.read_voltage_signal_2
            sc = self.serial_connection.read_current_signal_2

        sv.connect(self.read_voltage_response_handler)
        sc.connect(self.read_current_response_handler)

        self.__zero_lcds()

        self.__read_values_timer = QTimer(self)
        self.__read_values_timer.timeout.connect(self.read_values)
        self.__read_values_timer.start(125)

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
        if self.serial_connection.is_connected():  # self.ui.change_voltage_check_box.isChecked() and
            if self.__set_voltage_req_in_queue is not None and not self.__set_voltage_req_in_queue.sent:
                self.__set_voltage_req_in_queue.update_value(self.target_voltage)
            else:
                self.__set_voltage_req_in_queue = SetVoltageRequest(self.target_voltage, self.channel_number - 1)
                self.serial_connection.send_request(self.__set_voltage_req_in_queue)

    def read_values(self):
        if not self.serial_connection.is_connected():
            return
        if self.channel_number == 1:
            sv = self.serial_connection.read_voltage_signal_1
            sc = self.serial_connection.read_current_signal_1
        else:
            sv = self.serial_connection.read_voltage_signal_2
            sc = self.serial_connection.read_current_signal_2
        if self.__read_voltage_req_in_queue is None or self.__read_voltage_req_in_queue.sent:
            self.__read_voltage_req_in_queue = ReadVoltageRequest(self.channel_number - 1)
            self.serial_connection.send_request(self.__read_voltage_req_in_queue, sv)
        if self.__read_current_req_in_queue is None or self.__read_current_req_in_queue.sent:
            self.__read_current_req_in_queue = ReadCurrentRequest(self.channel_number - 1)
            self.serial_connection.send_request(self.__read_current_req_in_queue, sc)

    def __zero_lcds(self):
        lcd_display(self.ui.set_voltage_lcd, 0.0)
        lcd_display(self.ui.real_voltage_lcd, 0.0)
        lcd_display(self.ui.current_lcd, 0.0)

    def read_voltage_response_handler(self, r: ReadVoltageResponse):
        lcd_display(self.ui.real_voltage_lcd, r.voltage / 1000.0)

    def read_current_response_handler(self, r: ReadCurrentResponse):
        lcd_display(self.ui.current_lcd, r.current / 1000.0)


class Channel(QWidget):
    def __init__(self, channel_number: int, serial_connection: SerialConnection, *args, **kwargs):
        super(Channel, self).__init__(*args, **kwargs)
        self.vbox_layout = QVBoxLayout()
        self.setLayout(self.vbox_layout)
        self.mode_combo_box = QComboBox(self)
        self.vbox_layout.addWidget(self.mode_combo_box)

        self.channel_number = channel_number

        self.serial_connection = serial_connection

        self.standard_mode = StandardMode(channel_number, serial_connection)

        self.modes = {
            'Standard': self.load_standard_mode,
            'PWM': self.load_pwm_mode
        }

        for m in self.modes:
            self.mode_combo_box.addItem(m)

        self.load_standard_mode()

    def load_standard_mode(self):
        # self.standard_mode.__init__(self.channel_number)
        self.vbox_layout.insertWidget(1, self.standard_mode)

    def load_pwm_mode(self):
        pass


class MainWindow(QWidget):
    serial_connection = SerialConnection(2)

    def __init__(self, n_channels, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.n_channels = n_channels
        self.setWindowTitle("Spannungsquelle")
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.port_selector = PortSelector(self.serial_connection)
        self.grid.addWidget(self.port_selector, 0, 0, 1, n_channels, Qt.AlignTop)
        self.channels = []
        for ch in range(1, n_channels + 1):
            self.channels.append(Channel(ch, self.serial_connection))
            self.grid.addWidget(self.channels[ch - 1], 1, ch - 1)

        self.setFixedSize(self.grid.sizeHint())
        self.serial_connection.start()


app = QApplication(sys.argv)

main_window = MainWindow(n_channels=2)
main_window.show()

app.exec()
