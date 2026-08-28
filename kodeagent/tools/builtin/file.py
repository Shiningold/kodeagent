"""file_read / file_write / file_edit —— 内置文件工具。"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class FileReadArgs(BaseModel):
    path: str = Field(description="要读取的文件绝对路径或相对路径")
    start_line: int | None = Field(default=None, description="起始行（1-indexed，含）")
    end_line: int | None = Field(default=None, description="结束行（含）")


class FileReadTool(Tool):
    name = "file_read"
    description = "读取本地文件内容"

    @property
    def args_schema(self) -> type[BaseModel]:
        return FileReadArgs

    async def execute(self, **kwargs) -> ToolResult:
        args = FileReadArgs(**kwargs)
        p = Path(args.path)
        if not p.exists():
            return ToolResult(success=False, output="", error=f"文件不存在: {args.path}")
        text = p.read_text(encoding="utf-8")
        if args.start_line or args.end_line:
            lines = text.splitlines()
            text = "\n".join(lines[(args.start_line or 1) - 1 : args.end_line])
        return ToolResult(success=True, output=text)


class FileWriteArgs(BaseModel):
    path: str = Field(description="目标文件路径")
    content: str = Field(description="写入内容")


class FileWriteTool(Tool):
    name = "file_write"
    description = "写入文件（覆盖）"

    @property
    def args_schema(self) -> type[BaseModel]:
        return FileWriteArgs

    async def execute(self, **kwargs) -> ToolResult:
        args = FileWriteArgs(**kwargs)
        p = Path(args.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(args.content, encoding="utf-8")
        return ToolResult(success=True, output=f"已写入 {len(args.content)} 字符到 {args.path}")


class FileEditArgs(BaseModel):
    path: str = Field(description="目标文件路径")
    old_text: str = Field(description="要被替换的原文")
    new_text: str = Field(description="替换后的文本")


class FileEditTool(Tool):
    name = "file_edit"
    description = "精确替换文件中的指定文本"

    @property
    def args_schema(self) -> type[BaseModel]:
        return FileEditArgs

    async def execute(self, **kwargs) -> ToolResult:
        args = FileEditArgs(**kwargs)
        p = Path(args.path)
        if not p.exists():
            return ToolResult(success=False, output="", error=f"文件不存在: {args.path}")
        text = p.read_text(encoding="utf-8")
        if args.old_text not in text:
            return ToolResult(success=False, output="", error="未找到指定的 old_text")
        new_text = text.replace(args.old_text, args.new_text, 1)
        p.write_text(new_text, encoding="utf-8")
        return ToolResult(success=True, output=f"已编辑 {args.path}")


file_read = FileReadTool()
file_write = FileWriteTool()
file_edit = FileEditTool()
