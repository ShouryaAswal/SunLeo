from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Awaitable, Callable, Optional


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._worker: Optional[Callable[[str], Awaitable[None]]] = None
        self._running = False

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)

    def start(self, worker: Callable[[str], Awaitable[None]]) -> None:
        if self._running:
            return
        self._worker = worker
        self._running = True
        self._worker_task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while self._running:
            job_id = await self._queue.get()
            try:
                if self._worker:
                    await self._worker(job_id)
            finally:
                self._queue.task_done()

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker_task
