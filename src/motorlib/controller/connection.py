import logging
from concurrent import futures
from typing import ClassVar

from pymodbus.client import ModbusSerialClient

from ..configuration import SerialPortConfig

logger = logging.getLogger(__name__)


class ModbusSerialConnection:
    __connections__: ClassVar[dict[str, ModbusSerialConnection]] = {}

    def __init__(self, cfg: SerialPortConfig):
        self.client = ModbusSerialClient(cfg.port, baudrate=cfg.baudRate)
        self.executor = futures.ThreadPoolExecutor(max_workers=1)

    def __new__(cls, cfg: SerialPortConfig):
        if cfg.port in ModbusSerialConnection.__connections__:
            return ModbusSerialConnection.__connections__[cfg.port]
        else:
            instance = super().__new__(cls)
            ModbusSerialConnection.__connections__[cfg.port] = instance
            return instance

    def close(self):
        return self.client.close()

    def _do_read_holding_registers(
        self, unit_address: int, register_address: int, count: int
    ):
        logger.debug(
            f'Read holding register(s): unit={unit_address},'
            f'register={register_address}, count={count}'
        )
        return self.client.read_holding_registers(
            address=register_address,
            count=count,
            device_id=unit_address,
        )

    def read_holding_registers(
        self, unit_address: int, register_address: int, num_registers: int = 1
    ):
        return self.executor.submit(
            self._do_read_holding_registers,
            unit_address,
            register_address,
            num_registers,
        )

    def _do_write_holding_register(
        self, unit_address: int, register_address: int, value: int
    ):
        logger.debug(
            f'Write holding register: unit={unit_address},'
            f'register={register_address}, value={value}'
        )
        return self.client.write_register(
            address=register_address, value=value, device_id=unit_address
        )

    def write_holding_register(
        self, unit_address: int, register_address: int, value: int
    ):
        return self.executor.submit(
            self._do_write_holding_register,
            unit_address,
            register_address,
            value,
        )
