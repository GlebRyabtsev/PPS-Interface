import sys

from serial_connection import serial_ports, ReadVoltageResponse, ReadCurrentResponse, SetVoltageRequest, \
    ReadVoltageRequest, ReadCurrentRequest, SerialConnection
from ui_portselector import Ui_PortSelector
from ui_standardmode import Ui_StandardMode

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget, \
    QGridLayout, QComboBox, \
    QVBoxLayout, QLCDNumber, QMessageBox

from datetime import datetime


def timestamp(i):
    print(str(i), " ", datetime.now().time())


def serial_ports_fast_dummy():
    return ['a', 'b', 'c']


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

    __active = True  # indicates whether the interface is currently selected

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
        self.serial_connection.connection_status_change_signal.connect(self.connections_status_changed_handler)

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
        if not self.__active or not self.serial_connection.is_connected():
            return
        lcd_display(self.ui.real_voltage_lcd, r.voltage / 1000.0)

    def read_current_response_handler(self, r: ReadCurrentResponse):
        if not self.__active or not self.serial_connection.is_connected():
            return
        lcd_display(self.ui.current_lcd, r.current / 1000.0)

    def connections_status_changed_handler(self, status: bool):
        if status is False:
            self.__zero_lcds()



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
