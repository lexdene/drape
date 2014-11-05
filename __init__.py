version = '0.1.11.15'

from ._config_wrapper import ConfigWrapper
from . import _default_configs


config = ConfigWrapper()
config.register(_default_configs)
