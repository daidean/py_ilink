from typing import Any


class MessageBuilder:
    def __init__(self) -> None:
        pass

    @staticmethod
    def message_from_text(message: str) -> dict[str, Any]:
        return {
            "type": 1,
            "text_item": {"text": message},
        }

    @staticmethod
    def message_from_image_media(media: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": 2,
            "image_item": {"media": media},
        }

    @staticmethod
    def message_from_voice_media(
        media: dict[str, Any],
        encode_type: int = 0,
        bits_per_sample: int = 0,
        sample_rate: int = 0,
        playtime: int = 0,
        text: str = "",
    ) -> dict[str, Any]:
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

    @staticmethod
    def message_from_file_media(
        media: dict[str, Any],
        file_name: str,
        md5: str,
        file_len: str,
    ) -> dict[str, Any]:
        file_item = {
            "media": media,
            "file_name": file_name,
            "md5": md5,
            "len": file_len,
        }

        return {
            "type": 4,
            "file_item": file_item,
        }

    @staticmethod
    def message_from_video_media(
        media: dict[str, Any],
        video_size: int,
        video_md5: str,
        play_length: int = 0,
    ) -> dict[str, Any]:
        video_item = {
            "media": media,
            "video_size": video_size,
            "video_md5": video_md5,
        }

        if play_length != 0:
            video_item.update({"play_length": play_length})

        return {
            "type": 5,
            "video_item": video_item,
        }
