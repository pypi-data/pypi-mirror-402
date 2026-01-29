from logging import Logger
from typing import Collection, Optional

from buz.event import Event
from buz.event.async_event_bus_with_publish_result import AsyncEventBusWithPublishResult
from buz.event.event_bus_publish_result import EventBusPublishResult
from buz.event.infrastructure.buz_kafka.base_async_buz_kafka_event_bus import BaseAsyncBuzKafkaEventBus
from buz.event.infrastructure.buz_kafka.publish_strategy.publish_strategy import KafkaPublishStrategy
from buz.event.middleware.async_publish_middleware import AsyncPublishMiddleware
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.services.async_kafka_producer import AsyncKafkaProducer
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.infrastructure.serializers.partitiion_key_generator import PartitionKeySerializer


class AsyncBuzKafkaEventBusWithPublishResult(BaseAsyncBuzKafkaEventBus, AsyncEventBusWithPublishResult):
    """
    Kafka event bus with publish result tracking and fail-fast behavior.

    Features:
    - Returns EventBusPublishResult with published/failed events
    - Fail-fast behavior (stops on first failure)
    - Partial success tracking for external state management
    """

    def __init__(
        self,
        *,
        publish_strategy: KafkaPublishStrategy,
        producer: AsyncKafkaProducer,
        logger: Logger,
        kafka_admin_client: Optional[KafkaAdminClient] = None,
        publish_middlewares: Optional[list[AsyncPublishMiddleware]] = None,
        auto_create_topic_configuration: Optional[AutoCreateTopicConfiguration] = None,
        partition_key_generator: Optional[PartitionKeySerializer] = None,
    ):
        super().__init__(
            publish_strategy=publish_strategy,
            producer=producer,
            logger=logger,
            kafka_admin_client=kafka_admin_client,
            publish_middlewares=publish_middlewares,
            auto_create_topic_configuration=auto_create_topic_configuration,
            partition_key_generator=partition_key_generator,
        )

    async def bulk_publish(self, events: Collection[Event]) -> EventBusPublishResult:
        """
        Publish events one by one with fail-fast behavior.

        Publishes events sequentially. If any event fails, stops immediately and returns the result with:
        - published_events: All events successfully published before the failure
        - failed_events: The first event that failed (only one event)

        This allows the caller to track which events were sent and which were not,
        enabling proper state management in external systems.

        Note: Kafka automatically handles partition assignment based on partition_key.
        Events with the same partition_key will go to the same partition and maintain order.

        Returns:
            EventBusPublishResult with published_events and failed_events
        """
        published_events: list[Event] = []
        failed_events: list[Event] = []

        # FAIL-FAST: Stop on first failure
        for event in events:
            try:
                await self.publish(event)
                published_events.append(event)
            except Exception as exc:
                self._logger.error(f"Failed to publish event {event.id}. Error: {exc}")
                failed_events.append(event)
                break

        return EventBusPublishResult(
            published_events=published_events,
            failed_events=failed_events,
        )
