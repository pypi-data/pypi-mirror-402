from openkosmos_core.config import Config

from openkosmos_ai.nodes.agent import AgentConfig
from openkosmos_ai.nodes.api import ApiConfig
from openkosmos_ai.nodes.database_client import DatabaseClientConfig
from openkosmos_ai.nodes.dify_client import DifyClientConfig
from openkosmos_ai.nodes.git_repo import GitRepoConfig
from openkosmos_ai.nodes.openai_client import OpenAIClientConfig
from openkosmos_ai.nodes.rag_flow_client import RAGFlowClientConfig
from openkosmos_ai.nodes.skill import SkillConfig
from openkosmos_ai.nodes.vector_store import VectorStoreConfig
from openkosmos_ai.nodes.xinference_client import XinferenceClientConfig


class AIConfig(Config):

    def get_api_config(self, name: str | list[str] = "api") -> ApiConfig:
        return self.get(name, ApiConfig)

    def get_vectorstore_config(self, name: str | list[str] = "vectorstore") -> VectorStoreConfig:
        return self.get(name, VectorStoreConfig)

    def get_openai_config(self, name: str | list[str] = "openai") -> OpenAIClientConfig:
        return self.get(name, OpenAIClientConfig)

    def get_database_config(self, name: str | list[str] = "database") -> DatabaseClientConfig:
        return self.get(name, DatabaseClientConfig)

    def get_gitrepo_config(self, name: str | list[str] = "gitrepo") -> GitRepoConfig:
        return self.get(name, GitRepoConfig)

    def get_dify_config(self, name: str | list[str] = "dify") -> DifyClientConfig:
        return self.get(name, DifyClientConfig)

    def get_ragflow_config(self, name: str | list[str] = "ragflow") -> RAGFlowClientConfig:
        return self.get(name, RAGFlowClientConfig)

    def get_xinference_config(self, name: str | list[str] = "xinference") -> XinferenceClientConfig:
        return self.get(name, XinferenceClientConfig)

    def get_agent_config(self, name: str | list[str] = "agent") -> AgentConfig:
        return self.get(name, AgentConfig)

    def get_skill_config(self, name: str | list[str] = "skill") -> SkillConfig:
        return self.get(name, SkillConfig)
