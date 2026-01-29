"""Base class for streaming connection handlers.

Stream handlers maintain persistent connections to external services
(WebSockets, Server-Sent Events, etc.) and emit events for workflow triggers.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StreamSubscription(BaseModel):
    """Subscription data from the database."""

    id: str
    workflow_id: str
    node_id: str
    stream_type: str
    credential_id: str | None
    connection_config: dict[str, Any]
    event_filter: dict[str, Any] | None
    status: str
    project_id: str


class StreamHandler(ABC):
    """Base class for streaming connection handlers.

    Subclasses implement specific protocol handling (Mattermost WS, Slack RTM, etc.)
    while this base class provides:
    - Reconnection logic with exponential backoff
    - Event filtering
    - Graceful shutdown

    Example usage:

        from flowire_sdk import StreamHandler, StreamSubscription

        class MyServiceHandler(StreamHandler):
            async def connect(self):
                credential = await self.resolve_credential()
                # Connect to service...

            async def disconnect(self):
                # Close connection...

            async def listen(self):
                async for message in self.connection:
                    yield {"event": "message", "data": message}
    """

    def __init__(
        self,
        subscription: StreamSubscription,
        event_callback: Callable[[StreamSubscription, dict[str, Any]], Coroutine[Any, Any, None]],
        credential_resolver: Callable[[str], Coroutine[Any, Any, dict[str, Any]]],
        metrics_tracker: Any | None = None,
    ):
        """Initialize handler.

        Args:
            subscription: Subscription data from database
            event_callback: Async callback to invoke when events arrive
            credential_resolver: Async function to resolve credential by ID
            metrics_tracker: Optional metrics tracker for observability
        """
        self.subscription = subscription
        self.event_callback = event_callback
        self.credential_resolver = credential_resolver
        self.metrics = metrics_tracker
        self.connected = False
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 300.0
        self._stop_event = asyncio.Event()

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to external service.

        Implementations should:
        1. Resolve credentials via self.credential_resolver
        2. Connect to the service
        3. Authenticate if required

        Raises:
            Exception: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close connection."""
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[dict[str, Any]]:
        """Yield events from the connection.

        Yields:
            Event dictionaries from the external service
        """
        yield {}  # Type hint helper, implementations override completely

    async def resolve_credential(self) -> dict[str, Any]:
        """Resolve the subscription's credential.

        Returns:
            Decrypted credential data

        Raises:
            ValueError: If no credential_id configured
        """
        if not self.subscription.credential_id:
            raise ValueError("No credential configured for subscription")
        return await self.credential_resolver(self.subscription.credential_id)

    def should_forward(self, event: dict[str, Any]) -> bool:
        """Check if event matches subscription's filter.

        Args:
            event: Event data from the stream

        Returns:
            True if event should be forwarded to workflow
        """
        event_filter = self.subscription.event_filter
        if not event_filter:
            return True

        # Check event type filter
        if "events" in event_filter:
            event_type = event.get("event") or event.get("type")
            if event_type not in event_filter["events"]:
                return False

        # Check channel filter
        if "channels" in event_filter and event_filter["channels"]:
            channel_id = event.get("channel_id") or event.get("channel")
            if channel_id not in event_filter["channels"]:
                return False

        return True

    async def run(self) -> None:
        """Main loop with reconnection logic.

        Runs until stop() is called. Handles reconnection with
        exponential backoff on failures.
        """
        # Track handler instance start
        if self.metrics:
            self.metrics.handler_started(self.subscription.stream_type)

        try:
            await self._run_loop()
        finally:
            # Track handler instance stop
            if self.metrics:
                self.metrics.handler_stopped(self.subscription.stream_type)

    async def _run_loop(self) -> None:
        """Internal run loop, separated for clean metrics tracking."""
        is_reconnect = False

        while not self._stop_event.is_set():
            try:
                # Track reconnection attempt
                if is_reconnect and self.metrics:
                    self.metrics.reconnection_attempt(self.subscription.stream_type)

                await self.connect()
                self.connected = True
                self.reconnect_delay = 1.0  # Reset on successful connect

                # Track successful connection
                if self.metrics:
                    self.metrics.connection_success(
                        self.subscription.id,
                        self.subscription.stream_type,
                    )

                logger.info(
                    "Connected: subscription=%s stream_type=%s",
                    self.subscription.id,
                    self.subscription.stream_type,
                )

                async for event in self.listen():
                    if self._stop_event.is_set():
                        break

                    # Track received event
                    if self.metrics:
                        event_type = event.get("event") or event.get("type")
                        self.metrics.event_received(
                            self.subscription.stream_type,
                            event_type,
                        )

                    if self.should_forward(event):
                        try:
                            await self.event_callback(self.subscription, event)
                        except Exception as e:
                            logger.error(
                                "Event callback failed: subscription=%s error=%s",
                                self.subscription.id,
                                e,
                            )
                    elif self.metrics:
                        self.metrics.event_filtered(self.subscription.stream_type)

            except asyncio.CancelledError:
                logger.info("Handler cancelled: subscription=%s", self.subscription.id)
                break

            except Exception as e:
                logger.error(
                    "Handler error: subscription=%s error=%s",
                    self.subscription.id,
                    e,
                )
                self.connected = False

                # Track connection failure
                if self.metrics:
                    error_type = type(e).__name__
                    self.metrics.connection_error(
                        self.subscription.id,
                        self.subscription.stream_type,
                        error_type,
                    )

            finally:
                try:
                    await self.disconnect()
                except Exception as e:
                    logger.warning("Disconnect error: %s", e)

                self.connected = False

            if self._stop_event.is_set():
                break

            # Mark as reconnect attempt for next iteration
            is_reconnect = True

            # Exponential backoff with jitter
            jitter = random.uniform(0, self.reconnect_delay * 0.1)
            delay = self.reconnect_delay + jitter
            logger.info(
                "Reconnecting in %.1fs: subscription=%s",
                delay,
                self.subscription.id,
            )

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=delay,
                )
                # Stop event was set during wait
                break
            except TimeoutError:
                # Normal timeout, continue to reconnect
                pass

            self.reconnect_delay = min(
                self.reconnect_delay * 2,
                self.max_reconnect_delay,
            )

    def stop(self) -> None:
        """Signal the handler to stop."""
        self._stop_event.set()
