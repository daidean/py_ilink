from datetime import datetime
from loguru import logger
from ilink import ILinkClient

ilink = ILinkClient()

while True:
    get_updates_buf = ilink.cache.get_login_info()["get_updates_buf"]
    updates = ilink.get_updates(get_updates_buf)
    logger.info(updates)

    ilink.cache.login_info_cache["get_updates_buf"] = updates["get_updates_buf"]
    ilink.cache.save_login_info(ilink.cache.login_info_cache)

    if not updates["msgs"]:
        continue

    for message in updates["msgs"]:
        logger.info(message)
        reply_to = message["from_user_id"]
        reply_ct = message["context_token"]

        reply = ilink.message_from_text(f"Hello World - {datetime.now()}")
        ilink.send_message(reply_to, reply_ct, reply)

        reply = ilink.message_from_image("assets/哈基耶.jpg", reply_to)
        ilink.send_message(reply_to, reply_ct, reply)
