import base64
import json
from pathlib import Path
import secrets
import time
from typing import Any
from loguru import logger
from qrcode import QRCode

import requests


class ILink:
    endpoint: str = "https://ilinkai.weixin.qq.com"
    status: dict[str, Any] = {}
    status_cache = Path("cache/bot_login_status.json")

    def __init__(self) -> None:
        self.status = self.bot_login_with_cache()

    def bot_login_with_cache(self) -> dict[str, Any]:
        if not self.status_cache.exists():
            return {}
        return json.loads(self.status_cache.read_text())

    def bot_login(self) -> dict[str, Any]:
        qr_url = f"{self.endpoint}/ilink/bot/get_bot_qrcode?bot_type=3"
        qr = requests.post(qr_url).json()
        logger.info(f"BOT未登录, 待授权二维码信息: {qr}")

        qr_code = qr.get("qrcode", "")
        qr_link = qr.get("qrcode_img_content", "")

        qr_img = QRCode()
        qr_img.add_data(qr_link)
        qr_img.print_ascii()

        while True:
            time.sleep(3)
            qr_resp = requests.post(
                f"{self.endpoint}/ilink/bot/get_qrcode_status?qrcode={qr_code}"
            ).json()
            logger.debug(f"BOT登录中 {qr_resp}")

            qr_status = qr_resp.get("status", "")
            if "confirmed" == qr_status:
                logger.info(f"BOT登录成功 {qr_resp}")
                self.status = qr_resp
                self.status_cache.write_text(json.dumps(qr_resp))
                return qr_resp

            if "expired" == qr_status:
                logger.warning(f"BOT登录超时 {qr_resp} ")
                return {}

    def rand_uin(self) -> str:
        rand_n = secrets.token_bytes(4)
        rand_s = base64.b64encode(rand_n).decode()
        return rand_s

    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.status['bot_token']}",
            "X-WECHAT-UIN": self.rand_uin(),
        }

    def call_api(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        resp = requests.post(url, headers=self.headers(), json=data)
        return resp.json()

    def get_updates(self, updates_buf: str = "") -> dict[str, Any]:
        path = "/ilink/bot/getupdates"
        data = {
            "get_updates_buf": updates_buf,
            "base_info": {"channel_version": "1.0.2"},
        }
        return self.call_api(path, data)

    def send_message(
        self,
        to_user_id: str,
        context_token: str,
        messages: list[str],
    ) -> dict[str, Any]:
        path = "/ilink/bot/sendmessage"
        data = {
            "msg": {
                "to_user_id": to_user_id,
                "message_type": 2,
                "message_state": 2,
                "context_token": context_token,
                "item_list": [
                    {"type": 1, "text_item": {"text": message}} for message in messages
                ],
            }
        }
        return self.call_api(path, data)

    def get_upload_url(self):
        path = "/ilink/bot/getuploadurl"
        print(path)

    def get_config(self) -> dict[str, Any]:
        path = "/ilink/bot/getconfig"
        data = {"ilink_user_id": self.status["ilink_user_id"]}
        return self.call_api(path, data)

    def send_typing(self):
        path = "/ilink/bot/sendtyping"
        print(path)


if __name__ == "__main__":
    ilink = ILink()

    # print(ilink.bot_login())
    # print(ilink.get_config())

    # result = ilink.get_updates()
    # print(result)

    # messages = [msg for msg in result["msgs"]]
    # message = messages[0]

    # print(
    #     ilink.send_message(
    #         message["from_user_id"],
    #         message["context_token"],
    #         ["hi1 from bot"],
    #     )
    # )
