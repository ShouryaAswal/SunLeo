from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Awaitable, Callable, Optional


class InMemoryJobQueue:
    def __init__(self, concurrency: int = 3) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_tasks: list[asyncio.Task] = []
        self._worker: Optional[Callable[[str], Awaitable[None]]] = None
        self._running = False
        self._concurrency = concurrency

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)

    def start(self, worker: Callable[[str], Awaitable[None]]) -> None:
        if self._running:
            return
        self._worker = worker
        self._running = True
        
        # Spin up multiple worker tasks to process the queue in parallel
        for _ in range(self._concurrency):
            task = asyncio.create_task(self._run())
            self._worker_tasks.append(task)

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
        for task in self._worker_tasks:
            task.cancel()
        if self._worker_tasks:
            with suppress(asyncio.CancelledError):
                await asyncio.gather(*self._worker_tasks)
        self._worker_tasks = []
