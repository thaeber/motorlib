import logging

import rich_click as click
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException

from ..configuration import DeviceConfig
from .cli import main


@main.command()
@click.pass_context
def diagnosis(ctx: click.Context) -> None:
    """Run a diagnosis of the motor system."""
    logger = logging.getLogger(__name__)

    connection: ModbusSerialClient = ctx.obj['connection']
    device: DeviceConfig = ctx.obj['device']
    # connection.read_holding_registers(address=, register_address=0, num_registers=10)
    try:
        logger.info(
            f'Diagnosing device {device.name} (unit address: {device.unitAddress})...'
        )
        message = b'Test'
        result = connection.diag_query_data(message, device_id=device.unitAddress)
        if result.isError():
            logger.error(f'Diagnosis failed: {vars(result)}')
        elif message == result.message:
            logger.info(f'Diagnosis successful: {result.message}')
        else:
            logger.error(f'Diagnosis failed: expected {message}, got {result.message}')

    except ModbusIOException as e:
        logger.error(e)
