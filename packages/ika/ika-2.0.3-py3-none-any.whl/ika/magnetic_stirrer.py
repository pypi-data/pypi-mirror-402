from typing import Dict

from ika.abc import IKADevice


class MagneticStirrer(IKADevice):
    # constant names are the functions, and the values are the corresponding NAMUR commands
    READ_THE_DEVICE_NAME = "IN_NAME"
    READ_ACTUAL_EXTERNAL_SENSOR_VALUE = "IN_PV_1"
    READ_ACTUAL_HOTPLATE_SENSOR_VALUE = "IN_PV_2"
    READ_STIRRING_SPEED_VALUE = "IN_PV_4"
    READ_VISCOSITY_TREND_VALUE = "IN_PV_5"
    READ_RATED_TEMPERATURE_VALUE = "IN_SP_1"
    READ_RATED_SET_SAFETY_TEMPERATURE_VALUE = "IN_SP_3"  # find the set safe temperature of the plate, the target/set
    # temperature the plate can go to is 50 degrees beneath this
    READ_RATED_SPEED_VALUE = "IN_SP_4"
    ADJUST_THE_SET_TEMPERATURE_VALUE = "OUT_SP_1"
    SET_TEMPERATURE_VALUE = "OUT_SP_1 "  # requires a value to be appended to the end of the command
    ADJUST_THE_SET_SPEED_VALUE = "OUT_SP_4"
    SET_SPEED_VALUE = "OUT_SP_4 "  # requires a value to be appended to the end of the command
    START_THE_HEATER = "START_1"
    STOP_THE_HEATER = "STOP_1"
    START_THE_MOTOR = "START_4"
    STOP_THE_MOTOR = "STOP_4"
    SWITCH_TO_NORMAL_OPERATING_MODE = "RESET"
    SET_OPERATING_MODE_A = "SET_MODE_A"
    SET_OPERATING_MODE_B = "SET_MODE_B"
    SET_OPERATING_MODE_D = "SET_MODE_D"
    SET_WD_SAFETY_LIMIT_TEMPERATURE_WITH_SET_VALUE_ECHO = "OUT_SP_12@"  # requires a value to be appended to the end of
    # the command
    SET_WD_SAFETY_LIMIT_SPEED_WITH_SET_VALUE_ECHO = "OUT_SP_42@"  # requires a value to be appended to the end of
    # the command
    WATCHDOG_MODE_1 = "OUT_WD1@"   # requires a value (bw 20-1500) to be appended to the end of the command - this is
    # the watchdog time in seconds. this command launches the watchdog function and must be transmitted within the
    # set watchdog time. in watchdog mode 1, if event WD1 occurs, the heating and stirring functions are switched off
    #  and ER 2 is displayed
    WATCHDOG_MODE_2 = "OUT_WD2@"   # requires a value (bw 20-1500) to be appended to the end of the command - this is
    # the watchdog time in seconds. this command launches the watchdog function and must be transmitted within the
    # set watchdog time. the WD2 event can be reset with the command "OUT_WD2@0", and this also stops the watchdog
    # function.  in watchdog mode 2, if event WD2 occurs, the speed target value is changed to the WD safety speed
    # limit and the temperature target value is change to the WD safety temperature limit value

    human_readable_commands: Dict[str, str] = {
        ADJUST_THE_SET_TEMPERATURE_VALUE: 'adjust the set temperature value',
        SET_TEMPERATURE_VALUE: 'set target temperature',
        ADJUST_THE_SET_SPEED_VALUE: 'adjust the set stir rate value',
        SET_SPEED_VALUE: 'set target stir rate',
        START_THE_HEATER: 'start heating',
        STOP_THE_HEATER: 'stop heating',
        START_THE_MOTOR: 'start stirring',
        STOP_THE_MOTOR: 'stop stirring',
        SWITCH_TO_NORMAL_OPERATING_MODE: 'switch to normal operating mode',
        SET_OPERATING_MODE_A: 'set operating mode a',
        SET_OPERATING_MODE_B: 'set operating mode b',
        SET_OPERATING_MODE_D: 'set operating mode d',
    }

    def __init__(self,
                 port: str,
                 dummy: bool = False,
                 ):
        super().__init__(port, dummy)

    def stir_rate(self) -> float:
        """
        Plate actual stir rate
        """
        return self._send_and_receive(command=self.READ_STIRRING_SPEED_VALUE)

    def target_stir_rate(self) -> float:
        """
        Stir rate hotplate is set to go to
        """
        return self._send_and_receive(command=self.READ_RATED_SPEED_VALUE)

    def set_target_stir_rate(self,
                             value,
                             ):
        command = self.SET_SPEED_VALUE + str(value) + ' '
        self.logger.debug(self.human_readable_commands[self.SET_SPEED_VALUE] + f' to {str(value)}')
        self._send(command=command)

    def probe_temperature(self):
        """
        read and return the temperature (degrees C) picked up by the temperature probe

        :return:
        """
        return self._send_and_receive(command=self.READ_ACTUAL_EXTERNAL_SENSOR_VALUE)

    def target_temperature(self) -> float:
        """
        read and return the temperature (degrees C) that the hotplate was set to maintain

        :return:
        """
        return self._send_and_receive(command=self.READ_RATED_TEMPERATURE_VALUE)

    def set_target_temperature(self,
                               value,
                               ):
        command = self.SET_TEMPERATURE_VALUE + str(value) + ' '
        command_str = self.human_readable_commands[self.SET_TEMPERATURE_VALUE] + f' to {str(value)}'
        self.logger.debug(command_str)
        self._send(command=command)

    def hotplate_sensor_temperature(self) -> float:
        """
        read and return the value (degrees C) that the hotplate itself is at

        :return:
        """
        return self._send_and_receive(command=self.READ_ACTUAL_HOTPLATE_SENSOR_VALUE)

    def hardware_safety_temperature(self):
        return self._send_and_receive(command=self.READ_RATED_SET_SAFETY_TEMPERATURE_VALUE)

    def viscosity_trend(self):
        """
        The viscosity trend

        :return:
        """
        return self._send_and_receive(command=self.READ_VISCOSITY_TREND_VALUE)

    def read_device_name(self):
        return self._send_and_receive(command=self.READ_THE_DEVICE_NAME)

    def adjust_the_set_temperature_value(self):
        self._send(command=self.ADJUST_THE_SET_TEMPERATURE_VALUE)

    def adjust_the_set_speed_value(self):
        self._send(command=self.ADJUST_THE_SET_SPEED_VALUE)

    def start_heating(self):
        self.logger.debug(self.human_readable_commands[self.START_THE_HEATER])
        self._send(command=self.START_THE_HEATER)

    def stop_heating(self):
        self.logger.debug(self.human_readable_commands[self.STOP_THE_HEATER])
        self._send(command=self.STOP_THE_HEATER)

    def start_stirring(self):
        self.logger.debug(self.human_readable_commands[self.START_THE_MOTOR])
        self._send(command=self.START_THE_MOTOR)

    def stop_stirring(self):
        self.logger.debug(self.human_readable_commands[self.STOP_THE_MOTOR])
        self._send(command=self.STOP_THE_MOTOR)

    def switch_to_normal_operating_mode(self):
        self.logger.debug(self.human_readable_commands[self.SWITCH_TO_NORMAL_OPERATING_MODE])
        self._send(command=self.SWITCH_TO_NORMAL_OPERATING_MODE)

    def set_operating_mode_a(self):
        self.logger.debug(self.human_readable_commands[self.SET_OPERATING_MODE_A])
        self._send(command=self.SET_OPERATING_MODE_A)

    def set_operating_mode_b(self):
        self.logger.debug(self.human_readable_commands[self.SET_OPERATING_MODE_B])
        self._send(command=self.SET_OPERATING_MODE_B)

    def set_operating_mode_d(self):
        command_str = self.human_readable_commands[self.SET_OPERATING_MODE_D]
        self.logger.debug(command_str)
        self._send(command=self.SET_OPERATING_MODE_D)

    def set_wd_safety_limit_temperature(self,
                                        value: str,
                                        ):
        command = self.SET_WD_SAFETY_LIMIT_TEMPERATURE_WITH_SET_VALUE_ECHO + value + ' '
        return self._send_and_receive(command=command)

    def set_wd_safety_limit_speed(self,
                                  value,
                                  ):
        command = self.SET_WD_SAFETY_LIMIT_SPEED_WITH_SET_VALUE_ECHO + str(value) + ' '
        return self._send_and_receive(command=command)

    def watchdog_mode_1(self,
                        value,
                        ):
        """
        This command launches the watchdog function and must be transmitted within the set watchdog time.
        in watchdog mode 1, if event WD1 occurs, the heating and stirring functions are switched off and ER 2 is
        displayed

        :param value: value between 20 and 1500 (units in seconds) - the watchdog time

        :return:
        """
        command = self.WATCHDOG_MODE_1 + str(value) + ' '
        self._send(command=command)

    def watchdog_mode_2(self,
                        value: str,
                        ):
        """
        This command launches the watchdog function and must be transmitted within the set watchdog time. the WD2
        event can be reset with the command "OUT_WD2@0", and this also stops the watchdog function.  in watchdog mode
        2, if event WD2 occurs, the speed target value is changed to the WD safety speed limit and the temperature
        target value is change to the WD safety temperature limit value

        :param value: value between 20 and 1500 (units in seconds) - the watchdog time

        :return:
        """
        command = self.WATCHDOG_MODE_2 + value + ' '
        self._send(command=command)

    def _send_and_receive(self,
                          command: str,
                          ):
        """
        Send a command, get a response back, and return the response
        :param str, command: a command that will give back a response - these will be:
            READ_THE_DEVICE_NAME
            READ_ACTUAL_EXTERNAL_SENSOR_VALUE
            READ_ACTUAL_HOTPLATE_SENSOR_VALUE
            READ_STIRRING_SPEED_VALUE
            READ_VISCOSITY_TREND_VALUE
            READ_RATED_TEMPERATURE_VALUE
            READ_RATE_SET_SAFETY_TEMPERATURE_VALUE
            READ_RATE_SPEED_VALUE

        :return:
        """
        if not self._dummy:
            response = super()._send_and_receive(command)
            # all the functions that would use this function, except when asking for the device name, returns a number.
            # however the return string type for all the other functions is a string of the type '#.# #', so we want to
            # change that into a float instead so it can be easily used
            if response == 'C-MAG HS7':
                return 'C-MAG HS7'
            elif response == 'RCT digital':
                return 'RCT digital'
            else:
                formatted_return_float = float(response.split()[0])  # return just the information we want as a float
            return formatted_return_float
