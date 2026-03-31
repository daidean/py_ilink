from typing import Any


class CDNMedia:
    def __init__(
        self,
        encrypt_query_param: str = "",
        aes_key: str = "",
        encrypt_type: int = 1,
    ) -> None:
        self.encrypt_query_param = encrypt_query_param
        self.aes_key = aes_key
        self.encrypt_type = encrypt_type

    def to_dict(self) -> dict[str, Any]:
        return {
            "encrypt_query_param": self.encrypt_query_param,
            "aes_key": self.aes_key,
            "encrypt_type": self.encrypt_type,
        }


class TextItem:
    def __init__(self, text: str = "") -> None:
        self.text = text

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text}


class ImageItem:
    def __init__(
        self,
        media: CDNMedia | None = None,
        thumb_media: CDNMedia | None = None,
        aeskey: str = "",
        mid_size: int = 0,
        thumb_size: int = 0,
        thumb_width: int = 0,
        thumb_height: int = 0,
        hd_size: int = 0,
    ) -> None:
        self.media = media
        self.thumb_media = thumb_media
        self.aeskey = aeskey
        self.mid_size = mid_size
        self.thumb_size = thumb_size
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height
        self.hd_size = hd_size

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.media:
            result["media"] = self.media.to_dict()
        if self.thumb_media:
            result["thumb_media"] = self.thumb_media.to_dict()
        if self.aeskey:
            result["aeskey"] = self.aeskey
        if self.mid_size:
            result["mid_size"] = self.mid_size
        if self.thumb_size:
            result["thumb_size"] = self.thumb_size
        if self.thumb_width:
            result["thumb_width"] = self.thumb_width
        if self.thumb_height:
            result["thumb_height"] = self.thumb_height
        if self.hd_size:
            result["hd_size"] = self.hd_size
        return result


class VoiceItem:
    def __init__(
        self,
        media: CDNMedia | None = None,
        encode_type: int = 0,
        bits_per_sample: int = 0,
        sample_rate: int = 0,
        playtime: int = 0,
        text: str = "",
    ) -> None:
        self.media = media
        self.encode_type = encode_type
        self.bits_per_sample = bits_per_sample
        self.sample_rate = sample_rate
        self.playtime = playtime
        self.text = text

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.media:
            result["media"] = self.media.to_dict()
        if self.encode_type:
            result["encode_type"] = self.encode_type
        if self.bits_per_sample:
            result["bits_per_sample"] = self.bits_per_sample
        if self.sample_rate:
            result["sample_rate"] = self.sample_rate
        if self.playtime:
            result["playtime"] = self.playtime
        if self.text:
            result["text"] = self.text
        return result


class FileItem:
    def __init__(
        self,
        media: CDNMedia | None = None,
        file_name: str = "",
        md5: str = "",
        len: str = "",
    ) -> None:
        self.media = media
        self.file_name = file_name
        self.md5 = md5
        self.len = len

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.media:
            result["media"] = self.media.to_dict()
        if self.file_name:
            result["file_name"] = self.file_name
        if self.md5:
            result["md5"] = self.md5
        if self.len:
            result["len"] = self.len
        return result


class VideoItem:
    def __init__(
        self,
        media: CDNMedia | None = None,
        video_size: int = 0,
        video_md5: str = "",
        play_length: int = 0,
        thumb_media: CDNMedia | None = None,
        thumb_size: int = 0,
        thumb_width: int = 0,
        thumb_height: int = 0,
    ) -> None:
        self.media = media
        self.video_size = video_size
        self.video_md5 = video_md5
        self.play_length = play_length
        self.thumb_media = thumb_media
        self.thumb_size = thumb_size
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.media:
            result["media"] = self.media.to_dict()
        if self.video_size:
            result["video_size"] = self.video_size
        if self.video_md5:
            result["video_md5"] = self.video_md5
        if self.play_length:
            result["play_length"] = self.play_length
        if self.thumb_media:
            result["thumb_media"] = self.thumb_media.to_dict()
        if self.thumb_size:
            result["thumb_size"] = self.thumb_size
        if self.thumb_width:
            result["thumb_width"] = self.thumb_width
        if self.thumb_height:
            result["thumb_height"] = self.thumb_height
        return result


class MessageItem:
    TYPE_TEXT = 1
    TYPE_IMAGE = 2
    TYPE_VOICE = 3
    TYPE_FILE = 4
    TYPE_VIDEO = 5

    def __init__(
        self,
        type: int = TYPE_TEXT,
        text_item: TextItem | None = None,
        image_item: ImageItem | None = None,
        voice_item: VoiceItem | None = None,
        file_item: FileItem | None = None,
        video_item: VideoItem | None = None,
    ) -> None:
        self.type = type
        self.text_item = text_item
        self.image_item = image_item
        self.voice_item = voice_item
        self.file_item = file_item
        self.video_item = video_item

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type}
        if self.text_item:
            result["text_item"] = self.text_item.to_dict()
        if self.image_item:
            result["image_item"] = self.image_item.to_dict()
        if self.voice_item:
            result["voice_item"] = self.voice_item.to_dict()
        if self.file_item:
            result["file_item"] = self.file_item.to_dict()
        if self.video_item:
            result["video_item"] = self.video_item.to_dict()
        return result


class WeixinMessage:
    MESSAGE_TYPE_USER = 1
    MESSAGE_TYPE_BOT = 2
    MESSAGE_STATE_NEW = 0
    MESSAGE_STATE_GENERATING = 1
    MESSAGE_STATE_FINISH = 2

    def __init__(self, data: dict[str, Any]) -> None:
        self.seq: int | None = data.get("seq")
        self.message_id: int | None = data.get("message_id")
        self.from_user_id: str | None = data.get("from_user_id")
        self.to_user_id: str | None = data.get("to_user_id")
        self.client_id: str | None = data.get("client_id")
        self.create_time_ms: int | None = data.get("create_time_ms")
        self.update_time_ms: int | None = data.get("update_time_ms")
        self.delete_time_ms: int | None = data.get("delete_time_ms")
        self.session_id: str | None = data.get("session_id")
        self.group_id: str | None = data.get("group_id")
        self.message_type: int | None = data.get("message_type")
        self.message_state: int | None = data.get("message_state")
        self.context_token: str | None = data.get("context_token")
        self.item_list: list[dict[str, Any]] = data.get("item_list", [])
