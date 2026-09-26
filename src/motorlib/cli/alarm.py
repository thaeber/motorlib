import logging

import rich_click as click
from pymodbus.exceptions import ModbusIOException

from ..controller import BaseController
from .cli import main


@main.group()
@click.pass_context
def alarm(ctx: click.Context) -> None:
    """Manage the alarm state of the motor."""


@alarm.command()
@click.pass_context
def reset(ctx: click.Context) -> None:
    """Reset the alarm of the motor."""
    logger = logging.getLogger(__name__)

    device: BaseController = ctx.obj['device']
    try:
        device.alarm_reset()
    except ModbusIOException as e:
        logger.error(e)
