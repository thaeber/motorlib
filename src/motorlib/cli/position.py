import logging

import rich_click as click
from pymodbus.exceptions import ModbusIOException

from ..controller import BaseController
from .cli import main


@main.command()
@click.pass_context
def position(ctx: click.Context) -> None:
    """Get the current position of the motor."""
    logger = logging.getLogger(__name__)

    device: BaseController = ctx.obj['device']
    axis = ctx.obj['axis']
    try:
        position = device.get_position()
        logger.info(f'Current position of axis "{axis}": {position}')
    except ModbusIOException as e:
        logger.error(e)
