from logging import Logger
from typing import Optional

from buz.event import Event
from buz.event.exceptions.event_not_published_exception import EventNotPublishedException
from buz.event.infrastructure.buz_kafka.exceptions.kafka_event_bus_config_not_valid_exception import (
    KafkaEventBusConfigNotValidException,
)
from buz.event.infrastructure.buz_kafka.publish_strategy.publish_strategy import KafkaPublishStrategy
from buz.event.middleware.async_publish_middleware import AsyncPublishMiddleware
from buz.event.middleware.async_publish_middleware_chain_resolver import AsyncPublishMiddlewareChainResolver
from buz.kafka.domain.exceptions.topic_already_created_exception import KafkaTopicsAlreadyCreatedException
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.models.create_kafka_topic import CreateKafkaTopic
from buz.kafka.domain.services.async_kafka_producer import AsyncKafkaProducer
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient
from buz.kafka.infrastructure.serializers.implementations.cdc_partition_key_serializer import CDCPartitionKeySerializer
from buz.kafka.infrastructure.serializers.partitiion_key_generator import PartitionKeySerializer


class BaseAsyncBuzKafkaEventBus:
    """
    Base class for async Kafka event buses with common functionality.

    Provides:
    - Event publishing with middleware support
    - Topic auto-creation
    - Partition key generation
    - Connection management
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
        self._publish_middleware_chain_resolver = AsyncPublishMiddlewareChainResolver(publish_middlewares or [])
        self._publish_strategy = publish_strategy
        self._producer = producer
        self._topics_checked: dict[str, bool] = {}
        self._kafka_admin_client = kafka_admin_client
        self._auto_create_topic_configuration = auto_create_topic_configuration
        self._logger = logger
        self._partition_key_generator: PartitionKeySerializer = partition_key_generator or CDCPartitionKeySerializer()
        self._check_kafka_admin_client_is_needed()

    def _check_kafka_admin_client_is_needed(self) -> None:
        if self._kafka_admin_client is None and self._auto_create_topic_configuration is not None:
            raise KafkaEventBusConfigNotValidException(
                "A KafkaAdminClient is needed to create topics when 'auto_create_topic_configuration' is set."
            )

    async def publish(self, event: Event) -> None:
        """Publish a single event through the middleware chain."""
        await self._publish_middleware_chain_resolver.resolve(event, self._perform_publish)

    async def _perform_publish(self, event: Event) -> None:
        try:
            topic = self._publish_strategy.get_topic(event)

            if self._auto_create_topic_configuration is not None and self._is_topic_created(topic) is False:
                try:
                    self._logger.info(f"Creating missing topic: {topic}..")
                    self._get_kafka_admin_client().create_topics(
                        topics=[
                            CreateKafkaTopic(
                                name=topic,
                                partitions=self._auto_create_topic_configuration.partitions,
                                replication_factor=self._auto_create_topic_configuration.replication_factor,
                                configs=self._auto_create_topic_configuration.configs,
                            )
                        ]
                    )
                    self._logger.info(f"Created missing topic: {topic}")
                    self._topics_checked[topic] = True
                except KafkaTopicsAlreadyCreatedException:
                    pass

            headers = self._get_event_headers(event)
            await self._producer.produce(
                message=event,
                headers=headers,
                topic=topic,
                partition_key=self._partition_key_generator.generate_key(event),
            )
        except Exception as exc:
            raise EventNotPublishedException(event) from exc

    def _get_kafka_admin_client(self) -> KafkaAdminClient:
        if self._kafka_admin_client is None:
            raise KafkaEventBusConfigNotValidException("KafkaAdminClient is not set.")
        return self._kafka_admin_client

    def _is_topic_created(self, topic: str) -> bool:
        is_topic_created = self._topics_checked.get(topic, None)

        if is_topic_created is not None:
            return is_topic_created

        is_topic_created = self._get_kafka_admin_client().is_topic_created(topic)
        self._topics_checked[topic] = is_topic_created

        return is_topic_created

    def _get_event_headers(self, event: Event) -> dict:
        return {"id": event.id}

    async def connect(self) -> None:
        await self._producer.connect()

    async def disconnect(self) -> None:
        await self._producer.disconnect()
