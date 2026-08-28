"""ReAct 范式 —— Thought → Action → Observation 循环。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kodeagent.core.agent_hooks import AgentHooks, BeforeToolCallCtx, BeforeToolCallResult
from kodeagent.core.message import AgentMessage, convert_to_llm

if TYPE_CHECKING:
    from kodeagent.tools.base import Tool


def make_react_hooks(tools: list[Tool]) -> AgentHooks:
    """构造 ReAct 所需的 3 个核心 hook（可选 hook 保持 no-op）。"""
    tool_map = {t.name: t for t in tools}

    async def transform_context(messages: list[AgentMessage]) -> list[AgentMessage]:
        return messages

    async def _convert_to_llm(messages: list[AgentMessage]) -> list:
        return convert_to_llm(messages)

    async def before_tool_call(ctx: BeforeToolCallCtx) -> BeforeToolCallResult | None:
        if ctx.tool_name not in tool_map:
            return BeforeToolCallResult(block=True, reason=f"未知工具: {ctx.tool_name}")
        return None

    return AgentHooks(
        transform_context=transform_context,
        convert_to_llm=_convert_to_llm,
        before_tool_call=before_tool_call,
    )


__all__ = ["make_react_hooks"]
