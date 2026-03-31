import base64
import hashlib
import secrets
from typing import Any
from pathlib import Path
from loguru import logger

from .auth import AuthManager
from .api import APIClient
from .cdn import CDNClient
from .crypto import encrypt_aes_ecb
from .cache import CacheManager
from .messages import MessageBuilder
from .typing import TypingManager


class ILinkClient:
    endpoint: str = "https://ilinkai.weixin.qq.com"
    cdn_endpoint: str = "https://novac2c.cdn.weixin.qq.com"

    def __init__(
        self,
        cache_dir: str = "cache",
    ) -> None:
        self.cache = CacheManager(
            login_info_path=f"{cache_dir}/bot_login_info.json",
            typing_ticket_path=f"{cache_dir}/bot_typing_ticket.json",
            file_message_path=f"{cache_dir}/bot_upload_files.json",
        )

        self.auth = AuthManager(self.endpoint)
        self.api = APIClient(self.endpoint)
        self.cdn = CDNClient(self.cdn_endpoint)
        self.messages = MessageBuilder()
        self.typing = TypingManager(
            typing_ticket_cache=self.cache.get_typing_ticket(),
            save_callback=self.cache.save_typing_ticket,
        )

        self._init_from_cache()

    def _init_from_cache(self) -> None:
        login_info = self.cache.get_login_info()
        if login_info.get("bot_token"):
            self.api.update_credentials(
                bot_token=login_info["bot_token"],
                ilink_bot_id=login_info["ilink_bot_id"],
            )
            logger.info("BOT登录, 已加载登录缓存")
        else:
            logger.warning("BOT登录, 未找到登录缓存")

    def login(self) -> dict[str, Any]:
        login_info = self.auth.login()
        if login_info:
            self.cache.save_login_info(login_info)
            self.api.update_credentials(
                bot_token=login_info["bot_token"],
                ilink_bot_id=login_info["ilink_bot_id"],
            )
        return login_info

    def save_login_info(self, login_info: dict[str, Any]) -> None:
        self.cache.save_login_info(login_info)

    def get_updates(self, get_updates_buf: str = "") -> dict[str, Any]:
        return self.api.get_updates(get_updates_buf)

    def send_message(
        self,
        to_user_id: str,
        context_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        return self.api.send_message(to_user_id, context_token, message)

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
        return self.api.get_upload_url(
            filekey, media_type, to_user_id, rawsize, rawfilemd5, filesize, aeskey
        )

    def get_config(self, ilink_user_id: str, context_token: str) -> dict[str, Any]:
        return self.api.get_config(ilink_user_id, context_token)

    def send_typing(
        self,
        ilink_user_id: str,
        typing_ticket: str,
        status: int,
    ) -> dict[str, Any]:
        return self.api.send_typing(ilink_user_id, typing_ticket, status)

    def get_typing_ticket(self, ilink_user_id: str, context_token: str) -> str:
        cached = self.typing.get_cached_ticket(ilink_user_id)
        if cached:
            return cached

        resp = self.get_config(ilink_user_id, context_token)
        ticket = resp.get("typing_ticket", "")
        if ticket:
            self.typing.cache_ticket(ilink_user_id, ticket)
        return ticket

    def parse_file_and_upload(
        self,
        file: Path,
        file_type: int,
        to_user_id: str,
    ) -> dict[str, Any]:
        try:
            import pilk
        except ImportError:
            pilk = None

        if file_type == 4 and file.as_posix().endswith(".wav"):
            if pilk is None:
                logger.error("pilk library not installed, cannot convert wav to silk")
                return {"text": f"upload error: pilk not installed"}
            silk_path = file.as_posix().replace(".wav", ".silk")
            pilk.encode(file.as_posix(), silk_path)
            file = Path(silk_path)

        file_md5 = hashlib.md5(file.read_bytes()).hexdigest()
        file_cache_tag = f"{file_md5}|{to_user_id}"

        file_cache = self.cache.get_file_message()
        if file_cache.get(file_cache_tag):
            logger.debug(f"hit cache: {file_cache_tag}")
            return file_cache[file_cache_tag]

        filekey = secrets.token_hex(16)
        aeskey = secrets.token_bytes(16)

        upload_request = self.get_upload_url(
            filekey,
            media_type=file_type,
            to_user_id=to_user_id,
            rawsize=file.stat().st_size,
            rawfilemd5=file_md5,
            filesize=((file.stat().st_size // 16) + 1) * 16,
            aeskey=aeskey.hex(),
        )
        logger.debug(upload_request)

        upload_param = upload_request["upload_param"]
        upload_payload = encrypt_aes_ecb(file.read_bytes(), aeskey)

        encrypt_query_param = self.cdn.upload_file_to_cdn(
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

        file_cache[file_cache_tag] = media
        self.cache.save_file_message(file_cache)
        logger.debug(f"save cache: {file_cache_tag}")

        return media

    def message_from_text(self, message: str) -> dict[str, Any]:
        return self.messages.message_from_text(message)

    def message_from_image(self, file_path: str, to_user_id: str) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.messages.message_from_text(f"<img {file_path}>")

        media = self.parse_file_and_upload(
            file=file,
            file_type=1,
            to_user_id=to_user_id,
        )

        return self.messages.message_from_image_media(media)

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
            return self.messages.message_from_text(f"<voice {file_path}>")

        media = self.parse_file_and_upload(
            file=file,
            file_type=4,
            to_user_id=to_user_id,
        )

        return self.messages.message_from_voice_media(
            media=media,
            encode_type=encode_type,
            bits_per_sample=bits_per_sample,
            sample_rate=sample_rate,
            playtime=playtime,
            text=text,
        )

    def message_from_file(
        self,
        file_path: str,
        to_user_id: str,
        file_name: str,
    ) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.messages.message_from_text(f"<file {file_path}>")

        file_md5 = hashlib.md5(file.read_bytes()).hexdigest()
        file_len = f"{file.stat().st_size}"

        media = self.parse_file_and_upload(
            file=file,
            file_type=3,
            to_user_id=to_user_id,
        )

        return self.messages.message_from_file_media(
            media=media,
            file_name=file_name,
            md5=file_md5,
            file_len=file_len,
        )

    def message_from_video(
        self,
        file_path: str,
        to_user_id: str,
        play_length: int = 0,
    ) -> dict[str, Any]:
        file = Path(file_path)
        if not file.exists():
            return self.messages.message_from_text(f"<video {file_path}>")

        file_md5 = hashlib.md5(file.read_bytes()).hexdigest()
        file_len = file.stat().st_size

        media = self.parse_file_and_upload(
            file=file,
            file_type=2,
            to_user_id=to_user_id,
        )

        return self.messages.message_from_video_media(
            media=media,
            video_size=file_len,
            video_md5=file_md5,
            play_length=play_length,
        )
