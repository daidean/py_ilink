import time
import base64
import secrets


def rand_uin() -> str:
    rand_n = secrets.token_bytes(4)
    rand_s = base64.b64encode(rand_n).decode()
    return rand_s


def rand_file_key(byte_count: int = 16) -> str:
    return secrets.token_hex(byte_count)


def time_ms() -> int:
    return int(time.time() * 1000)


def generate_client_id() -> str:
    return f"openclaw-weixin:{time_ms()}-{secrets.token_hex(4)}"
