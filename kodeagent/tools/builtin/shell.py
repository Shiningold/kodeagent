"""shell_exec —— 带安全策略的 shell 执行（v1 基础版：超时 + 危险命令拦截）。"""

from __future__ import annotations

import asyncio

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult

# 危险命令前缀 —— 需人工确认（v1 直接拦截，阶段 3 加 TUI 确认）
_DANGEROUS = ("rm -rf", "sudo", "shutdown", "reboot", "mkfs", "dd if=", ":(){:|:&};:")


class ShellExecArgs(BaseModel):
    command: str = Field(description="要执行的 shell 命令")
    timeout: int = Field(default=30, description="超时秒数")


class ShellExecTool(Tool):
    name = "shell_exec"
    description = "执行 shell 命令（带超时与基础安全策略）"

    @property
    def args_schema(self) -> type[BaseModel]:
        return ShellExecArgs

    async def execute(self, **kwargs) -> ToolResult:
        args = ShellExecArgs(**kwargs)
        cmd = args.command.strip()
        for d in _DANGEROUS:
            if cmd.startswith(d) or d in cmd:
                return ToolResult(success=False, output="", error=f"危险命令被拦截: {d}")
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=args.timeout)
            output = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")
            success = proc.returncode == 0
            return ToolResult(
                success=success,
                output=output,
                error=err if err else None,
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(success=False, output="", error=f"命令超时（{args.timeout}s）")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


shell_exec = ShellExecTool()
