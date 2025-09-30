from aio_pika import connect_robust, Message, ExchangeType, IncomingMessage
from aio_pika.abc import (
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractRobustExchange,
    AbstractRobustQueue,
)
from typing import Optional, Callable, Awaitable
import asyncio, os,logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = os.getenv("QUEUE_NAME")
# RABBITMQ_URL = settings.rabbitmq_url


class RabbitMQ:
    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchange: Optional[AbstractRobustExchange] = None
        self.queue: Optional[AbstractRobustQueue] = None
        self.consumer_task: Optional[asyncio.Task] = None

    async def connect(self, url: str = "amqp://guest:guest@localhost/"):
        self.connection = await connect_robust(url)
        self.channel = await self.connection.channel()
        # Set prefetch count for fair dispatch
        await self.channel.set_qos(prefetch_count=10)
        return self

    async def setup_exchange(
        self, name: str, type: ExchangeType = ExchangeType.DIRECT
    ):
        self.exchange = await self.channel.declare_exchange(name, type, durable=True)
        return self

    async def setup_queue(self, name: str, durable: bool = True):
        self.queue = await self.channel.declare_queue(name, durable=durable)
        return self

    async def bind_queue(self, routing_key: str = ""):
        if not self.exchange or not self.queue:
            raise ValueError("Exchange and queue must be setup first")
        await self.queue.bind(self.exchange, routing_key)
        return self

    async def publish(self, message: str, routing_key: str = ""):
        if not self.exchange:
            raise ValueError("Exchange must be setup first")

        message_obj = Message(
            body=message.encode(),
            delivery_mode=2,  # persistent
        )
        await self.exchange.publish(message_obj, routing_key=routing_key)

    async def consume(
        self,
        callback: Callable[[str], Awaitable[None]],
        queue_name: Optional[str] = None,
        no_ack: bool = False,
    ):
        """Start consuming messages from the queue."""
        if not self.queue and not queue_name:
            raise ValueError("Queue must be setup or queue_name must be provided")

        queue = self.queue if not queue_name else await self.channel.declare_queue(queue_name)

        async def process_message(message: IncomingMessage):
            try:
                body = message.body.decode()
                await callback(body)
                if not no_ack:
                    await message.ack()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if not no_ack:
                    await message.nack(requeue=False)  # Don't requeue failed messages

        self.consumer_task = asyncio.create_task(
            self._start_consumer(queue, process_message)
        )
        return self.consumer_task

    async def _start_consumer(self, queue, process_message):
        """Internal method to start consuming messages."""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_message(message)

    async def close(self):
        """Close connection and cancel consumer tasks."""
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass

        if self.connection:
            await self.connection.close()

    async def handle_message(message: str):
        """Process incoming RabbitMQ messages."""
        logger.info(f"Received message: {message}")


async def start_worker(handle_message, rabbitmq: RabbitMQ, url: str = RABBITMQ_URL, queue_name: str = QUEUE_NAME) -> None:
    await rabbitmq.connect(url)
    await rabbitmq.setup_exchange("events", ExchangeType.DIRECT)
    await rabbitmq.setup_queue(queue_name)
    await rabbitmq.bind_queue(f"{queue_name}_key")
    
    # Start consumer
    await rabbitmq.consume(handle_message)


async def close_worker(rabbitmq: RabbitMQ) -> None:
    await rabbitmq.close()


async def handle_message(message: str):
    """Process incoming RabbitMQ messages."""
    logger.info(f"Received message: {message}")
    # Add your business logic here
    # Example: parse JSON, update database, etc.



@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def robust_publish(rabbitmq: RabbitMQ, message: str, routing_key: str):
    try:
        await rabbitmq.publish(message, routing_key)
    except Exception as e:
        logger.error(f"Failed to publish message: {str(e)}")
        raise