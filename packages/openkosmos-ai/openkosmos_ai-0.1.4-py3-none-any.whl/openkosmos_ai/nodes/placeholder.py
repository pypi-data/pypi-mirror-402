from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class PlaceholderConfig(AIBaseConfig):
    name: str


class PlaceholderNode(BaseStateNode[PlaceholderConfig]):

    def __init__(self, config: str | PlaceholderConfig = None):
        if isinstance(config, str):
            super().__init__(PlaceholderConfig(name=config))
        else:
            super().__init__(config)

    def __call__(self, *args, **kwargs):
        print("[PLACEHOLDER]", self.config().name)
        pass
