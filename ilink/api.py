import requests
from typing import Any
from loguru import logger


class APIClient:
    def __init__(
        self,
        endpoint: str = "https://ilinkai.weixin.qq.com",
        bot_token: str = "",
        ilink_bot_id: str = "",
    ) -> None:
        self.endpoint = endpoint
        self.bot_token = bot_token
        self.ilink_bot_id = ilink_bot_id

    def update_credentials(self, bot_token: str, ilink_bot_id: str) -> None:
        self.bot_token = bot_token
        self.ilink_bot_id = ilink_bot_id

    def _generate_headers(self) -> dict[str, str]:
        import base64
        import secrets

        rand_n = secrets.token_bytes(4)
        rand_s = base64.b64encode(rand_n).decode()

        return {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.bot_token}",
            "X-WECHAT-UIN": rand_s,
        }

    def call_api(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.endpoint}{path}"
        data.update({"base_info": {"channel_version": "1.0.2"}})
        resp = requests.post(url, headers=self._generate_headers(), json=data)
        return resp.json()

    def get_updates(self, get_updates_buf: str = "") -> dict[str, Any]:
        path = "/ilink/bot/getupdates"
        data = {"get_updates_buf": get_updates_buf}
        return self.call_api(path, data)

    def send_message(
        self,
        to_user_id: str,
        context_token: str,
        message: dict[str, Any],
        client_id: str = "",
    ) -> dict[str, Any]:
        import time
        import secrets

        path = "/ilink/bot/sendmessage"
        if not client_id:
            client_id = (
                f"openclaw-weixin:{int(time.time() * 1000)}-{secrets.token_hex(4)}"
            )

        data = {
            "msg": {
                "from_user_id": self.ilink_bot_id,
                "to_user_id": to_user_id,
                "client_id": client_id,
                "message_type": 2,
                "message_state": 2,
                "context_token": context_token,
                "item_list": [message],
            }
        }
        return self.call_api(path, data)

    def get_upload_url(
        self,
        filekey: str,
        media_type: int,
        to_user_id: str,
        rawsize: int,
        rawfilemd5: str,
        filesize: int,
        aeskey: str,
    ) -> dict[str, Any]:
        path = "/ilink/bot/getuploadurl"
        data = {
            "filekey": filekey,
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
