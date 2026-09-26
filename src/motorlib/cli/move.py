import logging

import pint
import rich_click as click
from pymodbus.exceptions import ModbusIOException

from ..controller import BaseController
from .cli import main


def pint_dimensionality_validator(dimensionality: str):
    """Create a click validator for a specific unit using pint."""
    ureg = pint.application_registry.get()

    def validate(ctx, param, value):
        if value is None:
            return value
        try:
            quantity = ureg.Quantity(value)
            if quantity.check(dimensionality):
                return value
            else:
                raise click.BadParameter(
                    f'Value must be of dimensionality {dimensionality}, got {value:~P}'
                )
        except pint.errors.UndefinedUnitError, pint.errors.DimensionalityError:
            raise click.BadParameter(
                f'Value must be of dimensionality {dimensionality}, got {value:~P}'
            )

    return validate


@main.command(context_settings={'ignore_unknown_options': True})
@click.pass_context
@click.argument(
    'distance',
    type=pint.Quantity,
    required=True,
    callback=pint_dimensionality_validator('[length]'),
    help=('The distance to move the motor by. Must be a physical distance, e.g. 10mm.'),
)
def move(ctx: click.Context, distance) -> None:
    """Move the motor by the specified distance."""
    logger = logging.getLogger(__name__)

    logger.info(f'Moving motor by distance: {distance:~P}')

    device: BaseController = ctx.obj['device']
    try:
        device.move_by(distance)
    except (ModbusIOException, RuntimeError) as e:
        logger.error(e)


@main.command(context_settings={'ignore_unknown_options': True})
@click.pass_context
@click.argument(
    'position',
    type=pint.Quantity,
    required=True,
    callback=pint_dimensionality_validator('[length]'),
    help=('The position to move the motor to. Must be a physical distance, e.g. 10mm.'),
)
def goto(ctx: click.Context, position) -> None:
    """Move the motor to the specified position."""
    logger = logging.getLogger(__name__)

    logger.info(f'Moving motor to position: {position:~P}')

    device: BaseController = ctx.obj['device']
    try:
        device.move_to(position)
    except (ModbusIOException, RuntimeError) as e:
        logger.error(e)
