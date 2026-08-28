"""Agent 基类 —— hook 组装 + 事件流入口。"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .event_bus import EventBus
from .paradigm import run_loop

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .agent_hooks import AgentHooks
    from .llm import LLMProvider
    from .message import AgentMessage


class Agent:
    def __init__(
        self,
        llm: LLMProvider,
        hooks: AgentHooks,
        event_bus: EventBus | None = None,
        tools: list[dict] | None = None,
        tool_executor=None,
    ) -> None:
        self.llm = llm
        self.hooks = hooks
        self.event_bus = event_bus or EventBus()
        self.tools = tools
        self.tool_executor = tool_executor

    async def run(self, goal: str) -> AsyncIterator[AgentMessage]:
        dispatch_task = None
        if self.event_bus.subscriber_count() > 0:
            dispatch_task = asyncio.create_task(self.event_bus.dispatch_loop())
        try:
            async for msg in run_loop(
                goal=goal,
                llm=self.llm,
                hooks=self.hooks,
                event_bus=self.event_bus,
                tools=self.tools,
                tool_executor=self.tool_executor,
            ):
                yield msg
        finally:
            self.event_bus.close()
            if dispatch_task:
                await dispatch_task

    async def prompt(self, goal: str) -> str:
        """简化入口：跑完一轮，返回最终 assistant 文本。"""
        result = ""
        async for msg in self.run(goal):
            if msg.role == "assistant":
                result = msg.content
        return result
