#!/usr/bin/env python3
"""
RabbitMQ Consumer for AI Audio Match
Consumes messages and starts Temporal workflows
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage

import logging

from .config import get_config_instance, get_rabbitmq_url

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SkipMessageException(Exception):
    """Exception to indicate a message should be skipped without error"""
    pass


class RejectMessageException(Exception):
    def __init__(self, message: str, requeue: bool = False):
        super().__init__(message)
        self.requeue = requeue
        """Exception to indicate a message should be rejected without requeue"""
        pass


class RabbitMQConsumerBase:
    """RabbitMQ Consumer with Temporal workflow integration"""

    def __init__(self):
        # Use Config class instance instead of plain dict
        self.config = get_config_instance()

        # Connection objects
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None

        # Control flags
        self.is_running = False
        self.should_stop = False

        # Statistics
        self.stats = {
            "messages_consumed": 0,
            "workflows_started": 0,
            "errors": 0,
            "start_time": None,
        }

    async def setup_queues_and_exchanges(self) -> bool:
        """Setup RabbitMQ queues and exchanges with detailed logging"""
        try:
            logger.info("🔧 Setting up RabbitMQ queues and exchanges...")

            # Declare exchange
            logger.info(f"📡 Declaring/creating exchange: {self.config.rabbitmq.exchange_name}")
            exchange = await self.channel.declare_exchange(
                self.config.rabbitmq.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            logger.info(f"✅ Exchange ready: {self.config.rabbitmq.exchange_name}")

            # Declare main queue
            logger.info(f"📥 Declaring/creating main queue: {self.config.rabbitmq.queue_name}")
            self.queue = await self.channel.declare_queue(
                self.config.rabbitmq.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": self.config.consumer.dead_letter_queue
                }
            )
            logger.info(f"✅ Main queue ready: {self.config.rabbitmq.queue_name}")

            # Declare dead letter queue
            logger.info(f"💀 Declaring/creating dead letter queue: {self.config.consumer.dead_letter_queue}")
            dlq = await self.channel.declare_queue(
                self.config.consumer.dead_letter_queue,
                durable=True
            )
            logger.info(f"✅ Dead letter queue ready: {self.config.consumer.dead_letter_queue}")

            # Bind queue to exchange
            logger.info(f"🔗 Binding queue to exchange with routing key: {self.config.rabbitmq.routing_key}")
            await self.queue.bind(
                exchange,
                self.config.rabbitmq.routing_key
            )

            # Also bind with additional routing keys for flexibility
            additional_keys = ["audio.*", "ai-audio.*"]
            for key in additional_keys:
                try:
                    await self.queue.bind(exchange, key)
                    logger.info(f"🔗 Additional binding: {key}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not bind additional key {key}: {e}")

            logger.info("✅ Queue binding completed")

            # Log queue setup completion
            logger.info(f"📊 Queue setup completed - Queue: {self.config.rabbitmq.queue_name}")

            return True

        except Exception as e:
            logger.error("❌ Failed to setup queues and exchanges", extra={"error": str(e)})
            return False

    async def connect(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            rabbitmq_url = get_rabbitmq_url()
            logger.info(
                f"🔗 Connecting to RabbitMQ at: {rabbitmq_url.replace(self.config.rabbitmq.password, '***')}"
            )

            self.connection = await aio_pika.connect_robust(
                rabbitmq_url,
                heartbeat=self.config.rabbitmq.heartbeat,
                connection_timeout=self.config.rabbitmq.connection_timeout,
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(
                prefetch_count=self.config.rabbitmq.prefetch_count
            )

            logger.info("✅ RabbitMQ connection established")

            # Setup queues and exchanges
            if not await self.setup_queues_and_exchanges():
                return False

            logger.info("✅ Connected to RabbitMQ successfully")
            return True

        except Exception as e:
            logger.exception(f"❌ Failed to connect to RabbitMQ: {str(e)}")
            logger.error(
                f"Connection URL (masked): {get_rabbitmq_url().replace(self.config.rabbitmq.password, '***')}"
            )
            rmq_cfg = self.config.to_dict()["rabbitmq"].copy()
            rmq_cfg["password"] = "***"
            logger.error(f"RabbitMQ config: {rmq_cfg}")
            return False

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("✅ Disconnected from RabbitMQ")
        except Exception as e:
            logger.warning("⚠️ Error during RabbitMQ disconnect", extra={"error": str(e)})

    async def on_message(self, message_id: str, message_data: Any) -> bool: pass
    """Handle message and start appropriate workflow"""

    async def process_message(self, message: IncomingMessage) -> bool:
        """Process a single message from RabbitMQ"""
        try:
            # Parse message
            message_data = json.loads(message.body.decode())
            logger.debug("Processing message", extra={"message_id": message.message_id})
            if "type" not in message_data or "data" not in message_data:
                raise ValueError("Message missing 'type' or 'data' fields")
            await self.on_message(message.message_id, message_data)
            # Acknowledge message
            await message.ack()

            # Update statistics
            self.stats["messages_consumed"] += 1
            self.stats["workflows_started"] += 1

            return True
        except RejectMessageException as e:
            logger.info(f"Rejecting message: {str(e)}", extra={"message_id": message.message_id})
            await message.reject(requeue=e.requeue)
            self.stats["errors"] += 1
            return False
        except SkipMessageException as e:
            logger.info(f"Skipping message: {str(e)}", extra={"message_id": message.message_id})
            await message.ack()
            return True
        except json.JSONDecodeError as e:
            logger.exception("Invalid JSON in message", extra={"error": str(e)})
            await message.reject(requeue=False)
            self.stats["errors"] += 1
            return False

        except Exception as e:
            logger.exception("Failed to process message", extra={"error": str(e)})
            # Reject with requeue for temporary failures
            await message.reject(requeue=True)
            self.stats["errors"] += 1
            return False

    async def wait_for_capacity(self, interval: int = 10): pass
    """Wait until we have capacity to start a new workflow"""

    async def monitor_and_fetch(self, check_interval=10):
        """Monitor workflow capacity and fetch messages accordingly"""
        logger.info("🔍 Starting workflow monitor and message fetcher...")
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if self.should_stop:
                        break
                    logger.debug("Fetched message from queue", extra={"message_id": message.message_id})
                    await self.wait_for_capacity(interval=check_interval)
                    logger.debug("Capacity available, processing message", extra={"message_id": message.message_id})
                    await self.process_message(message)
        except Exception as e:
            logger.exception(f"Error in monitor loop: {str(e)}", extra={"error": str(e), "error_type": type(e).__name__})
            await asyncio.sleep(10)

    async def start_consuming(self, monitor_check_interval=10):
        """Start consuming messages from RabbitMQ"""
        self.should_stop = False
        while self.should_stop is False:
            try:
                if not await self.connect():
                    raise RuntimeError("Failed to connect to RabbitMQ")

                self.is_running = True
                self.stats["start_time"] = datetime.utcnow().isoformat()

                logger.info("🚀 Starting RabbitMQ consumer...")
                # Log configuration safely (mask sensitive data)
                safe_cfg = self.config.to_dict()
                safe_cfg["rabbitmq"]["password"] = "***"
                logger.info("Consumer configuration", extra={"config": safe_cfg})

                try:
                    await self.monitor_and_fetch(check_interval=monitor_check_interval)
                finally:
                    await self.disconnect()
                    self.is_running = False
                    logger.info("🛑 RabbitMQ consumer stopped")
            except Exception as e:
                logger.exception("❌ Error in consumer loop", extra={"error": str(e), "error_type": type(e).__name__})
                self.stats["errors"] += 1
                await asyncio.sleep(5)

    async def stop_consuming(self):
        """Stop consuming messages"""
        logger.info("🛑 Stopping RabbitMQ consumer...")
        self.should_stop = True
        self.disconnect()  # Close connection to unblock any waiting operations
        # Wait for graceful shutdown
        while self.is_running:
            await asyncio.sleep(0.1)

    def get_statistics(self) -> Dict[str, Any]:
        """Get consumer statistics"""
        uptime = None
        if self.stats["start_time"]:
            start_time = datetime.fromisoformat(self.stats["start_time"])
            uptime = (datetime.utcnow() - start_time).total_seconds()
        config_clone = self.config.to_dict()
        if "password" in config_clone.get("rabbitmq", {}):
            config_clone["rabbitmq"]["password"] = "***"
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "is_running": self.is_running,
            "config": config_clone
        }
