import logging
from os import PathLike
from pathlib import Path
from typing import Literal

from omegaconf import OmegaConf
from pydantic import BaseModel, ConfigDict
from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)


class SerialPortConfig(BaseModel):
    port: str = 'COM1'
    baudRate: int = 19200


Driver = Literal['AZR-CD', 'AZK']


class DeviceConfig(BaseModel):
    name: str
    unitAddress: int = 1
    driver: Driver = 'AZR-CD'


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
