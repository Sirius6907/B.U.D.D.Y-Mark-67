from __future__ import annotations

import asyncio
from typing import Awaitable, Callable


class ExecutionWatchdog:
    async def monitor(
        self,
        task: asyncio.Task,
        timeout: float,
        on_timeout: Callable[[str], Awaitable[None] | None],
    ) -> bool:
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
            return False
        except asyncio.TimeoutError:
            task.cancel()
            result = on_timeout(f"Task exceeded timeout of {timeout:.2f}s")
            if asyncio.iscoroutine(result):
                await result
            return True
