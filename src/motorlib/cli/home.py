import logging

import rich_click as click
from pymodbus.exceptions import ModbusIOException

from ..controller import BaseController
from .cli import main


@main.command()
@click.pass_context
def home(ctx: click.Context) -> None:
    """Home the motor."""
    logger = logging.getLogger(__name__)

    device: BaseController = ctx.obj['device']
    try:
        device.home()
    except ModbusIOException as e:
        logger.error(e)
