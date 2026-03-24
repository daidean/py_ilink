import json
import time
import base64
import secrets
import requests

from typing import Any
from pathlib import Path
from datetime import datetime
from loguru import logger
from qrcode import QRCode


class ILink:
    endpoint: str = "https://ilinkai.weixin.qq.com"
    login_info: dict[str, Any] = {}
    login_info_path = Path("cache/bot_login_info.json")

    def __init__(self) -> None:
        self.login_info = self.bot_login_with_cache()

    def bot_login_with_cache(self) -> dict[str, Any]:
        if not self.login_info_path.exists():
            return {}
        return json.loads(self.login_info_path.read_text())

    def bot_login(self) -> dict[str, Any]:
        qr_get_path = "/ilink/bot/get_bot_qrcode?bot_type=3"
        qr_get_url = f"{self.endpoint}{qr_get_path}"
        qr = requests.post(qr_get_url).json()
        logger.info(f"BOT未登录, 待授权二维码信息: {qr}")

        qr_code, qr_link = qr["qrcode"], qr["qrcode_img_content"]
        qr_img = QRCode()
        qr_img.add_data(qr_link)
        qr_img.print_ascii()

        logger.info("BOT未登录, 等待扫描二维码授权")
        qr_query_path = f"/ilink/bot/get_qrcode_status?qrcode={qr_code}"
        qr_query_url = f"{self.endpoint}{qr_query_path}"
        while True:
            time.sleep(3)
            qr_resp = requests.post(qr_query_url).json()
            logger.debug(f"BOT登录状态: {qr_resp}")

            if "confirmed" == qr_resp["status"]:
                qr_resp["get_updates_buf"] = ""
                logger.info(f"BOT登录成功 {qr_resp}")
                return qr_resp

            if "expired" == qr_resp["status"]:
                logger.warning(f"BOT登录超时 {qr_resp} ")
                return {}

    def save_login_info(self, login_info: dict[str, Any]) -> None:
        self.login_info = login_info
        self.login_info_path.write_text(json.dumps(login_info))

    def rand_uin(self) -> str:
        rand_n = secrets.token_bytes(4)
        rand_s = base64.b64encode(rand_n).decode()
        return rand_s

    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.login_info['bot_token']}",
            "X-WECHAT-UIN": self.rand_uin(),
        }

    def call_api(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        resp = requests.post(url, headers=self.headers(), json=data)
        return resp.json()

    def get_updates(self, get_updates_buf: str = "") -> dict[str, Any]:
        path = "/ilink/bot/getupdates"
        data = {
            "get_updates_buf": get_updates_buf,
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

    def get_config(self):
        path = "/ilink/bot/getconfig"
        print(path)

    def send_typing(self):
        path = "/ilink/bot/sendtyping"
        print(path)


if __name__ == "__main__":
    ilink = ILink()

    login_info = ilink.bot_login()
    ilink.save_login_info(login_info)
    logger.info(login_info)

    while True:
        get_updates_buf = ilink.login_info["get_updates_buf"]
        updates = ilink.get_updates(get_updates_buf)
        logger.info(updates)

        ilink.login_info["get_updates_buf"] = updates["get_updates_buf"]
        ilink.save_login_info(ilink.login_info)

        if not updates["msgs"]:
            continue

        messages = [msg for msg in updates["msgs"]]
        for message in messages:
            reply = f"Hello World - {datetime.now()}"
            reply_to = message["from_user_id"]
            reply_ct = message["context_token"]
            ilink.send_message(reply_to, reply_ct, [reply])
