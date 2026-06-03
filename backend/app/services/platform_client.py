"""算力网络平台接口客户端 — 封装对平台三个接口的 HTTP 调用。

接口列表：
- auth_check (2.4.2.2): 身份校验，用 code 换取平台 token
- get_user_info (2.4.2.3): 用平台 token 获取用户和租户信息
- send_heartbeat (2.4.2.4): 应用心跳（签名认证）
"""

import logging

import requests

from ..config import Config
from ..utils.signature import build_signed_headers

logger = logging.getLogger(__name__)

_TIMEOUT = 10  # 请求超时秒数


class PlatformError(Exception):
    """平台接口调用异常。"""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"[{code}] {msg}")


def _check_response(data: dict, action: str) -> dict:
    """检查平台返回的 code 是否为 20000，否则抛出 PlatformError。"""
    code = data.get("code")
    msg = data.get("msg", "未知错误")
    if code != 20000:
        logger.warning("平台接口 %s 返回失败: code=%s msg=%s", action, code, msg)
        raise PlatformError(code, msg)
    return data


def auth_check(code: str) -> str:
    """调用身份校验接口（2.4.2.2 appAuthCheck）。

    Args:
        code: 平台生成的随机码。

    Returns:
        平台 token 字符串。
    """
    url = Config.platform_url(f"/extral/{Config.PLATFORM_APP_CODE}/appAuthCheck")
    payload = {
        "appID": Config.PLATFORM_APP_ID,
        "appSecret": Config.PLATFORM_APP_SECRET,
        "code": code,
    }
    logger.info("调用平台身份校验接口: url=%s", url)
    resp = requests.post(url, json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    _check_response(data, "appAuthCheck")
    return data["data"]  # 平台 token 字符串


def get_user_info(platform_token: str) -> dict:
    """调用用户信息接口（2.4.2.3 getUserInfoByToken）。

    Args:
        platform_token: auth_check 返回的平台 token。

    Returns:
        包含 user 和 tenant 信息的字典。
        user: {loginLoginname, loginUname, ...}
        tenant: {tenantID, tenantAccount, tenantPassword}
    """
    url = Config.platform_url(f"/api/extral/{Config.PLATFORM_APP_CODE}/getUserInfoByToken")
    headers = {"Authorization": platform_token}
    payload = {"appID": Config.PLATFORM_APP_ID}
    logger.info("调用平台用户信息接口: url=%s", url)
    resp = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    _check_response(data, "getUserInfoByToken")
    return data["data"]


def send_heartbeat() -> dict:
    """调用应用心跳接口（2.4.2.4 heartbeat，签名认证）。

    Returns:
        平台响应字典。
    """
    url = Config.platform_url("/api/extra/v1/application/heartbeat")
    headers = build_signed_headers(Config.PLATFORM_APP_ID, Config.PLATFORM_APP_SECRET)
    logger.info("发送应用心跳: url=%s", url)
    resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 20000:
        logger.warning("心跳返回失败: code=%s msg=%s", data.get("code"), data.get("msg"))
    else:
        logger.info("心跳发送成功")
    return data
