from typing import Optional, List

import requests

from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class XinferenceClientConfig(AIBaseConfig):
    base_url: str
    api_key: str
    rerank_model: Optional[str] = "bge-reranker-v2-m3"
    embed_model: Optional[str] = "bge-m3"


class XinferenceClientNode(BaseStateNode[XinferenceClientConfig]):
    def __init__(self, config: XinferenceClientConfig):
        super().__init__(config)

    def rerank(self, documents: List[str], query: str, top_n=3):
        return requests.post(self.config().base_url + "/v1/rerank",
                             json={
                                 "model": self.config().rerank_model,
                                 "query": query,
                                 "documents": documents,
                                 "top_n": top_n
                             }).json()["results"]

    def embed(self, input: str):
        return requests.post(self.config().base_url + "/v1/embeddings",
                             json={
                                 "model": self.config().embed_model,
                                 "input": input,
                                 "encoding_format": "float"
                             }).json()
