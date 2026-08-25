import logging

import rich_click as click
from pymodbus.exceptions import ModbusIOException
from rich.console import Console

from ..controller import BaseController
from ._cli_utils import format_status_table
from .cli import main


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Get the status of the motor."""
    logger = logging.getLogger(__name__)
    console = Console()

    device: BaseController = ctx.obj['device']
    try:
        logger.info('Getting motor status...')
        status = device.get_status()

        logger.debug('Motor status: %s', status)

        table = format_status_table(status, title='Motor Status')
        console.print(table)

    except ModbusIOException as e:
        logger.error(e)
