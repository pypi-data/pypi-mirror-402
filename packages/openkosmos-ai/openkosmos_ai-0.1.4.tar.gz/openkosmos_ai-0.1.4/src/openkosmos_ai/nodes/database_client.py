from sqlalchemy import create_engine

from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class DatabaseClientConfig(AIBaseConfig):
    url: str


class DatabaseClientNode(BaseStateNode[DatabaseClientConfig]):
    def __init__(self, config: DatabaseClientConfig):
        super().__init__(config)
        self.database_engine = create_engine(config.url, pool_size=10)

    def engine(self):
        return self.database_engine
