import asyncio
import json
from typing import Callable, Optional, Dict
from aio_pika import Message, DeliveryMode, connect_robust
from aio_pika.abc import AbstractConnection, AbstractIncomingMessage

class ConnectionOptions(object):
    host_name: str = 'localhost'
    username: str = 'guest'
    password: str = 'guest'
    enable_tls: bool = False

class AsyncRabbitMqClient:
    def __init__(self, options: ConnectionOptions = None):
        """
        Initialize an asynchronous RabbitMQ client
        :param options: connection options (if None, defaults are used)
        """
        self._options = options if options else ConnectionOptions()
        self._consumer_connection = None
        self._producer = None
        self._consumers = []

    async def _create_connection(self) -> AbstractConnection:
        """
        Create a robust RabbitMQ connection
        """
        url = f"amqp://{self._options.username}:{self._options.password}@{self._options.host_name}/"
        connection = await connect_robust(url)
        return connection

    async def publish(self, queue: str, payload: object, headers: Optional[Dict] = None) -> None:
        """
        Publish a message to a queue. Producer is created the first time this is called.

        NOTE: This creates ONE connection for the producer and reuses it for subsequent publishes.
        :param queue: name of the queue.
        :param payload: message payload.
        :param headers: message headers.
        :return: None
        """
        if self._producer is None:
            connection = await self._create_connection()
            self._producer = Producer(connection)
        await self._producer.publish(queue, payload, headers)

    async def add_handler(self, queue: str, handler: Callable) -> None:
        """
        Register a consumer handler for a queue.
        :param queue: name of the queue.
        """
        if self._consumer_connection is None:
            self._consumer_connection = await self._create_connection()
        consumer = Consumer(self._consumer_connection)
        self._consumers.append(consumer)
        await consumer.consume(queue, handler)

    @classmethod
    async def loop(cls):
        """
        Block forever to keep the event loop alive
        """
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass

class Producer:
    def __init__(self, connection: AbstractConnection):
        self._connection = connection
        self._channel = None

    async def publish(self, queue_name: str, payload: object, headers: Optional[Dict] = None) -> None:
        assert self._connection is not None
        if self._channel is None:
            self._channel = await self._connection.channel()

        q = await self._channel.declare_queue(queue_name, durable=True)
        body = json.dumps(payload).encode('utf-8')
        m = Message(body=body, headers=headers, delivery_mode=DeliveryMode.PERSISTENT)
        await self._channel.default_exchange.publish(m, routing_key=q.name)

    async def close(self):
        if self._channel is not None:
            await self._channel.close()
        if self._connection is not None:
            await self._connection.close()

class Consumer:
    def __init__(self, connection: AbstractConnection):
        self._connection = connection
        self._channel = None

    async def consume(self, queue_name: str, handler: Callable) -> None:
        assert self._connection is not None
        ch = await self._connection.channel()
        await ch.set_qos(prefetch_count=1)
        q = await ch.declare_queue(queue_name, durable=True)

        async def on_message(msg: AbstractIncomingMessage) -> None:
            try:
                payload = json.loads(msg.body.decode('utf-8'))
            except json.JSONDecodeError:
                payload = msg.body.decode('utf-8')
            try:
                await handler(payload, msg)
                await msg.ack()
            except Exception as e:
                print(e)
                await msg.nack(requeue=False)

        await q.consume(on_message, no_ack=False)
