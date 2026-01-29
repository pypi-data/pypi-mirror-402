import requests

from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class RAGFlowClientConfig(AIBaseConfig):
    base_url: str
    api_key: str


class RAGFlowClientNode(BaseStateNode[RAGFlowClientConfig]):
    def __init__(self, config: RAGFlowClientConfig):
        super().__init__(config)
        self.api_prefix = "/api/v1"
        self.auth_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }

    def list_datasets(self, page=1, page_size=1000, dataset_id: str = None, orderby="create_time",
                      desc="true",
                      dataset_name=None):
        id_str = "" if dataset_id is None else f"&id={dataset_id}"
        name_str = "" if dataset_name is None else f"&name={dataset_name}"
        return requests.get(
            self.config().base_url + f"{self.api_prefix}/datasets?page={page}&page_size={page_size}&orderby={orderby}&desc={desc}{name_str}{id_str}",
            headers=self.auth_header).json()

    def get_document_chunks(self, dataset_id: str, document_id: str, page=1, page_size=1000):
        return requests.get(self.config().base_url +
                            f"{self.api_prefix}/datasets/{dataset_id}/documents/{document_id}/chunks?page={page}&page_size={page_size}",
                            headers=self.auth_header).json()

    def get_documents(self, dataset_id: str, document_id: str = None, page=1, page_size=1000):
        return requests.get(self.config().base_url +
                            f"{self.api_prefix}/datasets/{dataset_id}/documents?page={page}&page_size={page_size}" + (
                                "" if document_id is None else f"&id={document_id}"),
                            headers=self.auth_header).json()

    def get_document_content(self, dataset_id: str, document_id: str):
        return requests.get(self.config().base_url +
                            f"{self.api_prefix}/datasets/{dataset_id}/documents/{document_id}",
                            headers=self.auth_header).content

    def retrieve(self, question: str, dataset_ids: list[str], top_k=1):
        return requests.post(self.config().base_url + f"{self.api_prefix}/retrieval",
                            headers=self.auth_header, json={
                "question": question,
                "dataset_ids": dataset_ids,
                "top_k": top_k
            }).json()
