"""Tool Protocol + ToolResult。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pydantic import BaseModel


@dataclass
class ToolResult:
    """工具执行结果。"""

    success: bool
    output: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }


@runtime_checkable
class Tool(Protocol):
    """工具 Protocol——v1 必传 name/description/args_schema。"""

    name: str
    description: str

    @property
    def args_schema(self) -> type[BaseModel]:
        """pydantic BaseModel 子类——描述参数结构。"""
        ...

    async def execute(self, **kwargs: Any) -> ToolResult:
        """实际执行逻辑。kwargs 已由 args_schema 校验。"""
        ...
