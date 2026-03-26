import json
import time
import base64
import secrets
import requests

from typing import Any
from pathlib import Path
from datetime import datetime
from qrcode import QRCode
from loguru import logger


class ILink:
    endpoint: str = "https://ilinkai.weixin.qq.com"
    login_info_path = Path("cache/bot_login_info.json")
    typing_ticket_path = Path("cache/bot_typing_ticket.json")

    def __init__(self) -> None:
        self.login_info_cache = self.login_with_cache()
        self.typing_ticket_cache = self.typing_ticket_with_cache()

    """ 工具方法 """

    def typing_ticket_with_cache(self) -> dict[str, Any]:
        if not self.typing_ticket_path.exists():
            return {}
        return json.loads(self.typing_ticket_path.read_text())

    def save_typing_ticket(self, typing_ticket: dict[str, Any]) -> None:
        self.typing_ticket_cache = typing_ticket
        self.typing_ticket_path.write_text(json.dumps(typing_ticket))

    def login_with_cache(self) -> dict[str, Any]:
        if not self.login_info_path.exists():
            logger.warning("BOT登录, 未找到登录缓存")
            return self.login()

        logger.info("BOT登录, 已加载登录缓存")
        return json.loads(self.login_info_path.read_text())

    def login(self) -> dict[str, Any]:
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
        self.login_info_cache = login_info
        self.login_info_path.write_text(json.dumps(login_info))

    def rand_uin(self) -> str:
        rand_n = secrets.token_bytes(4)
        rand_s = base64.b64encode(rand_n).decode()
        return rand_s

    def rand_file_key(self, byte_count: int = 16) -> str:
        return secrets.token_hex(byte_count)

    def time_ms(self) -> int:
        return int(time.time() * 1000)

    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.login_info_cache['bot_token']}",
            "X-WECHAT-UIN": self.rand_uin(),
        }

    def client_id(self) -> str:
        return f"openclaw-weixin:{self.time_ms}-{secrets.token_hex(4)}"

    def message_from_text(self, message: str) -> dict[str, Any]:
        return {"type": 1, "text_item": {"text": message}}

    def message_from_image(self): ...  # type 2
    def message_from_voice(self): ...  # type 3
    def message_from_file(self): ...  # type 4
    def message_from_video(self): ...  # type 5

    """ 接口调用 """

    def call_api(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        data.update({"base_info": {"channel_version": "1.0.2"}})
        resp = requests.post(url, headers=self.headers(), json=data)
        return resp.json()

    """ 协议方法 """

    def get_updates(self, get_updates_buf: str = "") -> dict[str, Any]:
        path = "/ilink/bot/getupdates"
        data = {"get_updates_buf": get_updates_buf}
        return self.call_api(path, data)

    def send_message(
        self,
        to_user_id: str,
        context_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        path = "/ilink/bot/sendmessage"
        data = {
            "msg": {
                "from_user_id": self.login_info_cache["ilink_bot_id"],
                "to_user_id": to_user_id,
                "client_id": self.client_id(),
                "message_type": 2,  # `1` = USER, `2` = BOT
                "message_state": 2,  # `0` = NEW, `1` = GENERATING, `2` = FINISH
                "context_token": context_token,
                "item_list": [message],
            }
        }
        return self.call_api(path, data)

    def get_upload_url(
        self,
        media_type: int,
        to_user_id: str,
        rawsize: int,
        rawfilemd5: str,
        filesize: int,
        aeskey: str,
    ):
        path = "/ilink/bot/getuploadurl"
        data = {
            "filekey": self.rand_file_key(),
            "media_type": media_type,
            "to_user_id": to_user_id,
            "rawsize": rawsize,
            "rawfilemd5": rawfilemd5,
            "filesize": filesize,
            "no_need_thumb": True,
            "aeskey": aeskey,
        }
        return self.call_api(path, data)

    def get_config(self, ilink_user_id: str, context_token: str) -> dict[str, Any]:
        path = "/ilink/bot/getconfig"
        data = {
            "ilink_user_id": ilink_user_id,
            "context_token": context_token,
        }
        return self.call_api(path, data)

    def send_typing(
        self,
        ilink_user_id: str,
        typing_ticket: str,
        status: int,
    ) -> dict[str, Any]:
        path = "/ilink/bot/sendtyping"
        data = {
            "ilink_user_id": ilink_user_id,
            "typing_ticket": typing_ticket,
            "status": status,
        }
        return self.call_api(path, data)

    def get_typing_ticket(self, ilink_user_id: str, context_token: str) -> str:
        now_time = time.time()
        typing_ticket = self.typing_ticket_cache.get(ilink_user_id)

        if typing_ticket and now_time < typing_ticket["valid_time"]:
            return typing_ticket["typing_ticket"]

        typing_ticket = self.get_config(ilink_user_id, context_token)
        typing_ticket.update({"valid_time": now_time + 60 * 60 * 24})

        self.typing_ticket_cache[ilink_user_id] = typing_ticket
        self.save_typing_ticket(self.typing_ticket_cache)

        return typing_ticket["typing_ticket"]


if __name__ == "__main__":
    ilink = ILink()

    login_info = ilink.login()
    ilink.save_login_info(login_info)
    logger.info(login_info)

    while True:
        get_updates_buf = ilink.login_info_cache["get_updates_buf"]
        updates = ilink.get_updates(get_updates_buf)
        logger.info(updates)

        ilink.login_info_cache["get_updates_buf"] = updates["get_updates_buf"]
        ilink.save_login_info(ilink.login_info_cache)

        if not updates["msgs"]:
            continue

        for message in updates["msgs"]:
            logger.info(message)
            reply = ilink.message_from_text(f"Hello World - {datetime.now()}")
            reply_to = message["from_user_id"]
            reply_ct = message["context_token"]

            reply_typing_ticket = ilink.get_typing_ticket(reply_to, reply_ct)
            logger.info(reply_typing_ticket)

            typing_resp = ilink.send_typing(reply_to, reply_typing_ticket, 1)
            logger.info(typing_resp)

            reply_resp = ilink.send_message(reply_to, reply_ct, reply)
            logger.info(reply_resp)

            typing_resp = ilink.send_typing(reply_to, reply_typing_ticket, 2)
            logger.info(typing_resp)
