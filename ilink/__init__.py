"""
微信 iLink Bot API SDK

基于 ilink-protocol-spec.md 协议规范实现
"""

from .client import ILinkClient
from .models import (
    CDNMedia,
    TextItem,
    ImageItem,
    VoiceItem,
    FileItem,
    VideoItem,
    MessageItem,
    WeixinMessage,
)
from .crypto import encrypt_aes_ecb, decrypt_aes_ecb
from .cache import CacheManager
from .auth import AuthManager
from .api import APIClient
from .cdn import CDNClient
from .messages import MessageBuilder
from .typing import TypingManager

__version__ = "1.0.0"
__all__ = [
    "ILinkClient",
    "CDNMedia",
    "TextItem",
    "ImageItem",
    "VoiceItem",
    "FileItem",
    "VideoItem",
    "MessageItem",
    "WeixinMessage",
    "encrypt_aes_ecb",
    "decrypt_aes_ecb",
    "CacheManager",
    "AuthManager",
    "APIClient",
    "CDNClient",
    "MessageBuilder",
    "TypingManager",
]
