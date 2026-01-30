
from typing import Union

from ika.abc import IKADevice, IKAError


class ThermoshakerProtocol:
    """
    From the manual
    Command syntax and format:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are seperated by at least one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated with
          Blank CR LF (hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    About watchdog:
        watchdog functions monitors the serial data flow. if, once this function has been activated there is no
        retransmission of the command from the computer within the set time ("watchog time:), the tempering and
        mixing functions are switched off in accordance with the set "watchdog" function or are changed to the set
        target values. data transmission may be interrupted by, for example, a crash in the operating system,
        a power failure in the pc, or an issue with the connection table between the computer and the device
        watchdog mode 1
            - if there is an interruption in data communications (longer than the set watchdog time), the tempering
            functions are switched off and Error 2 is displayed
        watchdog mode 2
            - if there is an interruption in data communications (longer than the set watchdog time), the temperature
            target value is changed to the WD safety temperature value. error message Error 2 is displayed
    """
    # thermoshaker NAMUR commands
    READ_ACTUAL_TEMPERATURE = "IN_PV_2"  # current actual temperature
    READ_ACTUAL_SPEED = "IN_PV_4"  # current actual shake speed
    READ_SET_TEMPERATURE = "IN_SP_2"  # temperature to go to
    READ_SET_SPEED = "IN_SP_4"  # speed to shake at
    SET_TEMPERATURE = "OUT_SP_2"  # set temperature to go to to xxx: OUT_SP_2 xxx
    SET_SPEED = "OUT_SP_4"  # set speed to shake at to xxx: OUT_SP_4 xxx
    # set the WD-safety temperature with echo of the set defined value: OUT_SP_12@n
    SET_WATCHDOG_SAFETY_TEMPERATURE = "OUT_SP_12@"
    # start the watchdog mode 1 and set the watchdog time to n (20 to 1500) second: OUT_WD1@N
    # echos the Watchdog time. during a WD1-event, the tempering functions are switched off. This command
    # needs to be sent within the watchdog time
    WATCHDOG_MODE_1 = "OUT_WD1@"
    # start the watchdog mode 2 and set the watchdog time to n (20 to 1500) second: OUT_WD2@N
    # echos the Watchdog time. during a WD2-event, the set temperature is changed to the WD safety temperature. This
    # command needs to be sent within the watchdog time
    WATCHDOG_MODE_2 = "OUT_WD2@"
    SWITCH_TO_NORMAL_OPERATING_MODE = 'RESET'
    START_TEMPERING = "START_2"
    STOP_TEMPERING = "STOP_2"
    START_MOTOR = "START_4"
    STOP_MOTOR = "STOP_4"
    READ_SOFTWARE_VERSION = 'IN_VERSION'
    READ_SOFTWARE_ID_AND_VERSION = 'IN_SOFTWARE_ID'


class Thermoshaker(IKADevice):
    def __init__(self,
                 port: str,
                 dummy: bool = False,
                 termination_character: bytes = b'\r'
                 ):
        """
        Supported/tested models:
            - MATRIX ORBITAL Delta Plus
        """
        super().__init__(port, dummy, termination_character)
        # track the last set watchdog safety temperature
        self._watchdog_safety_temperature: float = None

    def temperature(self) -> float:
        """actual temperature"""
        temp = self._send_and_receive(ThermoshakerProtocol.READ_ACTUAL_TEMPERATURE)
        return temp

    def target_temperature(self) -> float:
        """the set temperature to go to"""
        temp = self._send_and_receive(ThermoshakerProtocol.READ_SET_TEMPERATURE)
        return temp

    def set_target_temperature(self, value):
        self.logger.debug(f'set temperature to go to to {value}')
        self._send_and_receive(f'{ThermoshakerProtocol.SET_TEMPERATURE} {value}')

    def speed(self) -> float:
        """actual shake speed"""
        s = self._send_and_receive(ThermoshakerProtocol.READ_ACTUAL_SPEED)
        return s

    def target_speed(self) -> float:
        """the set speed to shake at"""
        s = self._send_and_receive(ThermoshakerProtocol.READ_SET_SPEED)
        return s

    def set_target_speed(self, value):
        self.logger.debug(f'set speed to shake at to {value} rpm')
        self._send_and_receive(f'{ThermoshakerProtocol.SET_SPEED} {value}')

    def watchdog_safety_temperature(self) -> Union[float, None]:
        """the watchdog safety temperature"""
        return self._watchdog_safety_temperature

    def set_watchdog_safety_temperature(self, value):
        self.logger.debug(f'set watchdog safety temperature to {value}')
        self._send_and_receive(f'{ThermoshakerProtocol.SET_WATCHDOG_SAFETY_TEMPERATURE}{value}')
        self._watchdog_safety_temperature = value

    def software_version(self) -> str:
        sv = self._send_and_receive(ThermoshakerProtocol.READ_SOFTWARE_VERSION)
        return sv

    def software_id_and_version(self) -> str:
        siv = self._send_and_receive(ThermoshakerProtocol.READ_SOFTWARE_ID_AND_VERSION)
        return siv

    def start_heating(self):
        self.logger.debug('start heating')
        self._send_and_receive(ThermoshakerProtocol.START_TEMPERING)

    def stop_heating(self):
        self.logger.debug('stop tempering')
        self._send_and_receive(ThermoshakerProtocol.STOP_TEMPERING)

    def start_shaking(self):
        self.logger.debug('start shaking')
        self._send_and_receive(ThermoshakerProtocol.START_MOTOR)

    def stop_shaking(self):
        self.logger.debug('stop shaking')
        self._send_and_receive(ThermoshakerProtocol.STOP_MOTOR)

    def start_watchdog_mode_1(self, t: int):
        """
        Start watchdog mode 1 and set the time or the watchdog to t seconds (20 - 1500)
        """
        if 20 <= t <= 1500:
            self.logger.debug(f'set watchdog mode 1 with watch time {t} seconds')
            self._send_and_receive(f'{ThermoshakerProtocol.WATCHDOG_MODE_1}{t}')
        else:
            raise IKAError('watchdog mode time must be between 20 - 1500 seconds')

    def start_watchdog_mode_2(self, t: int):
        """
        Start watchdog mode 2 and set the time or the watchdog to t seconds (20 - 1500)
        """
        if 20 <= t <= 1500:
            self.logger.debug(f'set watchdog mode 2 with watch time {t} seconds')
            self._send_and_receive(f'{ThermoshakerProtocol.WATCHDOG_MODE_2}{t}')
        else:
            raise IKAError('watchdog mode time must be between 20 - 1500 seconds')

    def switch_to_normal_operation_mode(self):
        """the concrete class should call this abstract method then continue with its implementation"""
        self.logger.debug('switch to normal operation mode')
        self._send_and_receive(ThermoshakerProtocol.SWITCH_TO_NORMAL_OPERATING_MODE)

    def _send_and_receive(self,
                          command: str,
                          ):
        """
        Perform a Serial request. Write data to the device and get a response back. The response is returned decoded
        as either a string or a float value.

        String response are for the ThermoshakerProtocols:
            - READ_SOFTWARE_VERSION
            - READ_SOFTWARE_ID_AND_VERSION
        Float response are for the ThermoshakerProtocols:
            - READ_ACTUAL_TEMPERATURE
            - READ_ACTUAL_SPEED
            - READ_SET_TEMPERATURE
            - READ_SET_SPEED
            - SET_WATCHDOG_SAFETY_TEMPERATURE

        :return: a string or float, depending on the appropriate response based on the data
        """
        if not self._dummy:
            response = super()._send_and_receive(command)
            # the response except when asking for the software version or software version and id returns a number in
            # the format is '#.#.#' for software version and '#;#.#.#' for id and software version
            # the response when getting back a float value is {serial command #.#}. except when setting the
            # watchdog safety temperature, that response is just a float value (#.#), and when starting watchdog mode
            # 1 or 2, that response is just an integer value
            # So first try to return the response as if the 1st index item after splitting the response by a white space
            # is a float, and if that doesnt work then return the response as if the 0th index item after splitting the
            # response by a white space is a float, and if that doesnt work then return the response as a string
            try:
                # try to get the 1st index as a float
                response: float = float(response.split()[1])
            except IndexError as e:
                # try to get the 0th index as a float
                try:
                    response: float = float(response.split()[0])
                except ValueError as e:
                    # response must be a string so just return the string
                    pass
            return response
