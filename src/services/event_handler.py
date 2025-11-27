import json, asyncio
from typing import Callable, Optional, Any
from aio_pika import Message, connect_robust, IncomingMessage
from src.core.config import (settings, logging)

class EventHandler_Service:
    def __init__(self):
        self.queue_name: str = settings.queue_name
        self.retry_queue: str = "webhook_retry_queue"
        self.channel = None
        self.connection = None
        self.message_callback: Optional[Callable[[dict], Any]] = None
        self.is_consuming = False

    def set_message_callback(self, callback: Callable[[dict], Any]):
        """Set the callback function to process messages"""
        self.message_callback = callback

    async def connect_rabbitmq(self, app):
        try:
            self.connection = await connect_robust(
                host="84.247.182.227",
                port=5672, 
                login="iyconsoft",
                password="Iyconsoft2025#",
                virtualhost="",
                timeout=30
            )
            app.state.rabbit_connection = self.connection
            await self.setup(app)  # Pass app to setup
            
        except ConnectionRefusedError:
            logging.error("❌ RabbitMQ connection refused - check if server is running")
            self.connection = None
        except aio_pika.AMQPConnectionError as e:
            logging.error(f"❌ AMQP connection error: {e}")
            self.connection = None
        except Exception as e:
            logging.error(f"❌ Unexpected connection error: {e}")
            self.connection = None

    async def setup(self, app):
        """Setup queues and start consuming"""
        try:
            if not self.connection:
                logging.error("No RabbitMQ connection available")
                return

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # Declare main queue
            queue = await self.channel.declare_queue(
                self.queue_name, 
                durable=True
            )
            
            # Declare retry queue
            retry_queue = await self.channel.declare_queue(
                self.retry_queue,
                durable=True
            )

            # Start consuming in background
            self.is_consuming = True
            app.state.worker_task = asyncio.create_task(
                self.consume(queue)
            )

            logging.info("✅ RabbitMQ Worker started successfully")
            
        except Exception as e:
            logging.error(f"Setup failed: {e}")

    async def send_message(self, body: dict):
        """Send message to queue"""
        if not self.channel:
            logging.error("No channel available to send message")
            return
            
        try:
            message = Message(
                body=json.dumps(body).encode(),
                delivery_mode=2  # Persistent message
            )
            await self.channel.default_exchange.publish(
                message,
                routing_key=self.queue_name
            )
            logging.info(f"📨 Message sent to {self.queue_name}")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    async def process_message(self, message: IncomingMessage):
        """Process incoming message with callback"""
        try:
            async with message.process():
                body = json.loads(message.body.decode())
                logging.info(f"Processing message: {body}")
                
                if self.message_callback:
                    try:
                        result = await self.message_callback(body)
                        logging.info(f"✅ Message processed successfully: {result}")
                    except Exception as callback_error:
                        logging.error(f"❌ Callback processing failed: {callback_error}")
                        await self.requeue_message(message)
                else:
                    logging.warning("⚠️ No callback registered for message processing")
                    await self.default_message_processing(body)

        except json.JSONDecodeError as e:
            logging.error(f"❌ Invalid JSON in message: {e}")
            await message.reject(requeue=False) 
        except Exception as e:
            logging.error(f"❌ Message processing failed: {e}")
            await self.requeue_message(message)

    async def default_message_processing(self, body: dict):
        """Default processing when no callback is set"""
        logging.info(f"Default processing for: {body}")
        # Add your default message processing logic here

    async def requeue_message(self, message: IncomingMessage):
        """Handle message retry logic"""
        try:
            retry_count = message.headers.get('x-retry-count', 0) + 1
            
            if retry_count < 3:  # Max 3 retries
                logging.info(f"🔄 Requeuing message (attempt {retry_count})")
                
                retry_message = Message(
                    body=message.body,
                    headers={'x-retry-count': retry_count},
                    delivery_mode=2
                )
                
                await self.channel.default_exchange.publish(
                    retry_message,
                    routing_key=self.retry_queue
                )
            else:
                logging.error("❌ Max retries exceeded, moving to DLQ")
                # You might want to send to a dead letter queue here
                await message.reject(requeue=False)
                
        except Exception as e:
            logging.error(f"❌ Failed to requeue message: {e}")
            await message.reject(requeue=False)

    async def consume(self, queue):
        """Start consuming messages from queue"""
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if not self.is_consuming:
                        break
                    await self.process_message(message)
        except Exception as e:
            logging.error(f"❌ Consumer error: {e}")
            self.is_consuming = False

    async def stop_consuming(self):
        """Stop the consumer gracefully"""
        self.is_consuming = False
        if self.connection:
            await self.connection.close()


class RouterEventHandler(EventHandler_Service):
    def __init__(self):
        super().__init__()
        self.handlers = {}
    
    def register_handler(self, message_type: str, callback: Callable):
        """Register different handlers for different message types"""
        self.handlers[message_type] = callback
    
    async def process_message(self, message: IncomingMessage):
        async with message.process():
            body = json.loads(message.body.decode())
            message_type = body.get('type')
            
            handler = self.handlers.get(message_type)
            if handler:
                await handler(body)
            else:
                logging.warning(f"No handler for message type: {message_type}")

event_handler: EventHandler_Service = EventHandler_Service()
eventrouter_handler: RouterEventHandler = RouterEventHandler()


#### getting event messages from event handler
# router_handler.register_handler('email', send_email_handler)
# router_handler.register_handler('sms', send_sms_handler)
# router_handler.register_handler('notification', send_notification_handler)


#### sending messages to event handler
# background_tasks.add_task(event_handler.send_message, payload)