import logging
from os import PathLike
from pathlib import Path
from typing import Annotated, Literal

import pint
import pydantic_pint
from omegaconf import OmegaConf
from pint import Quantity
from pydantic import BaseModel, ConfigDict, Field
from pydantic_pint import PydanticPintQuantity
from rich.pretty import pretty_repr

ureg = pint.application_registry.get()
ureg.define(
    'step = 1 * count = [dimensionless]'
)  # define a custom unit for motor steps
pydantic_pint.set_registry(ureg)
logger = logging.getLogger(__name__)


class SerialPortConfig(BaseModel):
    port: str = 'COM4'
    baudRate: int = 115200
    parity: Literal['N', 'E', 'O', 'M', 'S'] = 'E'
    stopbits: Literal[1, 1.5, 2] = 1  # pyright: ignore[reportInvalidTypeForm]


Driver = Literal['AZR-CD', 'AZK-KX']

type Resolution = Annotated[Quantity, PydanticPintQuantity('1/[length]')]
type Speed = Annotated[Quantity, PydanticPintQuantity('[length]/[time]')]


class DeviceConfig(BaseModel):
    name: str
    unitAddress: int = 1
    driver: Driver = 'AZR-CD'
    # resolution of linear stage
    resolution: Annotated[Resolution, Field(validate_default=True)] = '(1000step)/(6mm)'
    # speed of linear stage
    speed: Annotated[Speed, Field(validate_default=True)] = '2mm/s'
    crawl: Annotated[Speed, Field(validate_default=True)] = '0.1mm/s'
    fast: Annotated[Speed, Field(validate_default=True)] = '5mm/s'


class Config(BaseModel):
    model_config = ConfigDict(extra='forbid')
    connection: SerialPortConfig = SerialPortConfig()
    devices: list[DeviceConfig] = []


def _load_configuration_from_file(filename: str):

    config_path = Path(filename)
    if not config_path.exists():
        raise FileNotFoundError(f'Configuration file not found: {filename}')

    logger.info(f'Loading configuration from: {filename}')
    return OmegaConf.load(config_path)


def get_configuration(
    *,
    filename: None | str | PathLike = None,
    command_line_arguments: None | list[str] = None,
):
    cfg = OmegaConf.create(Config().model_dump())

    # merge with configuration from file if provided
    if filename is not None:
        try:
            file_config = _load_configuration_from_file(filename)
            cfg = OmegaConf.merge(cfg, file_config)
        except FileNotFoundError:
            logger.warning(
                f'Configuration file not found: {filename}. Using default configuration.'
            )

    # merge with command line arguments if provided
    if command_line_arguments is not None:
        cfg.merge_with_dotlist(command_line_arguments)

    # validate the final configuration against the Pydantic model
    result = Config.model_validate(OmegaConf.to_container(cfg, resolve=True))

    logger.debug('Current configuration:')
    logger.debug(pretty_repr(result))

    return result
