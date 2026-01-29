from abc import abstractmethod

from buz.event import Event
from buz.event.middleware.async_publish_middleware import AsyncPublishCallable, AsyncPublishMiddleware


class BaseAsyncPublishMiddleware(AsyncPublishMiddleware):
    """
    Base class for async publish middlewares with before/after hooks.
    Provides a template pattern for middleware that need to execute logic
    before and after event publishing.
    """

    async def on_publish(self, event: Event, publish: AsyncPublishCallable) -> None:
        await self._before_on_publish(event)
        await publish(event)
        await self._after_on_publish(event)

    @abstractmethod
    async def _before_on_publish(self, event: Event) -> None:
        """Hook executed before publishing the event."""
        pass

    @abstractmethod
    async def _after_on_publish(self, event: Event) -> None:
        """Hook executed after publishing the event."""
        pass
