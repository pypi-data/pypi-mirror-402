"""Kafka consumer for receiving requests."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Coroutine
from uuid import UUID

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.errors import KafkaError

from mem_common.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class IncomingRequest:
    """A request received from Kafka."""

    request_id: UUID
    service_name: str
    payload: dict[str, Any]
    sticky_key_value: str | None
    partition: int
    offset: int
    timestamp: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": str(self.request_id),
            "service_name": self.service_name,
            "payload": self.payload,
            "sticky_key_value": self.sticky_key_value,
            "partition": self.partition,
            "offset": self.offset,
            "timestamp": self.timestamp,
        }


class KafkaConsumer:
    """Kafka consumer for receiving service requests.

    Features:
    - Manual offset commits for at-least-once delivery
    - Sticky routing via partition assignment
    - Graceful shutdown with offset commit
    """

    def __init__(
        self,
        service_name: str,
        group_id: str | None = None,
        bootstrap_servers: str | None = None,
    ):
        self._service_name = service_name
        self._settings = get_settings()
        self._bootstrap_servers = (
            bootstrap_servers or self._settings.kafka_bootstrap_servers
        )
        self._group_id = (
            group_id or f"{self._settings.kafka_consumer_group_prefix}-{service_name}"
        )
        self._topic = f"memrun.requests.{service_name}"
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False
        self._pending_offsets: dict[TopicPartition, int] = {}

    async def start(self) -> None:
        """Start the Kafka consumer."""
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            enable_auto_commit=False,  # Manual commits for at-least-once
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            f"Started Kafka consumer for topic '{self._topic}' "
            f"with group '{self._group_id}'"
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer and commit pending offsets."""
        self._running = False
        if self._consumer:
            # Commit any pending offsets before stopping
            await self._commit_pending()
            await self._consumer.stop()
            self._consumer = None
            logger.info("Stopped Kafka consumer")

    async def consume(self) -> AsyncIterator[IncomingRequest]:
        """Consume requests from Kafka.

        Yields:
            IncomingRequest for each message.

        Usage:
            async for request in consumer.consume():
                result = await process(request)
                await consumer.ack(request)
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not started")

        while self._running:
            try:
                # Fetch messages with timeout
                result = await self._consumer.getmany(
                    timeout_ms=1000,
                    max_records=100,
                )

                for tp, messages in result.items():
                    for msg in messages:
                        try:
                            request = IncomingRequest(
                                request_id=UUID(msg.value["request_id"]),
                                service_name=msg.value["service_name"],
                                payload=msg.value["payload"],
                                sticky_key_value=msg.key,
                                partition=msg.partition,
                                offset=msg.offset,
                                timestamp=msg.timestamp,
                            )
                            yield request
                        except (KeyError, ValueError) as e:
                            logger.error(f"Failed to parse message: {e}")
                            # Still track offset to avoid re-processing
                            self._pending_offsets[tp] = msg.offset + 1

            except KafkaError as e:
                logger.error(f"Kafka error: {e}")
                await asyncio.sleep(1)

    async def ack(self, request: IncomingRequest) -> None:
        """Acknowledge a request (mark for commit).

        The offset will be committed on the next commit cycle.
        """
        tp = TopicPartition(self._topic, request.partition)
        self._pending_offsets[tp] = request.offset + 1

    async def commit(self) -> None:
        """Commit all pending offsets."""
        await self._commit_pending()

    async def _commit_pending(self) -> None:
        """Commit pending offsets to Kafka."""
        if self._consumer is None or not self._pending_offsets:
            return

        try:
            await self._consumer.commit(
                {tp: offset for tp, offset in self._pending_offsets.items()}
            )
            self._pending_offsets.clear()
            logger.debug("Committed offsets")
        except KafkaError as e:
            logger.error(f"Failed to commit offsets: {e}")

    @property
    def topic(self) -> str:
        """Get the topic name."""
        return self._topic

    @property
    def group_id(self) -> str:
        """Get the consumer group ID."""
        return self._group_id


class RequestProducer:
    """Kafka producer for sending requests to services.

    Used by the API to enqueue requests for workers.
    """

    def __init__(self, bootstrap_servers: str | None = None):
        from aiokafka import AIOKafkaProducer

        self._settings = get_settings()
        self._bootstrap_servers = (
            bootstrap_servers or self._settings.kafka_bootstrap_servers
        )
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        from aiokafka import AIOKafkaProducer

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info("Started Kafka producer")

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Stopped Kafka producer")

    async def send_request(
        self,
        service_name: str,
        request_id: UUID,
        payload: dict[str, Any],
        sticky_key: str | None = None,
    ) -> None:
        """Send a request to a service's topic.

        Args:
            service_name: Name of the target service.
            request_id: Unique request ID.
            payload: Request payload.
            sticky_key: Optional key for sticky routing.
        """
        if self._producer is None:
            raise RuntimeError("Producer not started")

        topic = f"memrun.requests.{service_name}"
        message = {
            "request_id": str(request_id),
            "service_name": service_name,
            "payload": payload,
        }

        await self._producer.send_and_wait(
            topic,
            value=message,
            key=sticky_key,
        )
        logger.debug(f"Sent request {request_id} to {topic}")
