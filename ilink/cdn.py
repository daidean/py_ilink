import hashlib
import requests
from typing import Any
from pathlib import Path
from loguru import logger


class CDNClient:
    def __init__(
        self,
        cdn_endpoint: str = "https://novac2c.cdn.weixin.qq.com",
    ) -> None:
        self.cdn_endpoint = cdn_endpoint

    def upload_file_to_cdn(self, param: str, filekey: str, payload: bytes) -> str:
        url = f"{self.cdn_endpoint}/c2c/upload"
        url += f"?encrypted_query_param={param}"
        url += f"&filekey={filekey}"
        headers = {"Content-Type": "application/octet-stream"}

        resp = requests.post(url, headers=headers, data=payload)
        logger.debug(resp)

        if resp.status_code != 200:
            logger.error(resp.headers)

        return resp.headers.get("x-encrypted-param", "")

    def download_file_from_cdn(self, encrypt_query_param: str) -> bytes:
        url = f"{self.cdn_endpoint}/c2c/download"
        url += f"?encrypted_query_param={encrypt_query_param}"

        resp = requests.get(url)
        if resp.status_code != 200:
            logger.error(f"Download failed: {resp.status_code}")
            return b""

        return resp.content
