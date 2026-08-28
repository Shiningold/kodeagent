"""事件类型定义 —— agent loop 产生，订阅者（TUI / headless / logger）消费。"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentEvent:
    type: str
    ts: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentStart(AgentEvent):
    type: str = "agent_start"


@dataclass
class TurnStart(AgentEvent):
    type: str = "turn_start"


@dataclass
class MessageStart(AgentEvent):
    type: str = "message_start"
    role: str = "assistant"
    content: str = ""


@dataclass
class MessageUpdate(AgentEvent):
    type: str = "message_update"
    delta: str = ""


@dataclass
class MessageEnd(AgentEvent):
    type: str = "message_end"
    role: str = "assistant"
    content: str = ""


@dataclass
class ToolExecutionStart(AgentEvent):
    type: str = "tool_execution_start"
    tool_call_id: str = ""
    tool_name: str = ""
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionEnd(AgentEvent):
    type: str = "tool_execution_end"
    tool_call_id: str = ""
    tool_name: str = ""
    success: bool = True
    output: str = ""
    error: str | None = None


@dataclass
class TurnEnd(AgentEvent):
    type: str = "turn_end"


@dataclass
class AgentEnd(AgentEvent):
    type: str = "agent_end"
