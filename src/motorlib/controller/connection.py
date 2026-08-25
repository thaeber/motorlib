import logging
from concurrent import futures
from typing import ClassVar

from pymodbus.client import ModbusSerialClient
from pymodbus.pdu import ModbusPDU

from ..configuration import SerialPortConfig

logger = logging.getLogger(__name__)


class ModbusSerialConnection:
    __connections__: ClassVar[dict[str, ModbusSerialConnection]] = {}

    def __init__(self, cfg: SerialPortConfig):
        self.cfg = cfg
        self.client = ModbusSerialClient(
            cfg.port,
            baudrate=cfg.baudRate,
            parity=cfg.parity,
            stopbits=cfg.stopbits,
        )
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        ModbusSerialConnection.__connections__.pop(self.cfg.port, None)
        return False

    @classmethod
    def close_all(cls):
        for connection in cls.__connections__.values():
            connection.close()
        cls.__connections__.clear()

    def _do_read_holding_registers(
        self, unit_address: int, register_address: int, num_registers: int
    ) -> ModbusPDU:
        logger.debug(
            f'Read holding register(s): unit={unit_address},'
            f'register={register_address}, count={num_registers}'
        )
        return self.client.read_holding_registers(
            address=register_address,
            count=num_registers,
            device_id=unit_address,
        )

    def read_holding_registers(
        self, unit_address: int, register_address: int, num_registers: int = 1
    ) -> futures.Future[ModbusPDU]:
        return self.executor.submit(
            self._do_read_holding_registers,
            unit_address,
            register_address,
            num_registers,
        )

    def _do_write_holding_register(
        self, unit_address: int, register_address: int, value: int
    ) -> ModbusPDU:
        logger.debug(
            f'Write holding register: unit={unit_address},'
            f'register={register_address}, value={value}'
        )
        return self.client.write_register(
            address=register_address, value=value, device_id=unit_address
        )

    def write_holding_register(
        self, unit_address: int, register_address: int, value: int
    ) -> futures.Future[ModbusPDU]:
        return self.executor.submit(
            self._do_write_holding_register,
            unit_address,
            register_address,
            value,
        )

    def _do_write_holding_registers(
        self, unit_address: int, register_address: int, values: list[int]
    ) -> ModbusPDU:
        logger.debug(
            f'Write holding registers: unit={unit_address},'
            f'register={register_address}, values={values}'
        )
        return self.client.write_registers(
            address=register_address, values=values, device_id=unit_address
        )

    def write_holding_registers(
        self, unit_address: int, register_address: int, values: list[int]
    ) -> futures.Future[ModbusPDU]:
        return self.executor.submit(
            self._do_write_holding_registers,
            unit_address,
            register_address,
            values,
        )
