"""EventBus —— asyncio.Queue 广播 + N 订阅者。

单线程异步，避免 GIL；慢订阅者不阻塞 agent loop（queue 满则丢 + warning）。
close() 仅停止接收新事件，已在队列中的事件会被 dispatch 排空后再退出。
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Protocol

from .logger import log

if TYPE_CHECKING:
    from .events import AgentEvent


class EventSubscriber(Protocol):
    async def on_event(self, event: AgentEvent) -> None: ...


class EventBus:
    def __init__(self, maxsize: int = 1000) -> None:
        self._queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue(maxsize=maxsize)
        self._subscribers: list[EventSubscriber] = []
        self._closed = False

    def subscribe(self, sub: EventSubscriber) -> None:
        self._subscribers.append(sub)

    def subscriber_count(self) -> int:
        return len(self._subscribers)

    async def emit(self, event: AgentEvent) -> None:
        if self._closed:
            return
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            log.warning(f"queue full, dropped {type(event).__name__}")
        # put_nowait 是同步的，不会让出控制权；必须显式 yield，
        # 否则 dispatch 任务在本协程（run_loop）结束前永远得不到执行。
        await asyncio.sleep(0)

    async def dispatch_loop(self) -> None:
        """循环分发事件。仅靠 None 哨兵退出，确保 close 前入队的事件被排空。"""
        while True:
            event = await self._queue.get()
            if event is None:
                break
            if not self._subscribers:
                continue
            await asyncio.gather(
                *(sub.on_event(event) for sub in self._subscribers),
                return_exceptions=True,
            )

    def close(self) -> None:
        """关闭入队，并投递 None 哨兵让 dispatch 在排空后退出。"""
        self._closed = True
        with contextlib.suppress(asyncio.QueueFull):
            self._queue.put_nowait(None)
