"""钉钉机器人消息推送（迁移自 wifi-monitor/dingtalk.py）。

设计说明：
- 仅依赖 Python 标准库（urllib），无需在 requirements.txt 中新增 requests；
- 自动处理钉钉自定义机器人的「加签」安全设置；
- 任何网络/协议异常都不向上抛出，返回 (ok, message)，供调用方决定是否落库告警。
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
from typing import Tuple


def _build_signed_url(webhook: str, secret: str) -> str:
    """按钉钉规则拼接 timestamp + sign 参数。"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))
    sep = "&" if "?" in webhook else "?"
    return f"{webhook}{sep}timestamp={timestamp}&sign={sign}"


def send_dingtalk(webhook: str, secret: str, text: str, timeout: int = 5) -> Tuple[bool, str]:
    """发送钉钉文本消息。

    返回 (是否成功, 说明信息)，永不抛异常，便于后台任务安全调用。
    """
    if not webhook:
        return False, "未配置钉钉 Webhook"
    url = _build_signed_url(webhook, secret) if secret else webhook
    payload = json.dumps({"msgtype": "text", "text": {"content": text}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("errcode") == 0:
            return True, "发送成功"
        return False, result.get("errmsg") or str(result)
    except Exception as e:  # noqa: BLE001 - 推送失败不应影响主流程
        return False, str(e)
