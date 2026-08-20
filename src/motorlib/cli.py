import logging

import rich_click as click
from rich.logging import RichHandler

from .configuration import get_configuration

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='[%X]',
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
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
def main(
    ctx: click.Context,
    debug: bool,
    config_filename: str,
    config_arguments: list[tuple[str, str]],
) -> None:
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    logger.warning(config_arguments)
    ctx.obj = {
        'config': get_configuration(
            filename=config_filename,
            command_line_arguments=[f'{k}={v}' for k, v in config_arguments],
        )
    }
