from logging import Logger
from typing import Collection, Optional

from buz.event import Event
from buz.event.async_event_bus import AsyncEventBus
from buz.event.infrastructure.buz_kafka.base_async_buz_kafka_event_bus import BaseAsyncBuzKafkaEventBus
from buz.event.infrastructure.buz_kafka.publish_strategy.publish_strategy import KafkaPublishStrategy
from buz.event.middleware.async_publish_middleware import AsyncPublishMiddleware
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.services.async_kafka_producer import AsyncKafkaProducer
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.infrastructure.serializers.partitiion_key_generator import PartitionKeySerializer


class AsyncBuzKafkaEventBus(BaseAsyncBuzKafkaEventBus, AsyncEventBus):
    """
    Async Kafka event bus with simple behavior (consistent with sync version).

    - Returns None from bulk_publish
    - Raises exception on failure
    - No retry logic
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

    async def bulk_publish(self, events: Collection[Event]) -> None:
        """Publish all events sequentially. Raises exception on first failure."""
        for event in events:
            await self.publish(event)
