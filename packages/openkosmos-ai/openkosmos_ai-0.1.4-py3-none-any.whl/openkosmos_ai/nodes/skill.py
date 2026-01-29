from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode
from openkosmos_ai.nodes.openai_client import OpenAIClientConfig


class SkillConfig(AIBaseConfig):
    openai: OpenAIClientConfig


class SkillNode(BaseStateNode[SkillConfig]):
    def __init__(self, config: SkillConfig):
        super().__init__(config)
