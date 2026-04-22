import asyncio

from core.async_queues import enqueue_latest


def test_enqueue_latest_adds_item_when_queue_has_space():
    queue = asyncio.Queue(maxsize=2)

    accepted = enqueue_latest(queue, "frame-1")

    assert accepted is True
    assert queue.get_nowait() == "frame-1"


def test_enqueue_latest_drops_oldest_when_queue_is_full():
    queue = asyncio.Queue(maxsize=2)
    queue.put_nowait("frame-1")
    queue.put_nowait("frame-2")

    accepted = enqueue_latest(queue, "frame-3")

    assert accepted is True
    assert queue.get_nowait() == "frame-2"
    assert queue.get_nowait() == "frame-3"
