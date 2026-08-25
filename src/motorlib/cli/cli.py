import logging

import rich_click as click
from rich.logging import RichHandler

from ..configuration import get_configuration
from ..controller import ModbusSerialConnection, get_controller

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='[%X]',
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.version_option(package_name='motorlib', prog_name='motor')
@click.option(
    '--config-file',
    'config_filename',
    type=str,
    default='.motors.yaml',
    show_default=True,
    help="""The name/path of the configuration file.""",
)
@click.option(
    '-c',
    'config_arguments',
    type=(str, str),
    multiple=True,
    help=(
        """Override configuration values from the command line. Use dot """
        """notation for nested values, e.g., -c connection.port COM3"""
    ),
)
@click.argument(
    'axis',
    type=str,
    required=True,
    help='The name of the axis to control, e.g., x, y, z.',
)
@click.pass_context
def main(
    ctx: click.Context,
    axis: str,
    debug: bool,
    config_filename: str,
    config_arguments: list[tuple[str, str]],
) -> None:
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)

    config = get_configuration(
        filename=config_filename,
        command_line_arguments=[f'{k}={v}' for k, v in config_arguments],
    )

    # validate that the specified axis exists in the configuration
    if not any(device.name == axis for device in config.devices):
        raise click.BadParameter(
            f"Axis '{axis}' not found in configuration. "
            f'Available axes: {[device.name for device in config.devices]}'
        )
    device_config = next(device for device in config.devices if device.name == axis)

    # create Modbus serial connection
    logger.debug(f'Opening Modbus serial connection on port {config.connection.port}')
    connection = ModbusSerialConnection(config.connection)

    ctx.obj = {
        'config': config,
        'device_config': device_config,
        'connection': ctx.with_resource(connection),
        'axis': axis,
        'device': get_controller(connection, device_config),
    }
