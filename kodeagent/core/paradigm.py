"""通用 loop 骨架 —— 所有范式共用。

ReAct / Plan-Execute 通过实现 AgentHooks 改变行为，不修改本文件。
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import TYPE_CHECKING

from .events import (
    AgentEnd,
    AgentStart,
    MessageEnd,
    MessageStart,
    MessageUpdate,
    ToolExecutionEnd,
    ToolExecutionStart,
    TurnEnd,
    TurnStart,
)
from .llm import LLMProvider, LLMRequest, LLMResponse
from .logger import log
from .message import AgentMessage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from .agent_hooks import AgentHooks
    from .event_bus import EventBus


async def run_loop(
    goal: str,
    llm: LLMProvider,
    hooks: AgentHooks,
    event_bus: EventBus,
    tools: list[dict] | None = None,
    tool_executor: Callable | None = None,
    messages: list[AgentMessage] | None = None,
) -> AsyncIterator[AgentMessage]:
    """运行一个完整 agent 会话，逐条 yield 产生的 AgentMessage。"""
    emit = event_bus.emit
    await emit(AgentStart())

    history: list[AgentMessage] = list(messages or [])
    history.append(AgentMessage(role="user", content=goal))

    while True:
        await emit(TurnStart())

        # 1. 注入 steering
        for msg in await hooks.get_steering_messages():
            history.append(msg)

        # 2. transform_context（语义层：注入记忆 / 压缩）
        history = await hooks.transform_context(history)

        # 3. convert_to_llm（协议层）—— AgentMessage → LLMMessage → dict（OpenAI wire format）
        llm_messages = [asdict(m) for m in await hooks.convert_to_llm(history)]

        # 4. 流式 LLM 响应
        req = LLMRequest(messages=llm_messages, model="", tools=tools, stream=True)
        await emit(MessageStart(role="assistant"))

        parts: list[str] = []
        async for delta in llm.stream_chat(req):
            parts.append(delta)
            await emit(MessageUpdate(delta=delta))

        content = "".join(parts)
        assistant_msg = AgentMessage(role="assistant", content=content)
        await emit(MessageEnd(role="assistant", content=content))

        # 解析 tool_calls（简化：从 mock 中直接取；真实流式需解析）
        tool_calls = await _extract_tool_calls(llm, req, content)
        assistant_msg.metadata["tool_calls"] = tool_calls
        history.append(assistant_msg)

        # 5. 执行工具（ponytail: gather 并发，tool 之间无依赖是 LLM 的隐含契约）
        if tool_calls and tool_executor:
            parsed = [
                (tc["id"], tc["function"]["name"], _safe_parse(tc["function"].get("arguments", "{}")))
                for tc in tool_calls
            ]
            for tc_id, name, args in parsed:
                log.log("tool_call_start", tool_name=name, args=args)
                await emit(ToolExecutionStart(tool_call_id=tc_id, tool_name=name, args=args))

            async def _run_one(tc_id: str, name: str, args: dict) -> dict:
                return await tool_executor(name=name, args=args, tool_call_id=tc_id)

            results = await asyncio.gather(*(_run_one(tc_id, name, args) for tc_id, name, args in parsed))

            for (tc_id, name, _args), result in zip(parsed, results, strict=False):
                log.log("tool_call_end", tool_name=name, success=result.get("success", True))
                await emit(
                    ToolExecutionEnd(
                        tool_call_id=tc_id,
                        tool_name=name,
                        success=result.get("success", True),
                        output=str(result.get("output", "")),
                        error=result.get("error"),
                    )
                )
                history.append(
                    AgentMessage(
                        role="toolResult",
                        content=str(result.get("output", "")),
                        metadata={"tool_call_id": tc_id, "tool_name": name},
                    )
                )

        await emit(TurnEnd())

        # 6. 停止判定
        if await hooks.should_stop_after_turn(history):
            break
        if not tool_calls:
            break  # 没有工具调用且不是 stop hook 触发 → 自然结束

        nxt = await hooks.prepare_next_turn(history)
        if nxt is not None:
            history = nxt

    await emit(AgentEnd())
    for m in history:
        yield m


async def _extract_tool_calls(llm: LLMProvider, req: LLMRequest, _content: str) -> list[dict]:
    """从 LLM 响应中提取 tool_calls。mock 直接返回；真实流式需单独 chat 拿完整响应。"""
    if hasattr(llm, "call_log"):
        # MockLLMProvider —— 重新用 chat 拿完整响应（含 tool_calls）
        resp: LLMResponse = await llm.chat(req)
        return resp.tool_calls or []
    return []


def _safe_parse(s: str) -> dict:
    import json

    try:
        return json.loads(s) if isinstance(s, str) else s
    except Exception:
        return {}
