"""
Outbox Worker Module

Background service for processing outbox events.
Uses MongoDB Change Streams for real-time reactivity with polling fallback.
"""

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from app.logging_config import get_logger
from app.models.outbox_event import OutboxEvent

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class OutboxWorker:
    """
    Worker for processing outbox events.
    """

    def __init__(self, polling_interval: float = 5.0) -> None:
        """
        Initialize the worker.

        Args:
            polling_interval: Seconds to wait between polling cycles.
        """
        from app.repositories.outbox_repository import get_outbox_repository

        self._repo = get_outbox_repository()
        self._polling_interval = polling_interval
        self._running = False
        self._processors: dict[str, Callable[[OutboxEvent], Coroutine[Any, Any, None]]] = {}
        self._task: asyncio.Task[None] | None = None

    def register_handler(self, event_type: str, handler: Callable[[OutboxEvent], Coroutine[Any, Any, None]]) -> None:
        """
        Register a handler for a specific event type.

        Args:
            event_type: Event type string.
            handler: Async function to process the event.
        """
        self._processors[event_type] = handler
        logger.debug(f"Registered handler for event type: {event_type}")

    async def start(self) -> None:
        """Start the worker in the background."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("OutboxWorker started")

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        logger.info("OutboxWorker stopped")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                # Process pending events
                await self._process_batch()

                # Wait before next batch
                await asyncio.sleep(self._polling_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in outbox worker loop: {e}", exc_info=True)
                await asyncio.sleep(self._polling_interval)

    async def _process_batch(self, limit: int = 10) -> None:
        """Process a batch of pending events."""
        events = await self._repo.get_pending_events(limit)

        if not events:
            return

        logger.debug(f"Processing batch of {len(events)} events")

        results = await asyncio.gather(*[self._process_event(event) for event in events], return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing event {events[i].id}: {result}")

    async def _process_event(self, event: OutboxEvent) -> None:
        """
        Process a single event.

        Args:
            event: The event object.
        """
        # 1. Mark as processing
        if not await self._repo.mark_as_processing(event.id):
            # Already picked up by another worker
            return

        handler = self._processors.get(event.event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event.event_type}")
            await self._repo.mark_as_failed(event.id, "No handler registered")
            return

        try:
            # 2. Execute handler
            await handler(event)

            # 3. Mark as completed
            await self._repo.mark_as_completed(event.id)
            logger.info(f"Event processed successfully: {event.id}")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e!s}"
            logger.error(f"Failed to process event {event.id}: {error_msg}")

            # 4. Handle failure (retry or DLQ)
            await self._repo.mark_as_failed(event.id, error_msg)


_worker_instance: OutboxWorker | None = None


def get_outbox_worker() -> OutboxWorker:
    """Get global OutboxWorker instance."""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = OutboxWorker()
    return _worker_instance
