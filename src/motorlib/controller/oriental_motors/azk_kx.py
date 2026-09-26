import logging
import time
from enum import IntFlag
from typing import Literal, override

import pint
import reactivex as rx
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler

from ...configuration import DeviceConfig
from ..base_controller import ContinuousMode
from ..connection import ModbusSerialConnection
from .oriental_motors_base import OrientalMotorsBaseController

poll_scheduler = ThreadPoolScheduler(1)


class AZKKXController(OrientalMotorsBaseController):
    class InputSignal(IntFlag):
        M0 = 1 << 0
        M1 = 1 << 1
        M2 = 1 << 2
        START = 1 << 3
        ZHOME = 1 << 4
        STOP = 1 << 5
        ALARM_RESET = 1 << 7
        FORWARD = 1 << 14
        BACKWARD = 1 << 15

    class OutputSignal(IntFlag):
        M0_R = 1 << 0
        M1_R = 1 << 1
        M2_R = 1 << 2
        START_R = 1 << 3
        HOME_END = 1 << 4
        READY = 1 << 5
        INFO = 1 << 6
        ALARM = 1 << 7
        MOVE = 1 << 13
        IN_POS = 1 << 14

        def is_ready(self) -> bool:
            return (
                self & AZKKXController.OutputSignal.READY
            ) == AZKKXController.OutputSignal.READY

        def is_moving(self) -> bool:
            return (
                self & AZKKXController.OutputSignal.MOVE
            ) == AZKKXController.OutputSignal.MOVE

        def is_in_pos(self) -> bool:
            return (
                self & AZKKXController.OutputSignal.IN_POS
            ) == AZKKXController.OutputSignal.IN_POS

        def is_alarm(self) -> bool:
            return (
                self & AZKKXController.OutputSignal.ALARM
            ) == AZKKXController.OutputSignal.ALARM

    def __init__(self, connection: ModbusSerialConnection, device_config: DeviceConfig):
        super().__init__(connection)
        self.device_config = device_config

    def get_status_bits(self) -> OutputSignal:
        """Get the status bits of the motor."""
        status_bits = self._get_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x007E,
        )
        return AZKKXController.OutputSignal(status_bits)

    @override
    def get_status(self) -> dict[str, bool]:
        """Get the status of the motor as a dictionary of boolean flags."""
        status_bits = self.get_status_bits()
        return {
            'M0_R': bool(status_bits & AZKKXController.OutputSignal.M0_R),
            'M1_R': bool(status_bits & AZKKXController.OutputSignal.M1_R),
            'M2_R': bool(status_bits & AZKKXController.OutputSignal.M2_R),
            'START_R': bool(status_bits & AZKKXController.OutputSignal.START_R),
            'HOME_END': bool(status_bits & AZKKXController.OutputSignal.HOME_END),
            'READY': bool(status_bits & AZKKXController.OutputSignal.READY),
            'INFO': bool(status_bits & AZKKXController.OutputSignal.INFO),
            'ALARM': bool(status_bits & AZKKXController.OutputSignal.ALARM),
            'MOVE': bool(status_bits & AZKKXController.OutputSignal.MOVE),
            'IN_POS': bool(status_bits & AZKKXController.OutputSignal.IN_POS),
        }

    @override
    def alarm_reset(self):
        """Reset the alarm of the motor."""
        logger = logging.getLogger(__name__)
        logger.info('Resetting motor alarm...')

        # check if the motor is in alarm state
        if not self.get_status_bits().is_alarm():
            logger.info('Motor is not in alarm state. No reset needed.')
            return

        # set the ALARM_RESET register to 1 to reset the alarm (first reset to 0, then set to 1)
        logger.debug('Setting ALARM_RESET register to 1 to reset the alarm...')
        self._set_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x0180,
            value=0,
        ).result()
        self._set_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x0180,
            value=1,
        ).result()

        # wait until READY is turned off, indicating that the motor has started resetting
        logger.debug('Waiting for motor to start resetting...')
        while not self.get_status_bits().is_ready():
            time.sleep(0.05)

        logger.info('Motor alarm reset successfully.')

    @override
    def home(self):
        """Home the motor."""
        logger = logging.getLogger(__name__)
        logger.info('Homing motor...')

        # check if the motor is ready to home
        if not self.get_status_bits().is_ready():
            raise RuntimeError('Motor is not ready to home.')

        # set the HOME bit to 1 to start homing
        logger.debug('Setting ZHOME bit to 1 to start homing...')
        self._set_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x007C,
            value=self.InputSignal.ZHOME,
        ).result()

        # wait until READY is turned off, indicating that the motor has started homing
        logger.debug('Waiting for motor to start homing...')
        while self.get_status_bits().is_ready():
            time.sleep(0.05)

        # reset the ZHOME_P bit to 0
        logger.debug('Resetting ZHOME_P bit to 0...')
        self._set_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x007C,
            value=0,
        ).result()

        # wait until motor reaches the home position by checking the HOME-END bit in the status register
        logger.debug('Waiting for motor to reach home position...')
        while True:
            position = self.get_position()
            logger.info(f'Current position: {position}')
            status = self.get_status_bits()
            if (
                status & AZKKXController.OutputSignal.HOME_END
            ) == AZKKXController.OutputSignal.HOME_END:
                break
            time.sleep(0.05)

        position = self.get_position()
        logger.info(f'Motor homed. Current position: {position}')

    @override
    def get_position(self) -> pint.Quantity:
        """Get the current position of the motor."""
        position = self._get_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x00C6,
        )

        logger = logging.getLogger(__name__)
        logger.debug(f'Current position (steps): {position}')

        resolution = self.device_config.resolution
        return position / resolution

    @override
    def move_by(
        self,
        distance: pint.Quantity,
    ):
        self._move(distance, mode='incremental')

    @override
    def move_to(
        self,
        position: pint.Quantity,
    ):
        self._move(position, mode='absolute')

    @override
    def _move(
        self,
        distance: pint.Quantity,
        mode: Literal['absolute', 'incremental'] = 'incremental',
    ):
        """Move the motor by the specified distance."""
        logger = logging.getLogger(__name__)

        # check if the motor is ready to move
        if not self.get_status_bits().is_ready():
            raise RuntimeError('Motor is not ready to move.')
        logger.info(f'Moving motor by {distance:.3f~P}...')

        # write operation data to the appropriate holding registers
        logger.debug(f'Setting operation data for move by {distance:.3f~P}...')
        self.set_operation_data(
            operation_number=0,
            position=distance,
            speed=self.device_config.speed,
            mode=mode,
        )

        # start move operation by setting the START and M0 bits in the input signal register
        logger.debug('Starting move operation by setting START and M0 bits...')
        self._set_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x007C,
            value=self.InputSignal.START,
        ).result()

        # wait until READY is turned off, indicating that the motor has started moving
        logger.debug('Waiting for motor to start moving...')
        while self.get_status_bits().is_ready():
            time.sleep(0.05)

        # reset the START and M0 bits in the input signal register
        logger.debug('Resetting START and M0 bits...')
        self._set_register_int32(
            unit_address=self.device_config.unitAddress,
            register_address=0x007C,
            value=0,
        ).result()

        # wait until motor reaches the target position by checking the IN_POS bit in the status register
        logger.info('Waiting for motor to reach target position...')
        while True:
            current_position = self.get_position()
            logger.info(f'Current position: {current_position:.3f~P}')
            status = self.get_status_bits()
            if status.is_alarm():
                raise RuntimeError('Motor alarm occurred during move operation.')
            if status.is_ready():
                break
            time.sleep(0.05)

    def continuous(
        self,
        commands: rx.Observable[ContinuousMode],
    ):
        logger = logging.getLogger(__name__)

        # setup operation data for continuous movement
        self.set_operation_data(
            operation_number=0,
            speed=self.device_config.speed,
        )
        self.set_operation_data(
            operation_number=1,
            speed=self.device_config.crawl,
        )
        self.set_operation_data(
            operation_number=2,
            speed=self.device_config.fast,
        )

        def set_motor(mode: ContinuousMode):
            """Set the motor to the specified mode."""
            if mode == ContinuousMode.FORWARD:
                logger.debug('Setting motor to FORWARD...')
                value = AZKKXController.InputSignal.FORWARD
            elif mode == ContinuousMode.BACKWARD:
                logger.debug('Setting motor to BACKWARD...')
                value = AZKKXController.InputSignal.BACKWARD
            elif mode == ContinuousMode.CRAWL_FORWARD:
                logger.debug('Setting motor to CRAWL_FORWARD...')
                value = (
                    AZKKXController.InputSignal.FORWARD | AZKKXController.InputSignal.M0
                )
            elif mode == ContinuousMode.CRAWL_BACKWARD:
                logger.debug('Setting motor to CRAWL_BACKWARD...')
                value = (
                    AZKKXController.InputSignal.BACKWARD
                    | AZKKXController.InputSignal.M0
                )
            elif mode == ContinuousMode.FAST_FORWARD:
                logger.debug('Setting motor to FAST_FORWARD...')
                value = (
                    AZKKXController.InputSignal.FORWARD | AZKKXController.InputSignal.M1
                )
            elif mode == ContinuousMode.FAST_BACKWARD:
                logger.debug('Setting motor to FAST_BACKWARD...')
                value = (
                    AZKKXController.InputSignal.BACKWARD
                    | AZKKXController.InputSignal.M1
                )
            elif mode == ContinuousMode.STOP:
                logger.debug('Stopping motor...')
                value = 0
            else:
                raise ValueError(f'Invalid mode: {mode}')

            self._set_register_int32(
                unit_address=self.device_config.unitAddress,
                register_address=0x007C,
                value=value,
            ).result()

        def check_alarm(value):
            """Check if the motor is in alarm state and raise an exception if it is."""
            status = self.get_status_bits()
            if status.is_alarm():
                raise RuntimeError('Motor alarm occurred during continuous operation.')
            return value

        stop_commands = commands.pipe(
            ops.debounce(0.2),
            ops.map(lambda _: ContinuousMode.STOP),
        )

        rx.merge(
            commands,
            stop_commands,
        ).pipe(
            ops.distinct_until_changed(),
            ops.finally_action(lambda: set_motor(ContinuousMode.STOP)),
        ).subscribe(
            on_next=set_motor,
        )

        return rx.interval(0.1, scheduler=poll_scheduler).pipe(
            ops.map(check_alarm),
            ops.map(lambda _: self.get_position()),
            ops.distinct_until_changed(),
            ops.finally_action(lambda: set_motor(ContinuousMode.STOP)),
        )

    def set_operation_data(
        self,
        operation_number: int = 0,
        position: None | pint.Quantity = None,
        speed: None | pint.Quantity = None,
        mode: None | Literal['absolute', 'incremental'] = None,
    ):
        """Write the operation data for the specified operation number."""
        logger = logging.getLogger(__name__)

        resolution = self.device_config.resolution
        baser_address = 0x1800 + operation_number * 0x0040

        if position is not None:
            if not position.check('[length]'):
                raise ValueError(f'Position must be a length, got {position.units}')

            logger.debug(
                f'Setting operation {operation_number} position to {position:.3f~P}...'
            )
            self._set_register_int32(
                unit_address=self.device_config.unitAddress,
                register_address=baser_address + 2,
                value=int(position * resolution),
            )

        if speed is not None:
            if not speed.check('[length]/[time]'):
                raise ValueError(f'Speed must be a length/time, got {speed.units}')

            logger.debug(
                f'Setting operation {operation_number} speed to {speed:.3f~P}...'
            )
            self._set_register_int32(
                unit_address=self.device_config.unitAddress,
                register_address=baser_address + 4,
                value=int((speed * resolution).m_as('Hz')),
            )

        if mode is not None:
            if mode not in ['absolute', 'incremental']:
                raise ValueError(
                    f'Mode must be "absolute" or "incremental", got {mode}'
                )

            logger.debug(f'Setting operation {operation_number} mode to {mode}...')
            self._set_register_int32(
                unit_address=self.device_config.unitAddress,
                register_address=baser_address + 0,
                value=2 if mode == 'incremental' else 1,
            )
