from typing import Union

from ika.abc import IKADevice, IKAError


class ChillerProtocol:
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
        pump functions are switched off in accordance with the set "watchdog" function or are changed to the set
        target values. data transmission may be interrupted by, for example, a crash in the operating system,
        a power failure in the pc, or an issue with the connection table between the computer and the device
        watchdog mode 1
            - if there is an interruption in data communications (longer than the set watchdog time), the tempering
            and pump functions are switched off and Error 2 is displayed
        watchdog mode 2
            - if there is an interruption in data communications (longer than the set watchdog time), speed target
            value is changed to the WD safety speed limit and the temperature target value is changed to the WD
            safety temperature value. error message Error 2 is displayed
    """
    # chiller NAMUR commands
    READ_INTERNAL_ACTUAL_TEMPERATURE = "IN_PV_2"  # current actual temperature
    READ_INTERNAL_SETTING_TEMPERATURE = "IN_SP_1"  # temperature to go to
    SET_INTERNAL_SETTING_TEMPERATURE = "OUT_SP_1"  # set temperature to go to to xxx: OUT_SP_1 xxx
    # set the WD-safety temperature with echo of the set defined value: OUT_SP_12@n
    SET_WATCHDOG_SAFETY_TEMPERATURE = "OUT_SP_12@"
    # start the watchdog mode 1 and set the watchdog time to n (20 to 1500) second: OUT_WD1@N
    # echos the Watchdog time. during a WD1-event, the tempering and pump functions are switched off. This command
    # needs to be sent within the watchdog time
    WATCHDOG_MODE_1 = "OUT_WD1@"
    # start the watchdog mode 2 and set the watchdog time to n (20 to 1500) second: OUT_WD2@N
    # echos the Watchdog time. during a WD2-event, the set temperature is changed to the WD safety temperature and
    # the pump set speed is set speed is set to the WD safety speed. This command needs to be sent within the watchdog
    # time
    WATCHDOG_MODE_2 = "OUT_WD2@"
    RESET = 'RESET'
    START_TEMPERING = "START_1"
    STOP_TEMPERING = "STOP_1"


class Chiller(IKADevice):
    def __init__(self,
                 port: str,
                 dummy: bool = False,
                 ):
        """
        Driver for an IKA chiller
        Supported/tested models:
            - RC 2 lite

        :param str, port: port to connect to the device
        """
        super().__init__(port, dummy)
        # track the last set watchdog safety temperature
        self._watchdog_safety_temperature: int = None

    def temperature(self) -> float:
        """internal actual temperature"""
        temp = self._send_and_receive(ChillerProtocol.READ_INTERNAL_ACTUAL_TEMPERATURE)
        return temp

    def target_temperature(self) -> float:
        """the internal setting temperature to go to"""
        temp = self._send_and_receive(ChillerProtocol.READ_INTERNAL_SETTING_TEMPERATURE)
        return temp

    def set_target_temperature(self, value):
        self.logger.debug(f'set setting temperature to {value}')
        self._send(f'{ChillerProtocol.SET_INTERNAL_SETTING_TEMPERATURE} {value}')

    def watchdog_safety_temperature(self) -> Union[int, None]:
        """the watchdog safety temperature"""
        return self._watchdog_safety_temperature

    def set_watchdog_safety_temperature(self, value: int):
        self.logger.debug(f'set watchdog safety temperature to {value}')
        self._send_and_receive(f'{ChillerProtocol.SET_WATCHDOG_SAFETY_TEMPERATURE}{value}')
        self._watchdog_safety_temperature = value

    def start_heating(self):
        self.logger.debug('start heating')
        self._send(ChillerProtocol.START_TEMPERING)

    def stop_heating(self):
        self.logger.debug('stop heating')
        self._send(ChillerProtocol.STOP_TEMPERING)

    def start_watchdog_mode_1(self, t: int):
        """
        Start watchdog mode 1 and set the time or the watchdog to t seconds (20 - 1500)
        """
        if 20 <= t <= 1500:
            self.logger.debug(f'set watchdog mode 1 with watch time {t} seconds')
            self._send_and_receive(f'{ChillerProtocol.WATCHDOG_MODE_1}{t}')
        else:
            raise IKAError('watchdog mode time must be between 20 - 1500 seconds')

    def start_watchdog_mode_2(self, t: int):
        """
        Start watchdog mode 2 and set the time or the watchdog to t seconds (20 - 1500)
        """
        if 20 <= t <= 1500:
            self.logger.debug(f'set watchdog mode 2 with watch time {t} seconds')
            self._send_and_receive(f'{ChillerProtocol.WATCHDOG_MODE_2}{t}')
        else:
            raise IKAError('watchdog mode time must be between 20 - 1500 seconds')

    def _send_and_receive(self,
                          command: str,
                          ) -> Union[str, int, float]:
        """
        Perform a Serial request. Write data to the device and get a response back. The response is returned
        decoded as either a string or a float value.

        Command - response
        READ_INTERNAL_ACTUAL_TEMPERATURE - #.# 2, where the first number is the actual temperature
        READ_INTERNAL_SETTING_TEMPERATURE - #.# 1, where the first number is the setting temperature
        SET_WATCHDOG_SAFETY_TEMPERATURE - integer, the temperature you set
        WATCHDOG_MODE_1 - integer, the time you set
        WATCHDOG_MODE_2 - integer, the time you set
        RESET -
        """
        if not self._dummy:
            response = super()._send_and_receive(command)
            try:
                # try to get the 1st index as a float
                response: float = float(response.split()[0])
            except ValueError as e:
                response = str(response)  # leave the response as a string
            return response
