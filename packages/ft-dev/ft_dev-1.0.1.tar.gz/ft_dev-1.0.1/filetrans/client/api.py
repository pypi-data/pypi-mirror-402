"""
filetrans client API wrapper
"""

import requests
from typing import Any, Dict


class FiletransClient:
    """filetrans jRPC 客户端"""

    def __init__(self, server_url: str, api_token: str):
        self.server_url = server_url.rstrip('/')
        self.api_token = api_token
        self.api_base = f"{self.server_url}/api/jrpc"

    def call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用 jRPC 方法"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": f"req_{id(self)}"
        }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.api_base, json=payload, headers=headers)

        try:
            data = response.json()
        except:
            raise Exception(f"Invalid response: {response.text}")

        if "error" in data and data["error"] is not None:
            error_msg = data["error"].get("message", str(data["error"]))
            raise Exception(error_msg)

        return data.get("result", {})
