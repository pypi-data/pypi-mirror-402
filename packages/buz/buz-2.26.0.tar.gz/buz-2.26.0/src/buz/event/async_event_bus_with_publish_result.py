from abc import ABC, abstractmethod
from typing import Collection

from buz.event import Event
from buz.event.event_bus_publish_result import EventBusPublishResult
from buz.kafka.infrastructure.interfaces.async_connection_manager import AsyncConnectionManager


class AsyncEventBusWithPublishResult(AsyncConnectionManager, ABC):
    """
    Event bus with publish result tracking capabilities.

    Unlike AsyncEventBus which returns None, this event bus returns
    EventBusPublishResult to report which events succeeded and which failed.

    This enables:
    - Partial success tracking
    - Fail-fast behavior with precise tracking
    - Application-level retry control
    - Better observability
    """

    @abstractmethod
    async def publish(self, event: Event) -> None:
        pass

    @abstractmethod
    async def bulk_publish(self, events: Collection[Event]) -> EventBusPublishResult:
        """
        Publish multiple events and return detailed results.

        Returns:
            EventBusPublishResult containing published_events and failed_events
        """
        pass
