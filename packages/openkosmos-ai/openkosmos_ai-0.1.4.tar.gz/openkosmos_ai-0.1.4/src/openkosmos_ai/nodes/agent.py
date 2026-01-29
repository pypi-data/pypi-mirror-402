from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode
from openkosmos_ai.nodes.openai_client import OpenAIClientConfig


class AgentConfig(AIBaseConfig):
    openai: OpenAIClientConfig


class AgentNode(BaseStateNode[AgentConfig]):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
