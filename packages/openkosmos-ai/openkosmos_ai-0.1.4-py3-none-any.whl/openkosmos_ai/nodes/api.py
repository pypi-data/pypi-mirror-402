from typing import Optional, Literal

import requests

from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class ApiConfig(AIBaseConfig):
    base_url: str
    api_key: Optional[str] = None
    auth_mode: Literal["totp", "api_key"] = "api_key"


class ApiNode(BaseStateNode[ApiConfig]):
    def __init__(self, config: ApiConfig):
        super().__init__(config)
        self.api_key = None
        if config.auth_mode == "api_key":
            self.api_key = config.api_key

    def auth_totp(self, user_code: str, totp_code: str):
        api_key = self.auth_by_totp(user_code, totp_code)
        self.api_key = api_key
        return api_key

    def auth(self, api_key: str):
        self.api_key = api_key
        return self.api_key

    def get_api_key(self, runtime_api_key=None):
        if runtime_api_key is None:
            return self.api_key
        else:
            return runtime_api_key

    def auth_by_totp(self):
        return self.api_key

    def get(self, path: str, api_key=None):
        return requests.get(self.config().base_url + path, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_api_key(api_key)}"
        }).json()

    def delete(self, path: str, api_key=None):
        return requests.delete(self.config().base_url + path, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_api_key(api_key)}"
        }).json()

    def post(self, path: str, form=None, json=None, api_key=None, files=None):
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_api_key(api_key)}"
        }
        if form is not None:
            header["Content-Type"] = "multipart/form-data"
            return requests.post(self.config().base_url + path, headers=header, data=form).json()
        if json is not None:
            return requests.post(self.config().base_url + path, headers=header, json=json).json()
        if files is not None:
            del header["Content-Type"]
            return requests.post(self.config().base_url + path, headers=header, files=files).json()
        else:
            return requests.post(self.config().base_url + path, headers=header).json()
