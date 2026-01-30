from typing import Union
from enum import Enum

from ika.abc import IKADevice, IKAError


class VacuumProtocol:
    """
    From the manual
    Command syntax and format:
        - Transmission process: Asynchronous character transmission in start-stop operation.
        - Transmission type: Full duplex.
        - Character format: Character composition according to data format in DIN 66022 for start-stop operation. 1
            start bit, 7 character bits, 1 parity bit (even), 1 stop bit.
        - Transmission speed: 9600 Bits/s.
        - Data flow control: none
        - Access method: Data transmission from the device to the computer only occurs after a _request from the
          computer.
        - The device only responds to requests from the computer. Even error messages are not send spontaneously from
          the device to the computer (automation system).
        - The commands are transmitted in captial letters.
        - Commands and parameters, as well as consecutive parameters, must be separated by at least one
            space (code: hex 0x20).
        - Each individual command (including parameters and data) and all responses are completed with
            CRLF (code: hex 0x20 hex 0x0d hex 0x0A) and can have a maximum length of 50 characters.
        - The dot is used for decimal separators in a floating-point value
(code: hex 0x2E).
    About watchdog:
        watchdog functions monitors the serial data flow. if, once this function has been activated there is no
        retransmission of the command from the computer within the set time ("watchog time:), the Evacuation function
        is switched off in accordance with the set “watchdog” mode or is returned to previously set target values.
        The data transmission may be interrupted by, for example, a crash in the operating system, a power failure in
        the PC or an issue with the connection cable between the computer and the device.
        watchdog mode 1
            - If event WD1 should occur, the evacuation function is switched off and WD1 Watchdog Error is displayed.
              Set watchdog time to m (20 - 1,500) seconds, with watchdog time echo. This command launches the
              watchdog function
        watchdog mode 2
            - If there is an interruption in data communications (longer than the set watchdog time),
              the speed target value is changed to the set WD safety speed limit. The warning PC 2 is displayed. The
              WD2 event can be reset with OUT_WD2@0 - this also stops the watchdog function. Set watchdog time to m
              (20 - 1,500) seconds, with watchdog time echo. This command launches the watchdog function and must be
              transmitted within the set watchdog time.
    """
    # vacuum NAMUR commands - for firmware version 0.0.020
    READ_ACTUAL_VALUES = "IN_PARA1"
    SET_VALUES = "OUT_PARA1"  # set the set values for the pump control
    SET_BLUETOOTH = "OUT_PARA2"  # set the set values for Bluetooth connection
    SEND_DEVICE_STATUS = "OUT_STATUS"  # send the actual device status
    READ_DEVICE_STATUS = "IN_STATUS"
    READ_FIRMWARE_VERSION = "IN_VERSION"
    READ_FIRMWARE_DATE = "IN_DATE"  # Read the release date of the display/logic firmware
    READ_DEVICE_NAME = "IN_NAME"
    READ_DEVICE_TYPE = "IN_DEVICE"
    READ_MAC_ADDRESS = "IN_ADDRESS"  # Read mac address of Wico
    READ_PAIRED_MAC_ADDRESS = "IN_PAIRING"  # Read paired mac address of station.
    SET_PAIRED_MAC_ADDRESSES = "OUT_ADDRESS"  # Write new paired mac addresses of both station and Wico
    READ_SET_PRESSURE = "IN_SP_66"  # Reads the set pressure value
    SET_PRESSURE = "OUT_SP_66"  # Sets set point pressure value
    READ_PRESSURE = "IN_PV_66"  # Reads the actual pressure value
    READ_EVACUATING_MODE = "IN_MODE_66"
    SET_EVACUATING_MODE = "OUT_MODE_66"
    READ_ERROR = "IN_ERROR"  # Reads error state
    TEST_ERROR = "OUT_ERROR"  # Test Error. Sends out error code
    READ_BLUETOOTH_DEVICE_NAME = "IN_BT_NAME"
    READ_CUSTOM_DEVICE_NAME = "IN_CUSTOM_DEVICE_NAME"
    SET_CUSTOM_DEVICE_NAME = "OUT_CUSTOM_DEVICE_NAME"
    READ_WATCHDOG_MODE_1_TIME = "IN_WD1@"  # reads communication watchdog time
    WATCHDOG_MODE_1 = "OUT_WD1@"  # Sets communication watchdog time
    WATCHDOG_MODE_2 = "OUT_WD2@"  # Set PC communication watchdog time 2
    SET_PC_SAFETY_PUMP_RATE = "OUT_SP_41"  # OUT_SP_41 n (0 - 100 %)
    SET_PC_SAFETY_PRESSURE = "OUT_SP_42"
    SWITCH_TO_NORMAL_OPERATING_MODE = "RESET"
    START = "START_66"  # Starts the measurement
    STOP = "STOP_66"  # Stops the measurement
    # not working
    START_IAP_MODE = "ENTER_IAP"
    CALIBRATE_VACUUM = "CALIB_66"  # It is used to calibrate vacuum.
    READ_VACUUM_CALIBRATION = "IN_CALIB_66"  # read vacuum calibration values
    CALIBRATE_VACUUM_2 = "OUT_CALIB_66"  # It is used to calibrate vacuum.


class DeviceErrors:
    """
    From the manual.
    Error codes from the device
    """
    # Device temperature error. The temperature of device has exceeded the limit. Action - Stop the device for a while
    # and restart again. If the problem occurs again and again, please call service department.
    ERROR_3 = "Error 3"
    # Motor overload - The motor is blocked because of overload. Action -  Stop the device for a while and restart
    # again. If the problem occurs again and again, please call service department.
    ERROR_4 = "Error 4"
    # Speed sensor fault. Device can’t detect the pump speed. The sensor occurs some unknown errors that device
    # can’t read the speed value. Action - Call service department
    ERROR_8 = "Error 8"
    # Storage Error. Read or _write internal flash error. Action - Call service department
    ERROR_9 = "Error 9"


class EvacuatingMode(Enum):
    """
    Modes
        Automatic: In the “Modes” menu, you can enable automatic boiling point recognition
            by selecting the “Automatic” menu item. No other parameters
            must be set. The boiling point is detected automatically. For rotary
            evaporators with heating bath, it must be ensured that the tempering
            medium and solvents have a constant temperature (e.g. 60 °C).
        Manual:
            In the “Manual” menu item, the target value can be specified (e.g.
            in "mbar”). The system is evacuated until the target value.
        Pump %:
            By selecting the “Pump %” menu item, the pump can be operated
            continuously with a running performance of between 100 % and 1 %.
        Program
            Under the “Program” menu, 10 user-defined pressure-time profiles
            can be created. The last measurement which is in manual mode can
            be saved as a program. The target value and the running performance
            can only be entered within the set limits (see menu item “Limits”)
            switching to the working screen and pressing the rotary/push
            knob starts the process. Pressing the knob again stops the process.
    """
    AUTOMATIC = 0
    MANUAL = 1
    PERCENT = 2
    PROGRAM = 3


class VacuumPump(IKADevice):
    def __init__(self,
                 port: str,
                 dummy: bool = False,
                 ):
        """
        Driver for an IKA vacuum pump
        Supported/tested models:
            - VACSTAR control

        :param str, port: port to connect to the device
        """
        super().__init__(port, dummy)
        # track the last set watchdog safety temperature
        self._watchdog_safety_pressure: int = None
        self._watchdog_safety_pump_rate: int = None

    def name(self) -> str:
        n = self._send_and_receive(VacuumProtocol.READ_DEVICE_NAME)
        return n

    def device_type(self) -> str:
        t = self._send_and_receive(VacuumProtocol.READ_DEVICE_TYPE)
        return t

    def firmware_version(self) -> str:
        sv = self._send_and_receive(VacuumProtocol.READ_FIRMWARE_VERSION)
        return sv

    def firmware_version_date(self) -> str:
        """the release date of the display/logic firmware"""
        siv = self._send_and_receive(VacuumProtocol.READ_FIRMWARE_DATE)
        return siv

    def mac_address(self):
        """ mac address of Wico"""
        ma = self._send_and_receive(VacuumProtocol.READ_MAC_ADDRESS)
        return ma

    def paired_mac_address(self):
        """paired mac address of station"""
        ma = self._send_and_receive(VacuumProtocol.READ_PAIRED_MAC_ADDRESS)
        return ma

    def pressure(self) -> float:
        """actual pressure"""
        p = int(self._send_and_receive(VacuumProtocol.READ_PRESSURE))
        return p

    def target_pressure(self) -> float:
        """the set point pressure to go to, mbar"""
        sp = self._send_and_receive(VacuumProtocol.READ_SET_PRESSURE)
        return int(sp)

    def set_target_pressure(self, value: int):
        self.logger.debug(f'set the set pressure to {value} mbar')
        self._send(f'{VacuumProtocol.SET_PRESSURE} {value}')

    def evacuating_mode(self) -> EvacuatingMode:
        """
        Modes
        Automatic: In the “Modes” menu, you can enable automatic boiling point recognition
            by selecting the “Automatic” menu item. No other parameters
            must be set. The boiling point is detected automatically. For rotary
            evaporators with heating bath, it must be ensured that the tempering
            medium and solvents have a constant temperature (e.g. 60 °C).
        Manual:
            In the “Manual” menu item, the target value can be specified (e.g.
            in "mbar”). The system is evacuated until the target value.
        Pump %:
            By selecting the “Pump %” menu item, the pump can be operated
            continuously with a running performance of between 100 % and 1 %.
        Program
            Under the “Program” menu, 10 user-defined pressure-time profiles
            can be created. The last measurement which is in manual mode can
            be saved as a program. The target value and the running performance
            can only be entered within the set limits (see menu item “Limits”)
            switching to the working screen and pressing the rotary/push
            knob starts the process. Pressing the knob again stops the process.
        """
        em = self._send_and_receive(VacuumProtocol.READ_EVACUATING_MODE)
        em = EvacuatingMode(em)
        return em

    def set_evacuating_mode(self, value: Union[EvacuatingMode, int]):
        if type(value) != EvacuatingMode:
            value = EvacuatingMode(value)
        self.logger.debug(f'set evacuating mode to {value.name}')
        self._send_and_receive(f'{VacuumProtocol.SET_EVACUATING_MODE} {value.value}')

    def watchdog_communication_time(self):
        """reads communication watchdog time"""
        t = self._send_and_receive(VacuumProtocol.READ_WATCHDOG_MODE_1_TIME)
        return float(t)

    def watchdog_safety_pump_rate(self) -> Union[int, None]:
        """the last set watchdog safety pump rate"""
        return self._watchdog_safety_pump_rate

    # havent actually tested this
    def set_watchdog_safety_pump_rate(self, value: int):
        """ set the safety pump rate, 0 - 100 %"""
        value = int(value)
        self.logger.debug(f'set the watchdog safety pump rate to {value}')
        self._send(f'{VacuumProtocol.SET_PC_SAFETY_PUMP_RATE} {value}')
        self._watchdog_safety_pump_rate = value

    # # technically should work, just not sure what the units are
    # def watchdog_safety_pressure(self) -> Union[int, None]:
    #     """the last set watchdog safety pressure"""
    #     return self._watchdog_safety_pressure
    #
    # def set_watchdog_safety_pressure(self, value):
    #     """ set the safety pump pressure"""
    #     if value is not None:
    #         value = int(value)
    #         self.logger.debug(f'set the watchdog safety pump pressure to {value}')
    #         self._send(f'{VacuumProtocol.SET_PC_SAFETY_PRESSURE} {value}')
    #         self._watchdog_safety_pressure = value

    def start_watchdog_mode_1(self, t: int):
        """
        Start watchdog mode 1 and set the time or the watchdog to t seconds (20 - 1500)
        """
        if 20 <= t <= 1500:
            self.logger.debug(f'set watchdog mode 1 with watch time {t} seconds')
            self._send_and_receive(f'{VacuumProtocol.WATCHDOG_MODE_1}{t}')
        else:
            raise IKAError('watchdog mode time must be between 20 - 1500 seconds')

    # # doesnt seem to be working
    # def start_watchdog_mode_2(self, t: int):
    #     """
    #     Start watchdog mode 2 and set the time or the watchdog to t seconds (20 - 1500)
    #     """
    #     if 20 <= t <= 1500:
    #         self.logger.debug(f'set watchdog mode 2 with watch time {t} seconds')
    #         self._send(f'{VacuumProtocol.WATCHDOG_MODE_2}{t}')
    #     else:
    #         raise IKAError('watchdog mode time must be between 20 - 1500 seconds')

    def start(self):
        self.logger.debug('start measurement')
        self._send(VacuumProtocol.START)

    def stop(self):
        self.logger.debug('stop measurement')
        self._send(VacuumProtocol.STOP)

    # # not working
    # def start_iap_mode(self):
    #     self.logger.debug('start IAP mode')
    #     self._send_and_receive(VacuumProtocol.START_IAP_MODE)

    def switch_to_normal_operation_mode(self):
        self.logger.debug('switch to normal operation mode')
        self._send_and_receive(VacuumProtocol.SWITCH_TO_NORMAL_OPERATING_MODE)

    def read_error(self):
        self.logger.debug('read the error state')
        e = self._send_and_receive(VacuumProtocol.READ_ERROR)
        return e

    def _send_and_receive(self,
                          command: str,
                          ) -> Union[str, int, float]:
        """
        Perform a Serial request. Write data to the device and get a response back. The response is returned
        decoded as either a string or a float value.

        Command - response
        READ_DEVICE_NAME - str, "VACSTAR Control"
        READ_DEVICE_TYPE - str, "IN_DEVICE VACSTAR Control"
        READ_FIRMWARE_VERSION - str, "IN_VERSION 1.1.011"
        READ_FIRMWARE_DATE - str, "IN_DATE 04/03/19"
        READ_MAC_ADDRESS - str, "IN_ADDRESS 68:27:19:F9:1B:36"
        READ_PAIRED_MAC_ADDRESS - str, "IN_PAIRING 68:27:19:F9:18:59"
        SWITCH_TO_NORMAL_OPERATING_MODE - str, "RESET"

        READ_SET_PRESSURE - IN_SP_66 ####.#
        READ_PRESSURE - IN_PV_66 ####.#
        READ_EVACUATING_MODE - IN_MODE_66 #
        READ_DEVICE_STATUS - IN_STATUS #####
        WATCHDOG_MODE_1 - 'OUT_SP_41 #'
        READ_WATCHDOG_MODE_1_TIME - '#'

        SET_EVACUATING_MODE - OUT_MODE_66 #

        START - None
        STOP - None
        RESET - None (? check)

        START_IAP_MODE - not working!
        WATCHDOG_MODE_2 - not working!
        :return: a string or float, depending on the appropriate response based on the data
        """
        if not self._dummy:
            response = super()._send_and_receive(command)
            if command == VacuumProtocol.READ_DEVICE_NAME or command == VacuumProtocol.SWITCH_TO_NORMAL_OPERATING_MODE:
                return response
            elif command == VacuumProtocol.READ_DEVICE_TYPE:
                return f'{response.split()[1]} {response.split()[2]}'
            elif command == VacuumProtocol.READ_DEVICE_TYPE or command == \
                    VacuumProtocol.READ_FIRMWARE_VERSION or command == VacuumProtocol.READ_FIRMWARE_DATE or command == \
                    VacuumProtocol.SWITCH_TO_NORMAL_OPERATING_MODE or command == VacuumProtocol.READ_MAC_ADDRESS or \
                    command == VacuumProtocol.READ_PAIRED_MAC_ADDRESS:
                return response.split()[1]
            try:
                # try to get the 1st index as a float
                response: float = float(response.split()[1])
            except ValueError as e:
                response = str(response)  # leave the response as a string
            return response