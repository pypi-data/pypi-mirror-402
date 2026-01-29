#!/usr/bin/env python3

import json
import requests
from dataclasses import dataclass

@dataclass
class FeishuConfig:
    app_id: str
    app_secret: str
    app_token: str
    table_id: str

class Feishu:
    def __init__(self, config_file: str):
        self.config = self.load_config(config_file)
        self.access_token = self._get_access_token()

    def load_config(self, config_file: str):
        with open(config_file, 'r') as config_file:
            config_data = json.load(config_file)

        feishu_config = FeishuConfig(
            app_id=config_data['app_id'],
            app_secret=config_data['app_secret'],
            app_token=config_data['app_token'],
            table_id=config_data['table_id']
        )

        return feishu_config

    def _get_access_token(self):
        url = f"https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.config.app_id,
            "app_secret": self.config.app_secret
        }
        response = requests.post(url, data=payload)
        return response.json()["tenant_access_token"]

    def _request_feishu_api(self, url: str, payload: dict):
        # 请求头
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(response.json())
        return response.status_code == 200

    def add_inference_record(self, payload: dict):
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.config.app_token}/tables/{self.config.table_id}/records"
        payload = {
            "fields": payload
        }
        return self._request_feishu_api(url, payload)

