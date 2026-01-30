import logging
import threading
import time

from serial import Serial

from .errors import IKAError


class IKADevice:
    def __init__(self,
                 port: str,
                 dummy: bool = False,
                 termination_character: bytes = b'\r'
                 ):
        """
        :param str, port: port to connect to the device
        :param termination_character: choose the termination character to read until (default carriage return)
        :param bool, dummy: if dummy is True then dont try to a serial device; used for unit tests
        """
        self._port = port
        self._dummy = dummy
        self.termination_character = termination_character

        self.logger = logging.getLogger(f'{self.__class__.__name__}')

        try:
            if not self.dummy:
                self._ser: Serial = Serial(self.port, 9600, 7, 'E', 1)
                # lock for use when making serial requests
                self._lock = threading.Lock()
        except Exception as e:
            self.logger.error(e)
            raise IKAError(msg=f'Unable to connect to an IKA device on port {port}. Make sure the device is '
                               'plugged in and the port is correct.')

    @property
    def port(self):
        """Port used to connect to the IKA device"""
        return self._port

    @property
    def dummy(self) -> bool:
        """If dummy is True then dont try to a serial device"""
        return self._dummy

    def _send(self,
              command: str,
              ):
        """
        Send a command
        :param str, command: a command with optional parameter's included if required (such as for setting temperature
            or stirring rate)
        :return:
        """
        if not self.dummy:
            with self._lock:
                # format the command to send so that it terminates with the line ending (CR LF)
                formatted_command: str = command + '\x0d\x0a'
                formatted_command_encoded = formatted_command.encode()
                self._ser.write(formatted_command_encoded)
                time.sleep(0.1)

    def _send_and_receive(self,
                          command: str,
                          ):
        if not self._dummy:
            self._send(command)
            response = self._ser.read_until(self.termination_character).decode()
            response.strip('\r')
            return response
