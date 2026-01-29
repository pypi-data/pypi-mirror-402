from typing import Generic, Type

from openkosmos_ai.common.model import AI_CONFIG_T


class BaseStateNode(Generic[AI_CONFIG_T]):
    _config = None

    def __init__(self, config=None):
        self._config = config

    def config(self) -> Type[AI_CONFIG_T]:
        return self._config
