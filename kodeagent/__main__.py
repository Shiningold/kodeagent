"""CLI 入口 —— `python -m kodeagent "你好"` 或 `kodeagent "你好"`。"""

from __future__ import annotations

import argparse
import asyncio
from typing import TYPE_CHECKING

from .agents.react import make_react_hooks
from .core.agent import Agent
from .core.event_bus import EventBus
from .core.llm import MockLLMProvider, OpenAIProvider
from .core.logger import StructuredLogger, log
from .tools.builtin import file_edit, file_read, file_write
from .tools.builtin.shell import shell_exec
from .tools.registry import ToolRegistry

if TYPE_CHECKING:
    from .tools.base import Tool


def _build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    for t in (file_read, file_write, file_edit, shell_exec):
        reg.register(t)
    return reg


def _build_agent(mock: bool = False) -> tuple[Agent, list[Tool]]:
    reg = _build_registry()
    tools = [file_read, file_write, file_edit, shell_exec]
    hooks = make_react_hooks(tools)

    llm = MockLLMProvider() if mock else OpenAIProvider()
    event_bus = EventBus()

    async def on_event(event) -> None:
        d = event.to_dict()
        t = d.pop("type")
        if t == "message_update":
            print(d.get("delta", ""), end="", flush=True)
        elif t == "message_end":
            print()
        elif t == "tool_execution_start":
            print(f"  🔧 {d.get('tool_name')}({d.get('args')})")
        elif t in ("agent_start", "agent_end"):
            log.log(t)

    class _Sub:
        async def on_event(self, event) -> None:
            await on_event(event)

    event_bus.subscribe(_Sub())

    async def tool_executor(name: str, args: dict, tool_call_id: str = "") -> dict:
        return await reg.execute(name=name, args=args, tool_call_id=tool_call_id)

    agent = Agent(llm=llm, hooks=hooks, event_bus=event_bus, tools=reg.to_openai_tools(), tool_executor=tool_executor)
    return agent, tools


async def _run(goal: str, mock: bool) -> None:
    agent, _ = _build_agent(mock=mock)
    await agent.prompt(goal)


def main() -> None:
    parser = argparse.ArgumentParser(prog="kodeagent", description="KodeAgent CLI")
    parser.add_argument("goal", nargs="*", help="要执行的目标 / 问题")
    parser.add_argument("--mock", action="store_true", help="使用 MockLLM（无需 API key）")
    parser.add_argument("--verbose", action="store_true", help="详细日志")
    args = parser.parse_args()

    if args.verbose:
        StructuredLogger().logger.setLevel("INFO")

    goal = " ".join(args.goal) if args.goal else "你好，介绍下你自己"
    asyncio.run(_run(goal, mock=args.mock))


if __name__ == "__main__":
    main()
