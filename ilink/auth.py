import time
import requests
from typing import Any
from loguru import logger


class AuthManager:
    def __init__(self, endpoint: str = "https://ilinkai.weixin.qq.com") -> None:
        self.endpoint = endpoint

    def get_qr_code(self) -> dict[str, Any]:
        qr_get_path = "/ilink/bot/get_bot_qrcode?bot_type=3"
        qr_get_url = f"{self.endpoint}{qr_get_path}"
        qr = requests.post(qr_get_url).json()
        logger.info(f"BOT未登录, 待授权二维码信息: {qr}")
        return qr

    def poll_qr_status(self, qr_code: str) -> dict[str, Any]:
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

    def login(self) -> dict[str, Any]:
        qr = self.get_qr_code()
        qr_code, qr_link = qr["qrcode"], qr["qrcode_img_content"]

        try:
            from qrcode import QRCode

            qr_img = QRCode()
            qr_img.add_data(qr_link)
            qr_img.print_ascii()
        except ImportError:
            logger.warning("qrcode library not installed, please scan manually")
            logger.info(f"QR Code URL: {qr_link}")

        logger.info("BOT未登录, 等待扫描二维码授权")
        return self.poll_qr_status(qr_code)
