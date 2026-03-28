import time
import json
import base64
import secrets
import hashlib
import requests

from typing import Any
from pathlib import Path
from datetime import datetime
from qrcode import QRCode
from loguru import logger

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class ILink:
    endpoint: str = "https://ilinkai.weixin.qq.com"
    cdn_endpoint: str = "https://novac2c.cdn.weixin.qq.com"
    login_info_path = Path("cache/bot_login_info.json")
    typing_ticket_path = Path("cache/bot_typing_ticket.json")
    file_message_path = Path("cache/bot_upload_files.json")

    def __init__(self) -> None:
        self.login_info_cache = self.login_with_cache()
        self.typing_ticket_cache = self.typing_ticket_with_cache()
        self.file_message_cache = self.file_message_with_cache()

    """ 工具方法 """

    def file_message_with_cache(self) -> dict[str, Any]:
        if not self.file_message_path.exists():
            return {}
        return json.loads(self.file_message_path.read_text())

    def save_file_message(self, file_message: dict[str, Any]) -> None:
        self.file_message_cache = file_message
        self.file_message_path.write_text(json.dumps(file_message))

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
        return f"openclaw-weixin:{self.time_ms()}-{secrets.token_hex(4)}"

    """ 工具方法: 消息格式化 """

    def message_from_text(self, message: str) -> dict[str, Any]:
        return {
            "type": 1,
            "text_item": {"text": message},
        }

    def message_from_image(self, file_path: str, to_user_id: str) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.message_from_text(f"<img {file_path}>")

        media = self.parse_file_and_upload(
            file=file,
            file_type=1,
            to_user_id=to_user_id,
        )

        return {
            "type": 2,
            "image_item": {"media": media},
        }

    def message_from_voice(
        self,
        file_path: str,
        to_user_id: str,
        encode_type: int = 0,
        bits_per_sample: int = 0,
        sample_rate: int = 0,
        playtime: int = 0,
        text: str = "",
    ) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.message_from_text(f"<voice {file_path}>")

        media = self.parse_file_and_upload(
            file=file,
            file_type=4,
            to_user_id=to_user_id,
        )

        voice_item: dict[str, Any] = {
            "media": media,
        }

        if encode_type != 0:
            voice_item.update({"encode_type": encode_type})
        if bits_per_sample != 0:
            voice_item.update({"bits_per_sample": bits_per_sample})
        if sample_rate != 0:
            voice_item.update({"sample_rate": sample_rate})
        if playtime != 0:
            voice_item.update({"playtime": playtime})
        if text != "":
            voice_item.update({"text": text})

        return {
            "type": 3,
            "voice_item": voice_item,
        }

    def message_from_file(
        self,
        file_path: str,
        to_user_id: str,
        file_name: str,
    ) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.message_from_text(f"<file {file_path}>")

        file_md5 = hashlib.md5(file.read_bytes()).hexdigest()
        file_len = f"{file.stat().st_size}"

        media = self.parse_file_and_upload(
            file=file,
            file_type=3,
            to_user_id=to_user_id,
        )

        file_item = {
            "media": media,
            "file_name": file_name,
            "md5": file_md5,
            "len": file_len,
        }

        return {
            "type": 4,
            "file_item": file_item,
        }

    def message_from_video(
        self,
        file_path: str,
        to_user_id: str,
        play_length: int = 0,
    ) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.message_from_text(f"<video {file_path}>")

        file_md5 = hashlib.md5(file.read_bytes()).hexdigest()
        file_len = file.stat().st_size

        media = self.parse_file_and_upload(
            file=file,
            file_type=2,
            to_user_id=to_user_id,
        )

        video_item = {
            "media": media,
            "video_size": file_len,
            "video_md5": file_md5,
        }

        if play_length != 0:
            video_item.update({"play_length": play_length})

        return {
            "type": 5,
            "video_item": video_item,
        }

    """ 工具方法：文件加解密 """

    def encrypt_aes_ecb(self, payload: bytes, key: bytes) -> bytes:
        padder = padding.PKCS7(128).padder()
        padded = padder.update(payload) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = cipher.encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    def decrypt_aes_ecb(self, payload: bytes, key: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        decryptor = cipher.decryptor()
        padded = decryptor.update(payload) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    """ 工具方法：cdn上传下载 """

    def parse_file_and_upload(
        self,
        file: Path,
        file_type: int,
        to_user_id: str,
    ) -> dict[str, Any]:
        file_md5 = hashlib.md5(file.read_bytes()).hexdigest()
        file_cache_tag = f"{file_md5}|{to_user_id}"

        if self.file_message_cache.get(file_cache_tag):
            file_cache: dict[str, Any] = self.file_message_cache[file_cache_tag]
            logger.debug(f"hit cache: {file_cache_tag}")
            return file_cache

        filekey = self.rand_file_key()
        aeskey = secrets.token_bytes(16)

        upload_request = self.get_upload_url(
            filekey,
            media_type=file_type,  # 文件上传的类型 1：图片 2：视频 3：文件 4：语音
            to_user_id=to_user_id,
            rawsize=file.stat().st_size,
            rawfilemd5=file_md5,
            filesize=((file.stat().st_size // 16) + 1) * 16,
            aeskey=aeskey.hex(),
        )
        logger.debug(upload_request)

        upload_param = upload_request["upload_param"]
        upload_payload = self.encrypt_aes_ecb(file.read_bytes(), aeskey)

        encrypt_query_param = self.upload_file_to_cdn(
            upload_param,
            filekey,
            upload_payload,
        )

        if not encrypt_query_param:
            return {"text": f"upload error: {file.name}"}

        media = {
            "encrypt_query_param": encrypt_query_param,
            "aes_key": base64.b64encode(aeskey.hex().encode()).decode(),
            "encrypt_type": 1,
        }

        self.file_message_cache[file_cache_tag] = media
        self.save_file_message(self.file_message_cache)
        logger.debug(f"save cache: {file_cache_tag}")

        return media

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

    def download_file_on_cdn(self): ...

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
        filekey: str,
        media_type: int,
        to_user_id: str,
        rawsize: int,
        rawfilemd5: str,
        filesize: int,
        aeskey: str,
    ):
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
            reply_to = message["from_user_id"]
            reply_ct = message["context_token"]

            reply = ilink.message_from_text(f"Hello World - {datetime.now()}")
            reply_resp = ilink.send_message(reply_to, reply_ct, reply)
            logger.info(reply_resp)

            reply = ilink.message_from_image("cache/images/哈基耶.jpg", reply_to)
            reply_resp = ilink.send_message(reply_to, reply_ct, reply)
            logger.info(reply_resp)

            reply = ilink.message_from_voice(
                "cache/voices/你好啊.wav",
                reply_to,
                encode_type=2,
                bits_per_sample=16,
                sample_rate=24_000,
                playtime=1000,
                text="你好啊",
            )
            reply_resp = ilink.send_message(reply_to, reply_ct, reply)
            logger.info(reply_resp)

            reply = ilink.message_from_file(
                "cache/files/protocol-spec.md",
                reply_to,
                file_name="protocol - spec.md",
            )
            reply_resp = ilink.send_message(reply_to, reply_ct, reply)
            logger.info(reply_resp)

            reply = ilink.message_from_video(
                "cache/videos/飞碟.mp4",
                reply_to,
                play_length=33000,
            )
            reply_resp = ilink.send_message(reply_to, reply_ct, reply)
            logger.info(reply_resp)
