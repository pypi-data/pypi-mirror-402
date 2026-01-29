import requests

from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class DifyClientConfig(AIBaseConfig):
    name: str
    url: str
    email: str
    password: str


class DifyClientNode(BaseStateNode[DifyClientConfig]):
    def __init__(self, config: DifyClientConfig):
        super().__init__(config)
        access_token = DifyClientNode.login(config)

        self.auth_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

    @staticmethod
    def login(config: DifyClientConfig):
        return requests.post(config.url + "/console/api/login", json={
            "email": config.email,
            "password": config.password,
            "language": "zh-Hans",
            "remember_me": "true"
        }).json()["data"]["access_token"]

    def console_api_apps(self, page=1, limit=100):
        return requests.get(self.config().url + f"/console/api/apps?page={page}&limit={limit}",
                            headers=self.auth_header).json()

    def console_api_apps_export(self, app_id: str):
        return requests.get(self.config().url + f"/console/api/apps/{app_id}/export?include_secret=true",
                            headers=self.auth_header).json()
