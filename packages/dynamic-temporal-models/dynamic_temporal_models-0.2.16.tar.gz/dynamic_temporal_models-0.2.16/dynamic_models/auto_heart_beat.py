import asyncio
import logging
from temporalio import activity
from typing import Callable


class AutoHeartbeat:
    def __init__(self, interval: int = 10):
        self.interval = interval
        self._stop_event = asyncio.Event()
        self._counter = 0
        self._task: asyncio.Task | None = None
        self._cancel_listeners: list[Callable[[], None]] = []

    async def _run(self):
        while not self._stop_event.is_set():
            try:
                if activity.is_cancelled():
                    raise asyncio.CancelledError()

                activity.heartbeat(self._counter)  # 👈 KHÔNG await
                logging.debug(f"[Heartbeat] Sent heartbeat #{self._counter}")
                self._counter += 1
            except asyncio.CancelledError as e:
                logging.info("[Heartbeat] Activity cancelled, notifying listeners")
                for cb in self._cancel_listeners:
                    cb()
                await self.stop()
                break
            except Exception as e:
                logging.warning(f"[Heartbeat error] {e}")
            await asyncio.sleep(self.interval)

    def add_cancel_listener(self, callback: Callable[[], None]):
        """Thêm callback khi activity bị cancel"""
        self._cancel_listeners.append(callback)

    async def start(self):
        if self._task is None:
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._stop_event.set()
            await self._task
            self._task = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
