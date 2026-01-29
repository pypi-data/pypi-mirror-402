from typing import TypeVar

from openkosmos_core.common.model import BaseConfig


class AIBaseConfig(BaseConfig):
    pass


AI_CONFIG_T = TypeVar("AI_CONFIG_T", bound=AIBaseConfig)
