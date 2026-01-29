#!/usr/bin/env python3
"""
RabbitMQ Publisher
Sends messages to RabbitMQ for processing by the consumer
"""

import asyncio
from itertools import zip_longest
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import aio_pika

from .config import get_config_instance, get_rabbitmq_url

import logging

# Get logger
logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """Publisher for sending messages to RabbitMQ"""

    def __init__(self):
        # Use Config class instance
        self.config = get_config_instance()
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                return True

            logger.info("Connecting to RabbitMQ...")
            self.connection = await aio_pika.connect_robust(
                get_rabbitmq_url(),
                heartbeat=self.config.rabbitmq.heartbeat,
                connection_timeout=self.config.rabbitmq.connection_timeout
            )
            self.channel = await self.connection.channel()

            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                self.config.rabbitmq.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            logger.info("✅ Connected to RabbitMQ for publishing")
            return True

        except Exception as e:
            logger.error("❌ Failed to connect to RabbitMQ", extra={"error": str(e)})
            return False

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error("Error disconnecting from RabbitMQ", extra={"error": str(e)})

    async def publish_message(self, message_type: str, message_data: Dict[str, Any], source='api', message_id: str = None, priority: int = 1) -> bool:
        """
        Publish a message to RabbitMQ

        Args:
            message_type: Type of message ('query' or 'index')
            message_data: The actual message data
            priority: Message priority (1-10, higher is more important)

        Returns:
            bool: True if message was published successfully
        """
        if not await self.connect():
            return False
        message_id = message_id or str(uuid.uuid4())
        try:
            # Prepare message body
            message_body = {
                "id": message_id,
                "type": message_type,
                "data": message_data,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": source,
                "priority": priority
            }

            # Create message
            message = aio_pika.Message(
                json.dumps(message_body).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Make messages persistent
                priority=priority,
                message_id=message_body["id"],
                timestamp=datetime.utcnow()
            )

            # Publish message
            await self.exchange.publish(
                message,
                routing_key=self.config.rabbitmq.routing_key
            )

            logger.info(
                f"✅ Published {message_type} message to RabbitMQ",
                extra={
                    "message_id": message_body["id"],
                    "message_type": message_type,
                    "priority": priority,
                    "custom_id": message_data.get("custom_id")
                }
            )
            return message_id

        except Exception as e:
            logger.error(
                f"❌ Failed to publish {message_type} message",
                extra={"error": str(e), "message_data": message_data}
            )
            return None

    async def publish_query(self, message_data: Dict, message_id=None, priority: int = 1, source='api') -> bool:
        """
        Publish a query message

        Args:
            uri: Audio file URL or path
            custom_id: Optional custom identifier
            top_k: Number of results to return
            threshold: Similarity threshold
            continuous_delta: Time delta for continuous search
            priority: Message priority

        Returns:
            bool: True if message was published successfully
        """
        return await self.publish_message("query", message_data, message_id=message_id, priority=priority, source=source)

    async def publish_index(self, message_data: Dict, message_id, priority: int = 1, source='api') -> bool:
        """
        Publish an index message

        Args:
            uri: Audio file URL or path
            custom_id: Optional custom identifier
            file_name: Optional file name
            priority: Message priority

        Returns:
            bool: True if message was published successfully
        """

        return await self.publish_message("index", message_data, message_id=message_id, priority=priority, source=source)

    async def publish_batch(self, messages: list, message_ids: list = [], source='api') -> Dict[str, Any]:
        """
        Publish multiple messages in batch

        Args:
            messages: List of message dictionaries

        Returns:
            dict: Statistics about the batch operation
        """
        if not await self.connect():
            return {"success": False, "error": "Failed to connect to RabbitMQ"}

        stats = {
            "total_messages": len(messages),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        for i, (msg, message_id) in enumerate(zip_longest(messages, message_ids, fillvalue=None)):
            try:
                message_type = msg.get("type", "query")
                message_data = msg.get("data", {})
                priority = msg.get("priority", 1)

                success = await self.publish_message(message_type, message_data, priority=priority, message_id=message_id, source=source)
                if success:
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1
                    stats["errors"].append(f"Message {i}: Failed to publish")

            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"Message {i}: {str(e)}")

        logger.info(
            f"Batch publish completed: {stats['successful']}/{stats['total_messages']} successful",
            extra=stats
        )

        return stats

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about the RabbitMQ queue"""
        if not await self.connect():
            return {"success": False, "error": "Failed to connect to RabbitMQ"}

        try:
            queue = await self.channel.declare_queue(
                self.config.rabbitmq.queue_name,
                passive=True  # Only check if it exists
            )
            stats = {
                "queue_name": queue.name,
                "message_count": queue.declaration_result.message_count,
                "consumer_count": queue.declaration_result.consumer_count,
            }
            logger.info("Fetched RabbitMQ queue stats", extra=stats)
            return {"success": True, "stats": stats}

        except aio_pika.exceptions.ChannelClosed as e:
            logger.error("Queue does not exist", extra={"error": str(e)})
            return {"success": False, "error": "Queue does not exist"}

        except Exception as e:
            logger.error("Failed to get queue stats", extra={"error": str(e)})
            return {"success": False, "error": str(e)}


# Global publisher instance
_publisher_instance = None


async def get_publisher() -> RabbitMQPublisher:
    """Get or create a global publisher instance"""
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = RabbitMQPublisher()
    return _publisher_instance


async def cleanup_publisher():
    """Cleanup the global publisher instance"""
    global _publisher_instance
    if _publisher_instance:
        await _publisher_instance.disconnect()
        _publisher_instance = None


if __name__ == "__main__":
    async def main():
        publisher = await get_publisher()
        stats = publisher.get_queue_stats()
        print(stats)
    asyncio.run(main())
