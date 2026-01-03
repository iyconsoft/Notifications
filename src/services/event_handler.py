import json
import asyncio
from typing import Callable, Optional, Any, Dict, List
from aio_pika import Message, connect_robust, IncomingMessage, Channel
from src.core.config import (settings, logging)

class EventHandler_Service:
    def __init__(self):
        self.queue_name: str = settings.queue_name
        self.retry_queue: str = "webhook_retry_queue"
        self.connection = None
        self.channels: Dict[str, Channel] = {}  # Multiple channels by name
        self.consumer_tasks: Dict[str, asyncio.Task] = {}  # Track consumer tasks
        self.message_callbacks: Dict[str, Callable[[dict], Any]] = {}  # Callbacks by queue
        self.is_consuming = False

    def set_message_callback(self, callback: Callable[[dict], Any], queue_name: str = None):
        """Set callback for specific queue (defaults to main queue)"""
        queue = queue_name or self.queue_name
        self.message_callbacks[queue] = callback
        logging.info(f"✅ Callback registered for queue: {queue}")

    async def connect_rabbitmq(self, app):
        try:
            self.connection = await connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port, 
                login=settings.rabbitmq_username,
                password=settings.rabbitmq_password,
                virtualhost="",
                timeout=30
            )
            app.state.rabbit_connection = self.connection
            await self.setup(app)
            
        except ConnectionRefusedError:
            logging.error("❌ RabbitMQ connection refused - check if server is running")
            self.connection = None
        except Exception as e:
            logging.error(f"❌ Connection error: {e}")
            self.connection = None

    async def setup(self, app):
        """Setup main queues and start consuming"""
        try:
            if not self.connection:
                logging.error("No RabbitMQ connection available")
                return

            # Setup main queue
            await self.setup_queue(
                queue_name=self.queue_name,
                app=app
            )
            
            # Setup retry queue
            await self.setup_queue(
                queue_name=self.retry_queue,
                app=app
            )

            logging.info("✅ RabbitMQ Multi-Channel Worker started successfully")
            
        except Exception as e:
            logging.error(f"Setup failed: {e}")

    async def setup_queue(self, queue_name: str, app, prefetch_count: int = 10):
        """Setup individual queue with its own channel"""
        try:
            # Create dedicated channel for this queue
            channel = await self.connection.channel()
            await channel.set_qos(prefetch_count=prefetch_count)
            
            # Declare queue
            queue = await channel.declare_queue(
                queue_name, 
                durable=True
            )
            
            # Store channel
            self.channels[queue_name] = channel
            
            # Start consumer task
            self.consumer_tasks[queue_name] = asyncio.create_task(
                self.consume(queue_name, queue)
            )
            
        except Exception as e:
            logging.error(f"❌ Failed to setup queue '{queue_name}': {e}")

    async def add_queue(self, queue_name: str, app, prefetch_count: int = 10):
        """Dynamically add a new queue"""
        if queue_name in self.channels:
            logging.warning(f"Queue '{queue_name}' already exists")
            return
            
        await self.setup_queue(queue_name, app, prefetch_count)

    async def send_message(self, body: dict, queue_name: str = None, routing_key: str = None):
        """Send message to specific queue"""
        target_queue = queue_name or self.queue_name
        target_routing = routing_key or target_queue
        
        if target_queue not in self.channels:
            logging.error(f"No channel available for queue: {target_queue}")
            return
            
        try:
            message = Message(
                body=json.dumps(body).encode(),
                delivery_mode=2  # Persistent message
            )
            
            channel = self.channels[target_queue]
            await channel.default_exchange.publish(
                message,
                routing_key=target_routing
            )
            logging.info(f"📨 Message sent to {target_queue}")
            
        except Exception as e:
            logging.error(f"Failed to send message to {target_queue}: {e}")

    async def process_message(self, message: IncomingMessage, queue_name: str):
        """Process incoming message with queue-specific callback"""
        try:
            async with message.process():
                body = json.loads(message.body.decode())
                # Get queue-specific callback
                callback = self.message_callbacks.get(queue_name)
                
                if callback:
                    try:
                        result = await callback(body)
                        logging.info(f"✅ Message processed successfully from {queue_name}: {result}")
                    except Exception as callback_error:
                        logging.error(f"❌ Callback processing failed for {queue_name}: {callback_error}")
                        await self.requeue_message(message, queue_name)
                else:
                    logging.warning(f"⚠️ No callback registered for queue: {queue_name}")
                    await self.default_message_processing(body, queue_name)

        except json.JSONDecodeError as e:
            logging.error(f"❌ Invalid JSON in message from {queue_name}: {e}")
            await message.reject(requeue=False) 
        except Exception as e:
            logging.error(f"❌ Message processing failed for {queue_name}: {e}")
            await self.requeue_message(message, queue_name)

    async def default_message_processing(self, body: dict, queue_name: str):
        """Default processing when no callback is set for a queue"""
        logging.info(f"Default processing for {queue_name}: {body}")

    async def requeue_message(self, message: IncomingMessage, queue_name: str):
        """Handle message retry logic with queue-specific handling"""
        try:
            retry_count = message.headers.get('x-retry-count', 0) + 1
            
            if retry_count < 3:  # Max 3 retries
                logging.info(f"🔄 Requeuing message from {queue_name} (attempt {retry_count})")
                
                retry_message = Message(
                    body=message.body,
                    headers={'x-retry-count': retry_count},
                    delivery_mode=2
                )
                
                # Use the same channel for retry
                channel = self.channels.get(queue_name)
                if channel:
                    await channel.default_exchange.publish(
                        retry_message,
                        routing_key=self.retry_queue
                    )
                else:
                    await message.reject(requeue=False)
            else:
                logging.error(f"❌ Max retries exceeded for {queue_name}, moving to DLQ")
                await message.reject(requeue=False)
                
        except Exception as e:
            logging.error(f"❌ Failed to requeue message from {queue_name}: {e}")
            await message.reject(requeue=False)

    async def consume(self, queue_name: str, queue):
        """Start consuming messages from specific queue"""
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    # if not self.is_consuming:
                    #     break
                    await self.process_message(message, queue_name)
                    
        except Exception as e:
            logging.error(f"❌ Consumer error for {queue_name}")
            self.is_consuming = False

    async def stop_consuming(self, queue_name: str = None):
        """Stop consuming from specific queue or all queues"""
        if queue_name:
            if queue_name in self.consumer_tasks:
                self.consumer_tasks[queue_name].cancel()
                logging.info(f"🛑 Stopped consumer for queue: {queue_name}")
        else:
            self.is_consuming = False
            for name, task in self.consumer_tasks.items():
                task.cancel()
                logging.info(f"🛑 Stopped consumer for queue: {name}")
            
            if self.connection:
                await self.connection.close()

    def get_active_queues(self) -> List[str]:
        """Get list of active queues"""
        return list(self.channels.keys())

    async def get_queue_message_count(self, queue_name: str) -> int:
        """Get message count for a specific queue"""
        if queue_name in self.channels:
            try:
                queue = await self.channels[queue_name].declare_queue(
                    queue_name, 
                    passive=True  # Just check, don't create
                )
                return queue.declaration_result.message_count
            except Exception as e:
                logging.error(f"Failed to get message count for {queue_name}: {e}")
        return 0


class RouterEventHandler(EventHandler_Service):
    def __init__(self):
        super().__init__()
        self.handlers: Dict[str, Dict[str, Callable]] = {}  # {queue_name: {message_type: callback}}
    
    def register_handler(self, message_type: str, callback: Callable, queue_name: str = None):
        """Register handler for specific message type and queue"""
        queue = queue_name or self.queue_name
        
        if queue not in self.handlers:
            self.handlers[queue] = {}
        
        self.handlers[queue][message_type] = callback
    
    async def process_message(self, message: IncomingMessage, queue_name: str):
        """Process message with router pattern"""
        async with message.process():
            body = json.loads(message.body.decode())
            message_type = body.get('type')
            
            # Get handlers for this queue
            queue_handlers = self.handlers.get(queue_name, {})
            handler = queue_handlers.get(message_type)
            
            if handler:
                try:
                    await handler(body)
                    # await message.ack()
                except Exception as e:
                    logging.error(f"❌ Handler failed for '{message_type}' in {queue_name}: {e}")
                    await self.requeue_message(message, queue_name)
            else:
                logging.warning(f"⚠️ No handler for message type '{message_type}' in queue '{queue_name}'")
                await self.default_message_processing(body, queue_name)


eventrouter_handler: RouterEventHandler = RouterEventHandler()

