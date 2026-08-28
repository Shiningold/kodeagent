"""Phase 1 冒烟测试 —— 验证 agent loop + event bus 端到端。"""

from __future__ import annotations

import pytest

from kodeagent.agents.react import make_react_hooks
from kodeagent.core.agent import Agent
from kodeagent.core.event_bus import EventBus
from kodeagent.core.events import AgentStart, TurnStart
from kodeagent.core.llm import LLMRequest, MockLLMProvider


@pytest.mark.asyncio
async def test_mock_stream(mock_llm: MockLLMProvider) -> None:
    """MockLLMProvider 流式返回完整内容。"""
    req = LLMRequest(messages=[{"role": "user", "content": "hello"}], model="")
    chunks: list[str] = [chunk async for chunk in mock_llm.stream_chat(req)]
    assert "".join(chunks) == "hi there"


@pytest.mark.asyncio
async def test_event_bus_drain() -> None:
    """close 后队列事件被排空，不丢弃。"""
    bus = EventBus()
    collected: list[str] = []

    class Sub:
        async def on_event(self, event) -> None:
            collected.append(type(event).__name__)

    bus.subscribe(Sub())

    async def run() -> None:

        await bus.emit(AgentStart())
        await bus.emit(TurnStart())
        bus.close()
        await bus.dispatch_loop()

    await run()
    assert collected == ["AgentStart", "TurnStart"]


@pytest.mark.asyncio
async def test_agent_run_end_to_end(mock_llm: MockLLMProvider) -> None:
    """Agent.run 完整跑完，产出 agent_start + agent_end，history 有 user + assistant。"""
    events: list[str] = []

    class Sub:
        async def on_event(self, event) -> None:
            events.append(type(event).__name__)

    bus = EventBus()
    bus.subscribe(Sub())

    hooks = make_react_hooks([])
    agent = Agent(llm=mock_llm, hooks=hooks, event_bus=bus)

    msgs = [m async for m in agent.run("hello")]

    assert "AgentStart" in events
    assert "AgentEnd" in events
    assert any(m.role == "user" for m in msgs)
    assert any(m.role == "assistant" for m in msgs)


@pytest.mark.asyncio
async def test_prompt_returns_text(mock_llm: MockLLMProvider) -> None:
    """Agent.prompt 返回最终 assistant 文本。"""
    agent = Agent(llm=mock_llm, hooks=make_react_hooks([]))
    result = await agent.prompt("hello")
    assert result == "hi there"
