"""LLM Provider 抽象 —— OpenAI / Anthropic / Ollama 薄包装。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

from .config import settings
from .exceptions import AuthError, ProviderError
from .logger import log

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@dataclass
class LLMRequest:
    messages: list[dict[str, Any]]
    model: str
    tools: list[dict[str, Any]] | None = None
    max_tokens: int = 4000
    temperature: float = 0.7
    stream: bool = False


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    stop_reason: str = "end_turn"  # end_turn | tool_use | length
    usage: dict[str, int] | None = None


class LLMProvider(Protocol):
    async def chat(self, request: LLMRequest) -> LLMResponse: ...
    def stream_chat(self, request: LLMRequest) -> AsyncGenerator[str, None]: ...


class OpenAIProvider:
    """包装 openai SDK，兼容 OpenAI / Ollama（OpenAI 协议）。"""

    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None) -> None:
        import openai

        self.model = model or settings.openai_model
        self.base_url = base_url or (
            settings.ollama_base_url if settings.llm_provider == "ollama" else settings.openai_base_url
        )
        # Ollama 不需要真实 key
        final_key = "ollama" if settings.llm_provider == "ollama" else (
            settings.openai_api_key.get_secret_value() if settings.openai_api_key else "sk-missing"
        )
        if settings.llm_provider == "openai" and not settings.openai_api_key:
            raise AuthError("OPENAI_API_KEY 未配置，请检查 .env")
        self.client = openai.AsyncOpenAI(api_key=final_key, base_url=self.base_url)

    async def chat(self, request: LLMRequest) -> LLMResponse:
        log.log("llm_request", model=self.model, messages_count=len(request.messages), stream=False)
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=cast("Any", request.messages),
                tools=cast("Any", request.tools),
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False,
            )
        except Exception as e:
            raise ProviderError(f"LLM 调用失败: {e}") from e

        choice = resp.choices[0]
        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,  # type: ignore[attr-defined]
                        "arguments": tc.function.arguments,  # type: ignore[attr-defined]
                    },
                }
                for tc in choice.message.tool_calls
                if hasattr(tc, "function")
            ]
        usage = None
        if resp.usage:
            usage = {"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens}
        log.log("llm_response", model=self.model, stop_reason=choice.finish_reason, usage=usage)
        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "end_turn",
            usage=usage,
        )

    async def stream_chat(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        log.log("llm_request", model=self.model, messages_count=len(request.messages), stream=True)
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=cast("Any", request.messages),
            tools=cast("Any", request.tools),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class MockLLMProvider:
    """确定性 mock —— 按消息特征返回预设响应。用于测试和无 key 场景。"""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.responses = responses or {}
        self.call_log: list[list[dict[str, Any]]] = []

    async def chat(self, request: LLMRequest) -> LLMResponse:
        self.call_log.append(request.messages)
        last = request.messages[-1].get("content", "") if request.messages else ""
        for pattern, response in self.responses.items():
            if pattern in str(last):
                return LLMResponse(content=response, stop_reason="end_turn")
        return LLMResponse(content="<mock echo: " + str(last)[:80] + ">", stop_reason="end_turn")

    async def stream_chat(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        resp = await self.chat(request)
        yield resp.content
