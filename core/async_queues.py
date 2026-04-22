from __future__ import annotations

import asyncio


def enqueue_latest(queue: asyncio.Queue, item: object) -> bool:
    """
    Keep the newest item when a bounded queue overflows.
    Returns True when the item is queued, False only if it still cannot be queued.
    """
    try:
        queue.put_nowait(item)
        return True
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass

        try:
            queue.put_nowait(item)
            return True
        except asyncio.QueueFull:
            return False
