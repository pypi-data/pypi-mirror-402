from ika.abc import IKADevice, IKAError


class OverheadStirrerProtocol:
    """
    From the manual
    Command syntax and format:
        - commands and parameters are transmitted as capital letters
        - commands and parameters including successive parameters are seperated by at least one space (hex 0x20)
        - each individual command (including parameters and data and each response are terminated with
          Blank CR LF (hex 0x20 hex 0x0d hex 0x0A) and have a maximum length of 80 characters
        - the decimal separator in a number is a dt (hex 0x2E)
    """
    # overhead stirrer NAMUR commands
    READ_DEVICE_NAME = "IN_NAME"
    READ_PT1000 = "IN_PV_3"  # read PT1000 value - temperature from the temperature sensor
    READ_ACTUAL_SPEED = "IN_PV_4"  # current actual speed
    READ_ACTUAL_TORQUE = "IN_PV_5"  # current actual torque
    READ_SET_SPEED = "IN_SP_4"  # speed to stir at
    READ_TORQUE_LIMIT = "IN_SP_5"
    READ_SPEED_LIMIT = "IN_SP_6"
    READ_SAFETY_SPEED = "IN_SP_8"  # safety speed value
    SET_SPEED = "OUT_SP_4"  # set the speed to stir at
    SET_TORQUE_LIMIT = "OUT_SP_5"  # set the torque limit
    SET_SPEED_LIMIT = "OUT_SP_6"
    SET_SAFETY_SPEED = "OUT_SP_8"
    START_MOTOR = "START_4"  # start stirring
    STOP_MOTOR = "STOP_4"  # stop stirring
    SWITCH_TO_NORMAL_OPERATING_MODE = 'RESET'
    # todo change the direction or rotation with "OUT_MODE_n" (n = 1 or 2). doesnt seem to work with the microstar C
    SET_ROTATION_DIRECTION = "OUT_MODE_"
    READ_ROTATION_DIRECTION = "IN_MODE"  # todo doesnt seem to work with the microstar C


class OverheadStirrer(IKADevice):
    def __init__(self,
                 port: str,
                 dummy: bool = False,
                 ):
        """
        Driver for an IKA overhead stirrer
        Supported/tested models:
            - Microstar 30

        :param str, port: port to connect to the device
        """
        super().__init__(port, dummy)

    def name(self) -> str:
        n = self._send_and_receive(OverheadStirrerProtocol.READ_DEVICE_NAME)
        return n

    def temperature(self) -> float:
        """temperature from the PT1000 temperature sensor"""
        temp = self._send_and_receive(OverheadStirrerProtocol.READ_PT1000)
        return temp

    def speed(self) -> int:
        """actual stir speed"""
        s = int(self._send_and_receive(OverheadStirrerProtocol.READ_ACTUAL_SPEED))
        return s

    def torque(self) -> float:
        """torque"""
        t = self._send_and_receive(OverheadStirrerProtocol.READ_ACTUAL_TORQUE)
        return t

    def target_speed(self) -> int:
        """the set speed to stir at"""
        s = int(self._send_and_receive(OverheadStirrerProtocol.READ_SET_SPEED))
        return s

    def set_target_speed(self, value: int):
        if value < 30:
            self.logger.error('unable to set the stir speed < 30 rpm')
            raise IKAError('unable to set the stir speed < 30 rpm')

        self.logger.debug(f'set speed to stir at to {value} rpm')
        self._send(f'{OverheadStirrerProtocol.SET_SPEED} {value}')

    # # todo add setting and reading rotation direction - doesnt work with the microstar c
    # def rotation_direction(self) -> str:
    #     """
    #
    #     :return: current rotation direction. cw for clockwise, ccw for counterclockwise
    #     """
    #     # todo check what the return is
    #     rd = self._send_and_receive(OverheadStirrerProtocol.READ_ROTATION_DIRECTION)
    #     if rd == 1:
    #         return 'cw'
    #     elif rd == 2:
    #         return 'ccw'
    #     else:
    #         raise Exception('unable to read the rotation direction')
    #
    # def set_rotation_direction(self, value: str):
    #     """
    #     Set the rotation direction to either clockwise or counterclockwise
    #     :param value: cw for clockwise, ccw for counterclockwise
    #     :return:
    #     """
    #     # todo check direction setting is correct
    #     if value:
    #         direction = None
    #         if value == 'cw':
    #             self.logger.debug(f'set rotation direction to clockwise')
    #             direction = 1
    #         elif value == 'ccw':
    #             self.logger.debug(f'set rotation direction to counterclockwise')
    #             direction = 2
    #         if direction:
    #             self._send(f'{OverheadStirrerProtocol.SET_ROTATION_DIRECTION} {direction}')

    def start_stirring(self):
        """
        for some reason whenever starting stirring the set stir speed seems to be reset to 0, so just set it again
        right
        after starting stirring
        :return:
        """
        set_speed = self.target_speed()
        self._send(OverheadStirrerProtocol.START_MOTOR)
        self.set_target_speed(set_speed)

    def stop_stirring(self):
        self._send(OverheadStirrerProtocol.STOP_MOTOR)

    def switch_to_normal_operation_mode(self):
        self.logger.debug('switch to normal operation mode')
        self._send(OverheadStirrerProtocol.SWITCH_TO_NORMAL_OPERATING_MODE)

    def _send_and_receive(self,
                          command: str,
                          ):
        """
        Perform a Serial request. Write data to the device and get a response back. The response is returned
        decoded as either a string or a float value.

        String response are for the ThermoshakerProtocols:
            - READ_DEVICE_NAME
        Float response are for the ThermoshakerProtocols -
            {command} - {format of the response}
            - READ_PT1000 - #.# 3
            - READ_ACTUAL_SPEED - #.# 4
            - READ_ACTUAL_TORQUE - #.# 5
            - READ_SET_SPEED - #.# 4
            - READ_TORQUE_LIMIT - #.# 5
            - READ_SPEED_LIMIT - #.# 6
            - READ_SAFETY_SPEED - #.# 8

        :param command: one of OverheadStirrerProtocol
        :return: a string or float, depending on the appropriate response based on the data
        """
        if not self._dummy:
            response = super()._send_and_receive(command)
            if response == 'Microstar C':
                # must have asked for the device name to get back this response, so the response should be
                # returned as is (as a string)
                return response
            else:
                # must have asked for a property that is returned as a number, only return the actual value (first
                # index after splitting the string by " ") as a float
                response: float = float(response.split()[0])
            return response
