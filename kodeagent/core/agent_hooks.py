"""AgentHooks 容器：3 必传 + 5 @property 可选。

整个 agent 的可扩展性集中在 hook 上。构造函数强制传 3 个核心 hook，
5 个可选 hook 用 @property 默认 no-op，覆写就生效。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .message import AgentMessage, LLMMessage


# ── hook 函数 Protocol ──────────────────────────────────────────────
class TransformContextFn(Protocol):
    """必传：LLM 调用前——注入长期记忆 / 压缩老消息 / 注入环境信息。"""

    async def __call__(self, messages: list[AgentMessage]) -> list[AgentMessage]: ...


class ConvertToLlmFn(Protocol):
    """必传：把 AgentMessage 转成 LLM 协议消息。"""

    async def __call__(self, messages: list[AgentMessage]) -> list[LLMMessage]: ...


@dataclass
class BeforeToolCallCtx:
    tool_name: str
    args: dict[str, Any]
    tool_call_id: str


@dataclass
class BeforeToolCallResult:
    block: bool = False
    reason: str = ""
    modified_args: dict[str, Any] | None = None


class BeforeToolCallFn(Protocol):
    """必传：拦截 / 修正 / 阻断工具调用。"""

    async def __call__(self, ctx: BeforeToolCallCtx) -> BeforeToolCallResult | None: ...


class ShouldStopFn(Protocol):
    async def __call__(self, messages: list[AgentMessage]) -> bool: ...


class PrepareNextTurnFn(Protocol):
    async def __call__(self, messages: list[AgentMessage]) -> list[AgentMessage] | None: ...


class SteeringFn(Protocol):
    async def __call__(self) -> list[AgentMessage]: ...


# ── 容器 ────────────────────────────────────────────────────────────
class AgentHooks:
    """v1 Hook 容器：3 必传 + 5 可选（@property 默认 no-op）。"""

    def __init__(
        self,
        transform_context: TransformContextFn,
        convert_to_llm: ConvertToLlmFn,
        before_tool_call: BeforeToolCallFn,
    ) -> None:
        self._transform_context = transform_context
        self._convert_to_llm = convert_to_llm
        self._before_tool_call = before_tool_call

    @property
    def transform_context(self) -> TransformContextFn:
        return self._transform_context

    @property
    def convert_to_llm(self) -> ConvertToLlmFn:
        return self._convert_to_llm

    @property
    def before_tool_call(self) -> BeforeToolCallFn:
        return self._before_tool_call

    # ── 4 可选 hook ──
    @property
    def should_stop_after_turn(self) -> ShouldStopFn:
        return _noop_should_stop

    @should_stop_after_turn.setter
    def should_stop_after_turn(self, fn: ShouldStopFn) -> None:
        self._should_stop_after_turn = fn

    @property
    def prepare_next_turn(self) -> PrepareNextTurnFn:
        return _noop_prepare_next

    @prepare_next_turn.setter
    def prepare_next_turn(self, fn: PrepareNextTurnFn) -> None:
        self._prepare_next_turn = fn

    @property
    def get_steering_messages(self) -> SteeringFn:
        return _noop_steering

    @get_steering_messages.setter
    def get_steering_messages(self, fn: SteeringFn) -> None:
        self._get_steering_messages = fn


async def _noop_should_stop(messages: list[AgentMessage]) -> bool:
    return False


async def _noop_prepare_next(messages: list[AgentMessage]) -> list[AgentMessage] | None:
    return None


async def _noop_steering() -> list[AgentMessage]:
    return []
