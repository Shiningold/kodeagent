"""双类型消息：AgentMessage（内部） + LLMMessage（协议）。

内部状态变化（压缩、记忆注入、skill）不污染 LLM 协议消息。
UI 渲染只看 AgentMessage，不需要知道 LLM 协议细节。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class AgentMessage:
    """Agent 内部消息——可以是标准 LLM 消息，也可以是应用扩展类型。"""

    role: str
    content: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    """LLM 协议消息——只包含 LLM 能理解的类型。"""

    role: Literal["user", "assistant", "toolResult"]
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


def convert_to_llm(messages: list[AgentMessage]) -> list[LLMMessage]:
    """LLM 调用前过滤 + 转换——所有扩展类型在这里处理。"""
    result: list[LLMMessage] = []
    for m in messages:
        if m.role in ("user", "assistant", "toolResult"):
            result.append(
                LLMMessage(
                    role=m.role,
                    content=m.content,
                    tool_call_id=m.metadata.get("tool_call_id"),
                    tool_calls=m.metadata.get("tool_calls"),
                )
            )
        elif m.role == "compaction":
            result.append(LLMMessage(role="user", content=f"<previous_summary>\n{m.content}\n</previous_summary>"))
        elif m.role == "memory_inject":
            result.append(LLMMessage(role="user", content=f"<relevant_memories>\n{m.content}\n</relevant_memories>"))
        elif m.role in ("skill_result", "user_steering"):
            pass  # 内部信号，不发给 LLM
    return result
