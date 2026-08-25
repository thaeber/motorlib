from ..configuration import DeviceConfig
from .base_controller import BaseController, ContinuousMode
from .connection import ModbusSerialConnection


def get_controller(connection: ModbusSerialConnection, device_config: DeviceConfig):
    if device_config.driver == 'AZR-CD':
        from .oriental_motors.azr_cd import AZRCDController

        return AZRCDController(connection, device_config)
    elif device_config.driver == 'AZK-KX':
        from .oriental_motors.azk_kx import AZKKXController

        return AZKKXController(connection, device_config)
    else:
        raise ValueError(f'Unsupported driver: {device_config.driver}')


__all__ = [
    'BaseController',
    'ContinuousMode',
    'ModbusSerialConnection',
    'get_controller',
]
