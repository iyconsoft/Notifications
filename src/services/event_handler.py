import json, asyncio
from aio_pika import Message
from src.core.config import (settings, logging)


class EventHandler_Service:

    async def __init__(self, app, connection):
        try:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            queue = await channel.declare_queue(settings.queue_name, durable=True)

            # Store in app.state for access later
            app.state.rabbit_connection = connection
            app.state.rabbit_channel = channel
            app.state.rabbit_queue = queue

            self.queue_name = settings.queue_name
            self.retry_queue = "webhook_retry_queue"
            self.channel = channel

            app.state.worker_task = await asyncio.create_task(
                self.consume(queue)
            )
        except Exception as e:
            logging.error(str(e))

    async def send_message(self, body: dict):
        message = Message(body=json.dumps(body).encode())
        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue_name
        )

    async def process_message(self, message):
        try:
            async with message.process():
                body = json.loads(message.body.decode())
                logging.info(f"Processing message: {body}")

                # write a process dispatcher here based on message content

        except Exception as e:
            logging.error(f"Message processing failed: {e}")
            await self.requeue_message(message)

    async def requeue_message(self, message):
        retry_count = message.headers.get('x-retry-count', 0) + 1
        if retry_count < 3:
            await self.channel.default_exchange.publish(
                Message(
                    body=message.body,
                    headers={'x-retry-count': retry_count}
                ),
                routing_key=self.retry_queue
            )

    async def consume(self, queue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self.process_message(message)


