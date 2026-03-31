import json
from typing import Any
from pathlib import Path
from loguru import logger


class CacheManager:
    def __init__(
        self,
        login_info_path: str = "cache/bot_login_info.json",
        typing_ticket_path: str = "cache/bot_typing_ticket.json",
        file_message_path: str = "cache/bot_upload_files.json",
    ) -> None:
        self.login_info_path = Path(login_info_path)
        self.typing_ticket_path = Path(typing_ticket_path)
        self.file_message_path = Path(file_message_path)

        self.login_info_cache = self._load_login_info()
        self.typing_ticket_cache = self._load_typing_ticket()
        self.file_message_cache = self._load_file_message()

    def _load_login_info(self) -> dict[str, Any]:
        if not self.login_info_path.exists():
            return {}
        return json.loads(self.login_info_path.read_text())

    def save_login_info(self, login_info: dict[str, Any]) -> None:
        self.login_info_cache = login_info
        self.login_info_path.parent.mkdir(parents=True, exist_ok=True)
        self.login_info_path.write_text(json.dumps(login_info))

    def _load_typing_ticket(self) -> dict[str, Any]:
        if not self.typing_ticket_path.exists():
            return {}
        return json.loads(self.typing_ticket_path.read_text())

    def save_typing_ticket(self, typing_ticket: dict[str, Any]) -> None:
        self.typing_ticket_cache = typing_ticket
        self.typing_ticket_path.parent.mkdir(parents=True, exist_ok=True)
        self.typing_ticket_path.write_text(json.dumps(typing_ticket))

    def _load_file_message(self) -> dict[str, Any]:
        if not self.file_message_path.exists():
            return {}
        return json.loads(self.file_message_path.read_text())

    def save_file_message(self, file_message: dict[str, Any]) -> None:
        self.file_message_cache = file_message
        self.file_message_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_message_path.write_text(json.dumps(file_message))

    def get_login_info(self) -> dict[str, Any]:
        return self.login_info_cache

    def get_typing_ticket(self) -> dict[str, Any]:
        return self.typing_ticket_cache

    def get_file_message(self) -> dict[str, Any]:
        return self.file_message_cache
