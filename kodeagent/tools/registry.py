"""工具注册 + 格式转换（OpenAI / Anthropic）。"""

from __future__ import annotations

from typing import Any

from .base import Tool, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"未注册工具: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def filter(self, whitelist: list[str]) -> ToolRegistry:
        """子 agent 用的白名单过滤。"""
        new = ToolRegistry()
        for name in whitelist:
            if name in self._tools:
                new._tools[name] = self._tools[name]
        return new

    def to_openai_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.args_schema.model_json_schema(),
                },
            }
            for t in self._tools.values()
        ]

    def to_anthropic_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.args_schema.model_json_schema(),
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, args: dict[str, Any], tool_call_id: str = "") -> dict[str, Any]:
        tool = self.get(name)
        try:
            validated = tool.args_schema(**args)
        except Exception as e:
            return ToolResult(success=False, output="", error=f"参数校验失败: {e}").to_dict()
        try:
            result = await tool.execute(**validated.model_dump())
            return result.to_dict()
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e)).to_dict()
