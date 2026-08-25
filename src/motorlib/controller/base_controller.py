from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal

import pint
from reactivex import Observable

from .connection import ModbusSerialConnection


class ContinuousMode(Enum):
    FORWARD = 'forward'
    BACKWARD = 'backward'
    CRAWL_FORWARD = 'crawl_forward'
    CRAWL_BACKWARD = 'crawl_backward'
    FAST_FORWARD = 'fast_forward'
    FAST_BACKWARD = 'fast_backward'
    STOP = 'stop'


class BaseController(ABC):
    def __init__(self, connection: ModbusSerialConnection):
        self.connection = connection

    @abstractmethod
    def get_status(self) -> dict[str, bool]:
        """Get the status (bits) of the motor."""
        raise NotImplementedError

    @abstractmethod
    def alarm_reset(self):
        """Reset the alarm of the motor."""
        raise NotImplementedError

    @abstractmethod
    def home(self):
        """Home the motor."""
        raise NotImplementedError

    @abstractmethod
    def get_position(self) -> pint.Quantity:
        """Get the current position of the motor."""
        raise NotImplementedError

    @abstractmethod
    def move_by(
        self,
        distance: pint.Quantity,
    ):
        """Move the motor by the specified distance."""
        raise NotImplementedError

    @abstractmethod
    def continuous(
        self,
        commands: Observable[ContinuousMode],
    ) -> Observable[pint.Quantity]:
        """Move the motor continuously at the specified speed and direction."""
        raise NotImplementedError
