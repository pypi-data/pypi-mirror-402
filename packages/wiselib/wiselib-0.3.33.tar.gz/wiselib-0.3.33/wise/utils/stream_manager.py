import asyncio
from collections import defaultdict


class StreamManager:
    def __init__(self):
        self._connections = defaultdict(list)  # user_id -> [asyncio.Queue, ...]
        self._lock = asyncio.Lock()

    async def register(self, *dispatch_keys: str) -> asyncio.Queue:
        q = asyncio.Queue()  # type: ignore
        async with self._lock:
            for dispatch_key in dispatch_keys:
                self._connections[dispatch_key].append(q)
        return q

    async def unregister(self, dispatch_key: str, queue: asyncio.Queue):
        async with self._lock:
            lst = self._connections.get(dispatch_key)
            if not lst:
                return
            try:
                lst.remove(queue)
            except ValueError:
                pass
            if not lst:
                del self._connections[dispatch_key]

    async def send_event(self, dispatch_key: str, event):
        """Push event to all queues registered to user_id."""
        async with self._lock:
            queues = list(self._connections.get(dispatch_key, []))
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                except Exception:
                    pass
                try:
                    q.put_nowait(event)
                except Exception:
                    pass


stream_manager = StreamManager()
