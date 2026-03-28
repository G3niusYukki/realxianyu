"""Kafka client for message publishing and consumption."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from xianyuflow_common.config import KafkaConfig

if TYPE_CHECKING:
    from kafka import KafkaConsumer, KafkaProducer

logger = logging.getLogger(__name__)

# Topic definitions
TOPICS: dict[str, str] = {
    "chat_messages": "xianyuflow.chat.messages",
    "chat_events": "xianyuflow.chat.events",
    "user_events": "xianyuflow.user.events",
    "order_events": "xianyuflow.order.events",
    "item_events": "xianyuflow.item.events",
    "notification_events": "xianyuflow.notification.events",
    "ai_requests": "xianyuflow.ai.requests",
    "ai_responses": "xianyuflow.ai.responses",
}


class KafkaClient:
    """Kafka client for publishing and consuming messages."""

    def __init__(self, config: KafkaConfig) -> None:
        """Initialize Kafka client.

        Args:
            config: Kafka configuration.
        """
        self.config = config
        self._producer: KafkaProducer | None = None
        self._consumer: KafkaConsumer | None = None

    def connect(self) -> None:
        """Initialize Kafka producer."""
        from kafka import KafkaProducer

        self._producer = KafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            client_id=self.config.client_id,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        logger.info("Kafka producer connected to %s", self.config.bootstrap_servers)

    def disconnect(self) -> None:
        """Close Kafka connections."""
        if self._producer:
            self._producer.close()
            self._producer = None
        if self._consumer:
            self._consumer.close()
            self._consumer = None
        logger.info("Kafka connections closed")

    def publish(
        self,
        topic: str,
        message: dict[str, Any],
        key: str | None = None,
    ) -> None:
        """Publish message to topic.

        Args:
            topic: Topic name.
            message: Message payload.
            key: Optional message key.

        Raises:
            RuntimeError: If producer not connected.
        """
        if not self._producer:
            raise RuntimeError("Kafka producer not connected. Call connect() first.")

        future = self._producer.send(topic, value=message, key=key)
        future.add_callback(
            lambda metadata: logger.debug(
                "Message sent to %s:%s", metadata.topic, metadata.partition
            )
        )
        future.add_errback(lambda exc: logger.error("Failed to send message: %s", exc))

    def consume(
        self,
        topics: list[str],
        group_id: str,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        """Consume messages from topics.

        Args:
            topics: List of topic names to subscribe.
            group_id: Consumer group ID.
            handler: Message handler function.

        Raises:
            RuntimeError: If already consuming.
        """
        from kafka import KafkaConsumer

        if self._consumer:
            raise RuntimeError("Already consuming. Call disconnect() first.")

        self._consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.config.bootstrap_servers,
            group_id=group_id,
            client_id=self.config.client_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

        logger.info("Started consuming topics: %s", topics)

        try:
            for message in self._consumer:
                try:
                    handler(message.value)
                except Exception as e:
                    logger.error("Error handling message: %s", e)
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            self._consumer.close()
            self._consumer = None
