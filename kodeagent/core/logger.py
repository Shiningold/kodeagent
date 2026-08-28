"""轻量结构化日志 —— stdlib logging + JSON，不引第三方依赖。"""

import json
import logging
import time
from typing import Any

# 敏感 key 模式：命中则值替换为 ***REDACTED***
_SENSITIVE_KEYS = ("api_key", "token", "secret", "password", "authorization")


def _redact(value: Any) -> Any:
    """递归脱敏：仅按 dict key 名匹配。

    ponytail: 不扫字符串内容——"sk-" 误杀正常文本，且真实 key 都走 dict 字段。
    若未来出现非 dict 携带明文 key，在此加规则，不提前扫全量字符串。
    """
    if isinstance(value, dict):
        return {k: "***REDACTED***" if _is_sensitive(k) else _redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def _is_sensitive(key: str) -> bool:
    k = key.lower()
    return any(s in k for s in _SENSITIVE_KEYS)


class StructuredLogger:
    """每条 log 一行 JSON，方便 grep / awk。"""

    def __init__(self, name: str = "kodeagent", level: int = logging.INFO) -> None:
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
        self.logger.setLevel(level)

    def log(self, event: str, **fields: Any) -> None:
        record = {"ts": int(time.time() * 1000), "event": event, **_redact(fields)}
        self.logger.info(json.dumps(record, ensure_ascii=False))

    def warning(self, msg: str) -> None:
        self.logger.warning(json.dumps({"ts": int(time.time() * 1000), "event": "warning", "msg": msg}))

    def error(self, msg: str, **fields: Any) -> None:
        record = {"ts": int(time.time() * 1000), "event": "error", "msg": msg, **_redact(fields)}
        self.logger.error(json.dumps(record, ensure_ascii=False))


log = StructuredLogger()
