import time
from typing import Any


class TypingManager:
    def __init__(
        self,
        typing_ticket_cache: dict[str, Any] | None = None,
        save_callback: Any = None,
    ) -> None:
        self.typing_ticket_cache = typing_ticket_cache or {}
        self.save_callback = save_callback

    def get_cached_ticket(self, ilink_user_id: str) -> str | None:
        now_time = time.time()
        typing_ticket = self.typing_ticket_cache.get(ilink_user_id)

        if typing_ticket and now_time < typing_ticket["valid_time"]:
            return typing_ticket["typing_ticket"]

        return None

    def cache_ticket(
        self, ilink_user_id: str, ticket: str, valid_hours: int = 24
    ) -> None:
        now_time = time.time()
        self.typing_ticket_cache[ilink_user_id] = {
            "typing_ticket": ticket,
            "valid_time": now_time + 60 * 60 * valid_hours,
        }

        if self.save_callback:
            self.save_callback(self.typing_ticket_cache)
