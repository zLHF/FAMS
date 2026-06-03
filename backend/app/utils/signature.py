"""HMAC-SHA256 签名工具 — 用于算网平台签名认证。

签名规则（参照手册 2.4.1.2）：
1. 生成 13 位毫秒级时间戳 x-time
2. 生成 16 位随机字符串 x-random
3. POST 请求：对 body 做 MD5 得出 x-body；GET 请求：参数按 key 降序排列 & 拼接后做 MD5
4. 拼接字符串：x-body={x-body}&x-random={x-random}&x-time={x-time}（无参数时不拼接 x-body 部分）
5. HMAC-SHA256(app_secret, 拼接字符串) 得到 x-sign
"""

import hashlib
import hmac
import secrets
import string


def md5_hex(text: str) -> str:
    """计算字符串的 MD5 十六进制摘要。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def generate_random_string(length: int = 16) -> str:
    """生成由数字和小写字母组成的随机字符串。"""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_signature(body_str: str, random_str: str, timestamp: str, app_secret: str) -> str:
    """根据签名规则生成 HMAC-SHA256 签名。

    Args:
        body_str: 已计算的 x-body 值（MD5 十六进制），无参数时为空字符串。
        random_str: x-random 值。
        timestamp: x-time 值（13 位毫秒时间戳字符串）。
        app_secret: 应用密钥。

    Returns:
        签名十六进制字符串。
    """
    # 拼接字符串：有 body 时为 x-body={body}&x-random={random}&x-time={timestamp}
    # 无 body 时为 x-random={random}&x-time={timestamp}
    if body_str:
        sign_str = f"x-body={body_str}&x-random={random_str}&x-time={timestamp}"
    else:
        sign_str = f"x-random={random_str}&x-time={timestamp}"

    return hmac.new(
        app_secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def compute_body_for_post(body: str) -> str:
    """POST 请求：对 body 字符串做 MD5 得出 x-body。"""
    if not body:
        return ""
    return md5_hex(body)


def compute_body_for_get(params: dict) -> str:
    """GET 请求：参数按 key 降序排列并以 & 拼接，然后做 MD5 得出 x-body。"""
    if not params:
        return ""
    sorted_items = sorted(params.items(), key=lambda x: x[0], reverse=True)
    query_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    return md5_hex(query_str)


def build_signed_headers(app_key: str, app_secret: str, body_str: str = "") -> dict:
    """构建签名认证所需的请求 Header。

    Args:
        app_key: 应用 ID（appKey / appID）。
        app_secret: 应用密钥。
        body_str: 已计算的 x-body 值，无参数时为空字符串。

    Returns:
        包含 appKey、x-random、x-time、x-sign 的 Header 字典。
    """
    import time

    timestamp = str(int(time.time() * 1000))  # 13 位毫秒时间戳
    random_str = generate_random_string(16)
    sign = generate_signature(body_str, random_str, timestamp, app_secret)

    return {
        "appKey": app_key,
        "x-random": random_str,
        "x-time": timestamp,
        "x-sign": sign,
    }
