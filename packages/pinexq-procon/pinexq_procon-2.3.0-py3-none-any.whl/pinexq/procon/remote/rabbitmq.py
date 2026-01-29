"""
Protocol wrapper for the communication via RabbitMQ.
"""

import asyncio
import logging
import ssl
from abc import ABCMeta
from collections.abc import Awaitable, Callable
from inspect import isawaitable

import aio_pika
import aio_pika.abc
import aio_pika.exceptions
import stamina
from aiormq import AMQPConnectionError, ChannelNotFoundEntity, ChannelPreconditionFailed

from ..core.exceptions import ProConBadMessage, ProConMessageRejected


log = logging.getLogger(__name__)

AMPQ_DEFAULT_PORT = 5672
AMPQS_DEFAULT_PORT = 5671  # TLS secured AMPQ


class AbstractQueueHandler(metaclass=ABCMeta):
    """Base class for all handlers reading/writing to a RMQ queue"""
    _parent: 'RabbitMQClient'

# @abstractmethod
    # async def close(self):
    #     ...

    @property
    def client_connected(self) -> asyncio.Event:
        return self._parent.connection.connected


class QueueSubscriber(AbstractQueueHandler):
    """Wrapper to handle a queue with subscription to a topic."""

    _is_consuming: asyncio.Event
    _is_started: asyncio.Event
    _is_stopped: asyncio.Event
    _consumer_task: asyncio.Task | None
    _msg_handler_tasks: set[asyncio.Task]
    _rmq_queue: aio_pika.abc.AbstractRobustQueue

    consumer_tag: str
    queue_name: str
    routing_key: str

    def __init__(
            self,
            queue_name: str,
            routing_key: str,
            msg_callback: Callable[[bytes], None] | Awaitable[bytes],
            _parent: 'RabbitMQClient',
    ):
        """
        Wrapper to handle a queue with subscription to a topic.

        Args:
            queue_name: Name of the queue to create.
            msg_callback: Callable accepting the incoming message as parameter.
            routing_key: Routing for the queue to bind to.
            _parent: The client (used internally).
        """
        self.queue_name = queue_name
        self.routing_key = routing_key
        self._callback = msg_callback
        self._parent = _parent
        self.consumer_tag = "not-set"
        self._consumer_task = None

        self._event_lock = asyncio.Lock()  # Locks access to the following events
        self._is_started = asyncio.Event()  # Indicates the queue is polling
        self._is_stopped = asyncio.Event()  # Indicates that the polling has stopped
        self._is_stopped.set()

    async def connect_to_queue(self):
        self._rmq_queue = await self._parent.channel.declare_queue(
            name=self.queue_name,
            durable=True,
            passive=True # do not create queue if it does not exist
        )

    async def _disconnect_from_queue(self):
        # log.debug('Unbinding queue "%s"', self.queue_name)
        # cancel consuming this since we can not shut down the whole connection
        try:
            # this is not working on reconnect, will reconnect anyway
            await self._rmq_queue.cancel(consumer_tag=self.consumer_tag, timeout=10)
            self.consumer_tag="canceled"
            # WORKAROUND: cancel will not remove the queue form reconnect callbacks in RobustChannel,
            # so a reconnect will still fail since it wants to connect to a non-existing (canceled) queue.
            # Other option is to reset the channel on reconnect and rebuild from own managed state.
            self._parent.channel._queues.pop(self.queue_name, None)
        except Exception as e:
            log.error(f"Failed to cancel consuming queue .{self.queue_name}: {e}")

    async def delete(self, force: bool = False):
        # log.debug('Deleting queue "%s"', self.queue_name)
        await self._rmq_queue.delete(
            if_unused=not force,
            if_empty=not force
        )

    async def _consumer_loop(self):
        """
        Poll the RMQ queue and consume messages.
        """
        # The Lock and Events prevent start-/stopping while in the progress of being start-/stopped.
        async with self._event_lock:
            self._is_stopped.clear()
            self._is_started.set()
        log.debug(f'Start consuming on <queue:%s>', self.queue_name)

        try:
            async with self._rmq_queue.iterator() as queue_iterator:
                # we need this tag to cancel the connection to the queue
                # it is hidden in iterator which would clean up when it is stopped, but this never happens
                self.consumer_tag = queue_iterator._consumer_tag
                async for message in queue_iterator:
                    await self._message_handler(message)

        finally:
            async with self._event_lock:
                self._is_started.clear()
                self._is_stopped.set()
            log.debug(f'Stop consuming on <queue:%s>', self.queue_name)

    async def run_consumer_loop(self):
        """Start the consumer task that polls for messages on the queue."""
        if self._is_started.is_set():
            log.warning('Consumer started, but is already running! <queue:%s>', self.queue_name)
            return
        await self._is_stopped.wait()
        await self.client_connected.wait()  # avoid consuming when disconnected

        self._consumer_task = asyncio.create_task(
            self._consumer_loop(),
            name="job-offer-consumer-loop"
        )
        await self._consumer_task  # <-- this will run until canceled

    async def stop_consumer_loop(self):
        """Stop the consumer task and listening for messages."""
        if self._is_stopped.is_set():
            # log.warning('Stop on non-running consumer! <queue:%s>', self.queue_name)
            return
        await self._is_started.wait()
        # Cancel the task and wait for it to end
        self._consumer_task.cancel()
        try:
            await self._consumer_task
            self._consumer_task = None
        except asyncio.CancelledError:
            pass
        finally:
            await self._disconnect_from_queue() # so on reconnect we do not look for this queue again

    async def _message_handler(self, message: aio_pika.abc.AbstractIncomingMessage):
        """Handle incoming messages in a callback and react to the message
            depending on (un)successful execution of the callback."""
        # difference between "nack" and "reject" -> https://www.rabbitmq.com/docs/nack#overview
        log.debug('→✉ Message received. <route:%s> <msg_id:%s>',
                  self.routing_key, message.message_id)
        try:
            res = self._callback(message.body)
            if isawaitable(res):  # allow for sync and async callbacks
                await res

        # Reject and drop message on deserialization/validation errors
        except ProConBadMessage as ex:
            await message.reject()
            cause = f" -> {str(ex.__cause__)}" if ex.__cause__ else str(ex)
            log.error('✖ Dropped invalid or broken message! %s <msg_id:%s>', cause, message.message_id)

        # The worker does currently accept no jobs
        except ProConMessageRejected as ex:
            await message.reject(requeue=True)
            cause = f" -> {str(ex.__cause__)}" if ex.__cause__ else str(ex)
            log.error('↩ Unable to process message! Message requeued. %s <msg_id:%s>', cause, message.message_id)

        # Reject and requeue after all other errors and propagate exception
        except Exception as ex:
            if self.client_connected.is_set():  # avoid sending error messages when disconnected
                await message.reject(requeue=True)
            log.error('↩ Exception during message handling! Message requeued. <msg_id:%s>', message.message_id)
            raise ex

        # Ack on successful handling of the message (this happens *before* processing the job)
        else:
            await message.ack()
            log.debug('✔ Message processed successfully! <msg_id:%s>', message.message_id)


class QueuePublisher(AbstractQueueHandler):
    """Wrapper to handle sending messages to a queue"""

    def __init__(
            self,
            exchange: aio_pika.abc.AbstractExchange,
            routing_key: str,
            _parent: 'RabbitMQClient'
    ):
        """
        Wrapper to handle sending messages to a queue.

        Args:
            exchange: The exchange messages will be sent to.
            routing_key: The routing key messages will be sent to.
            _parent: The client (used internally).
        """
        self._exchange = exchange
        self._routing_key = routing_key
        self._parent = _parent

    async def close(self):
        pass

    async def send(self, msg: str, wait_for_ack: bool = False):
        await self.client_connected.wait()  # avoid sending when disconnected
        message = aio_pika.Message(msg.encode())
        log.debug('←✉ Sending message: <route:%s> <msg_id:%s> Content: %s',
                  self._routing_key, message.message_id, message.body)
        await self._exchange.publish(
            message,
            routing_key=self._routing_key,
        )


class RabbitMQClient:
    """Wrapper providing a publisher/subscriber interface for a RabbitMQ connection."""

    connection: aio_pika.abc.AbstractRobustConnection | None = None
    channel: aio_pika.abc.AbstractRobustChannel
    exchange: aio_pika.abc.AbstractExchange
    _handlers: list[QueueSubscriber | QueuePublisher] = []
    connected: asyncio.Event

    def __init__(
            self,
            url: str | None = None,
            host: str = '',
            port: int = AMPQ_DEFAULT_PORT,
            login: str = '',
            password: str = '',
            exchange: str = '',
            vhost: str = '/'
    ):
        """

        Args:
            url:  RFC3986 formatted broker address. When None the other keywords are
                used for configuration.
            host: Hostname of the broker
            port: Broker port 5672 by default
            login: Username string. ‘guest’ by default.
            password: Password string. ‘guest’ by default.
            exchange: The exchange name as string.
            vhost: The server internal virtual host name to use.
        """
        self._connection_params = {
            'url': url,
            'host': host,
            'port': port,
            'login': login,
            'password': password,
            'exchange': exchange,
            'virtualhost': vhost,
            'timeout': 60,
        }

        if port == AMPQS_DEFAULT_PORT:
            self._connection_params['ssl_context'] = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            # ssl_options = aio_pika.abc.SSLOptions()
            self._connection_params['ssl'] = True

    async def connect_and_run(self) -> None:
        """Establish the connection to the server and declare an exchange."""
        log.info('Connecting to RabbitMQ server ... ')
        log.debug(f'RMQ connection parameters:\n'
                  f'url        : {self._connection_params["url"]}\n'
                  f'host       : {self._connection_params["host"]}\n'
                  f'port       : {self._connection_params["port"]}\n'
                  f'login      : {self._connection_params["login"]}\n'
                  f'password   : *****\n'
                  f'exchange   : {self._connection_params["exchange"]}\n'
                  f'virtualhost: {self._connection_params["virtualhost"]}\n'
                  f'timeout    : {self._connection_params["timeout"]}\n')

        await self._try_connecting()
        # self.connection.close_callbacks.add(self.on_server_disconnected)
        # self.connection.reconnect_callbacks.add(self.on_server_reconnected)

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        exchange_name: str = self._connection_params.pop('exchange')
        self.exchange = await self.channel.get_exchange(
            name=exchange_name,
            ensure=False,
        )

        log.info('Connection established')

    @stamina.retry(on=(AMQPConnectionError, ConnectionRefusedError), attempts=50, wait_initial=1.0)
    async def _try_connecting(self):
        self.connection = await aio_pika.connect_robust(
            **self._connection_params
        )
        await self.connection.connected.wait()  # a bit paranoid, but make sure we're connected

    @property
    def is_connected(self) -> bool:
        """Return True if the RMQ client is connected."""
        # Before connecting to the server `self.connection` is None
        return self.connection and self.connection.connected.is_set()

    # async def on_server_disconnected(self, con: aio_pika.abc.AbstractRobustConnection,
    #                                  exc: aiormq.exceptions.ConnectionClosed):
    #     # log.warning(f'Connection to RabbitMQ server lost! '
    #     #             f'(code: {exc.errno}, reason: {exc.reason} text: "{exc.strerror}")')
    #     self.connected.clear()

    # async def on_server_reconnected(self, *args):
    #     # log.info(f'Connection to RabbitMQ server reestablished. ({args})')
    #     self.connected.set()

    async def _stop_all_handlers(self) -> None:
        ...
        # TODO

    async def close(self):
        """Close the RabbitMQ connection"""
        log.info('Closing RabbitMQ connection ...')
        # await self._stop_all_handlers()  # ???
        if self.is_connected:
            await self.connection.close()

    async def subscriber(
            self,
            queue_name: str,
            callback: Callable,
            routing_key: str = ''
    ) -> QueueSubscriber | None:
        """
        Factory to create a QueueSubscriber bound to this exchange.

        Args:
            queue_name: Name of the queue to create.
            callback: Callable accepting the incoming message as parameter.
            routing_key: Routing for the queue to bind to.

        Returns:
            Instantiated QueueSubscriber object
        """
        log.debug('Creating subscription (queue: "%s", routing_key: "%s")',
                  queue_name, routing_key)

        consumer = QueueSubscriber(
            queue_name=queue_name,
            routing_key=routing_key,
            msg_callback=callback,
            _parent=self
        )
        try:
            await consumer.connect_to_queue()
            self._handlers.append(consumer)
        except (ChannelPreconditionFailed, ChannelNotFoundEntity) as exc:
            log.error(f"Can not connect to queue '{consumer.queue_name}': {exc}")
            return None
        except Exception as exc:
            log.error(f"Error connecting to queue '{consumer.queue_name}': {exc}")
            raise exc

        return consumer

    async def publisher(self, routing_key: str) -> QueuePublisher:
        """
        Factory to create a QueueSubscriber bound to this exchange.

        Args:
            routing_key: Routing for the queue to bind to.

        Returns:
            Instantiated QueuePublisher object.
        """
        log.debug('Creating publisher (routing_key: "%s")', routing_key)

        publisher = QueuePublisher(
            exchange=self.exchange,
            routing_key=routing_key,
            _parent=self
        )
        self._handlers.append(publisher)
        return publisher

    async def does_queue_exist(self, queue_name: str):
        connection = None
        try:
            connection = await aio_pika.connect_robust(**self._connection_params)
            async with connection.channel() as channel:
                await channel.declare_queue(queue_name, passive=True)
            log.debug(f"Queue '{queue_name}' exists.")
            return True

        except (ChannelPreconditionFailed, ChannelNotFoundEntity) as e:
            log.error(f"Queue '{queue_name}' does not exist, can not connect and will not create. {e}")
            return False
        except Exception as e:
            log.error(f"Error checking if queue '{queue_name}' does exist. {e}")
            raise e

        finally:
            if connection:
                await connection.close()