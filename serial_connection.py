import glob
import sys
import threading
import time
from queue import SimpleQueue, Empty

import serial
from PySide6.QtCore import QThread, Signal


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


class ChangeChannelModeRequest(SerialRequest):
    __CHANGE_CHANNEL_MODE_REQUEST_COMMAND = b'\x04'

    def __init__(self, channel: int, mode: str):
        channel_byte = bytes([channel])
        if mode == 'disabled':
            mode_byte = b'\x00'
        elif mode == 'standard':
            mode_byte = b'\x01'
        else:
            raise RuntimeError('ChangeChannelModeRequest: unrecognized mode')

        super(ChangeChannelModeRequest, self).__init__(self.__CHANGE_CHANNEL_MODE_REQUEST_COMMAND,
                                                       channel_byte.join(mode_byte),
                                                       StandardAcknowledgement())


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

    general_signal = Signal(object)

    def __init__(self, n_channels):
        super(SerialConnection, self).__init__()

    def run(self):
        print('Sc running')
        while not self.__exit:
            try:
                (request, signal) = self.__request_queue.get(True, 0.5)
            except Empty:
                continue
            if request is None:
                raise RuntimeError('No request')
            request.sent = True
            if self.__connected is False and isinstance(request, ConnectionRequest) is False:
                continue
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

    def set_exit(self):
        self.__exit = True