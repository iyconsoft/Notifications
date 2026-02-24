import json, asyncio
from datetime import datetime
from typing import Callable, Optional, Any, Dict, List
from aio_pika import Message, connect_robust, IncomingMessage, Channel
from src.core.config import settings, logging

class EventHandler_Service:
    def __init__(self):
        self.queue_name: str = settings.queue_name
        self.connection = None
        self.channels: Dict[str, Channel] = {}
        self.consumer_tasks: Dict[str, asyncio.Task] = {}
        self.message_callbacks: Dict[str, Callable[[dict], Any]] = {}
        self.handlers: Dict[str, Dict[str, Callable]] = {}  # {queue_name: {message_type: callback}}
        self.is_consuming = True  # Default to True

    def set_message_callback(self, callback: Callable[[dict], Any], queue_name: str = None):
        """Set callback for specific queue"""
        queue = queue_name or self.queue_name
        self.message_callbacks[queue] = callback
        logging.info(f"✅ Callback registered for queue: {queue}")

    async def register_handler(self, message_type: str, callback: Callable, queue_name: str = None):
        """Register handler for specific message type and queue"""
        queue = queue_name or self.queue_name
        
        if queue not in self.handlers:
            self.handlers[queue] = {}
        
        self.handlers[queue][message_type] = callback
        # logging.info(f"✅ Handler registered for '{message_type}' in queue '{queue}'")

    async def connect_rabbitmq(self, app):
        """Connect to RabbitMQ"""
        try:
            self.connection = await connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_username,
                password=settings.rabbitmq_password,
                virtualhost="/",
                timeout=30
            )
            app.state.rabbit_connection = self.connection
            logging.info("✅ Connected to RabbitMQ")
            
        except Exception as e:
            logging.error(f"❌ RabbitMQ connection failed: {e}")
            self.connection = None
            raise

    async def setup_consumers(self, app):
        """Setup and start consumers - Call this AFTER registering handlers"""
        if not self.connection:
            logging.error("No RabbitMQ connection available")
            return

        # Setup main queue consumer
        await self.setup_queue_consumer(
            queue_name=self.queue_name,
            app=app
        )
        # logging.info(f"✅ Started consumer for queue: {self.queue_name}")

    async def setup_queue_consumer(self, queue_name: str, app, prefetch_count: int = 10):
        """Setup consumer for a specific queue"""
        try:
            # Create channel for this queue
            channel = await self.connection.channel()
            await channel.set_qos(prefetch_count=prefetch_count)
            
            # Declare queue (MUST match what publisher uses)
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    'x-queue-type': 'classic',
                    # 'x-max-length': 100000  # Prevent memory overflow
                }
            )
            
            # Store channel
            self.channels[queue_name] = channel
            
            # Create and store consumer task
            self.consumer_tasks[queue_name] = asyncio.create_task(
                self.consume_queue(queue_name, queue),
                name=f"consumer-{queue_name}"
            )
            
            # logging.info(f"✅ Consumer task created for queue: {queue_name}")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup consumer for '{queue_name}': {e}")
            raise

    async def consume_queue(self, queue_name: str, queue):
        """Consume messages from a specific queue"""
        logging.info(f"🎯 Starting to consume from queue: {queue_name}")
        
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if not self.is_consuming:
                        break
                    
                    await self.process_incoming_message(message, queue_name)
                    
        except asyncio.CancelledError:
            logging.info(f"🛑 Consumer cancelled for queue: {queue_name}")
        except Exception as e:
            logging.error(f"❌ Consumer error for {queue_name}: {e}")

    async def process_incoming_message(self, message: IncomingMessage, queue_name: str):
        """Process incoming message"""
        try:
            # Parse message
            body = json.loads(message.body.decode())
            
            # Check for handler by message type
            message_type = body.get('type')
            queue_handlers = self.handlers.get(queue_name, {})
            
            if message_type in queue_handlers:
                handler = queue_handlers[message_type]
                
                async with message.process():
                    try:
                        # Execute handler
                        result = await handler(body)
                        logging.info(f"✅ Successfully processed '{message_type}': {result}")
                    except Exception as e:
                        logging.error(f"❌ Handler failed for '{message_type}': {e}")
                        # Reject with requeue
                        await message.reject(requeue=True)
            else:
                # No handler found
                logging.warning(f"⚠️ No handler for message type '{message_type}' in queue '{queue_name}'")
                await message.reject(requeue=False)  # Discard or send to DLQ
                
        except json.JSONDecodeError:
            logging.error(f"❌ Invalid JSON in message from {queue_name}")
            await message.reject(requeue=False)
        except Exception as e:
            logging.error(f"❌ Failed to process message from {queue_name}: {e}")
            await message.reject(requeue=True)

    async def send_message(self, body: dict, queue_name: str = None, routing_key: str = None):
        """Send message to queue"""
        target_queue = queue_name or self.queue_name
        target_routing = routing_key or target_queue
        
        try:
            # Ensure we have a channel for this queue
            if target_queue not in self.channels:
                channel = await self.connection.channel()
                await channel.declare_queue(target_queue, durable=True)
                self.channels[target_queue] = channel
            
            channel = self.channels[target_queue]
            
            # Create message
            message = Message(
                body=json.dumps(body).encode(),
                delivery_mode=2,  # Persistent
                content_type='application/json',
                headers={
                    'sent_at': datetime.utcnow().isoformat(),
                    'source': 'adapterapi'
                }
            )
            
            # Publish
            await channel.default_exchange.publish(
                message,
                routing_key=target_routing
            )
            
            logging.info(f"📨 Sent message to {target_queue}: {body.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to send message to {target_queue}: {e}")
            return False

    async def stop_all(self):
        """Stop all consumers and close connection"""
        self.is_consuming = False
        
        # Cancel all consumer tasks
        for queue_name, task in self.consumer_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logging.info(f"🛑 Stopped consumer for: {queue_name}")
        
        # Close channels
        for channel in self.channels.values():
            await channel.close()
        
        # Close connection
        if self.connection:
            await self.connection.close()
        
        logging.info("✅ Event handler stopped successfully")


