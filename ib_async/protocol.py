import abc
import asyncio
import enum
import inspect
import logging
import struct
import typing

from ib_async.errors import OutdatedServerError, NotConnectedError, ApiException
from ib_async.messages import Outgoing, Incoming, messages_with_version
from ib_async.protocol_versions import ProtocolVersion

LOG = logging.getLogger(__name__)

RequestId = typing.NewType('RequestId', int)
SerializableField = typing.Union[str, float, int, RequestId,
                                 typing.Dict[str, str],
                                 typing.List[str], bool,
                                 enum.Enum, None]

T = typing.TypeVar('T')
TK = typing.TypeVar('TK')
TV = typing.TypeVar('TV')


class IncomingMessage:
    def __init__(self, fields: typing.List[str], protocol_version: ProtocolVersion) -> None:
        self.fields = fields
        self.idx = 0
        self.protocol_version = protocol_version
        self.message_version = 0

        self.reset()

    def reset(self):
        self.idx = 0
        self.message_type = self.read(Incoming)
        if self.message_type in messages_with_version:
            self.message_version = self.read(int)
        else:
            self.message_version = 0

    def invoke_handler(self, handler: typing.Callable) -> typing.Any:
        signature = inspect.signature(handler)
        call_data = []  # type: typing.List[typing.Any]

        for parameter in signature.parameters.values():
            assert parameter.kind in (0, 1)
            if parameter.annotation == IncomingMessage:
                call_data.append(self)
            else:
                call_data.append(self.read(parameter.annotation))

        return handler(*call_data)

    @property
    def is_eof(self):
        return self.idx == len(self.fields)

    def read(self, the_type: typing.Type[T], *,
             min_version: ProtocolVersion = None, max_version: ProtocolVersion = None,
             min_message_version: int = None, max_message_version: int = None,
             default: typing.Optional[T] = None
             ) -> T:  # type: ignore
        """Consome one or more network-representation fields, and turn it into the provided python type."""

        # Apply message version restrictions
        if min_version and min_version > self.protocol_version:
            return default

        if max_version and max_version <= self.protocol_version:
            return default

        if min_message_version and min_message_version > self.message_version:
            return default

        if max_message_version and max_message_version <= self.message_version:
            return default

        # Start reading a field
        text = self.fields[self.idx]
        self.idx += 1

        if the_type == RequestId:
            return RequestId(int(text))  # type: ignore

        if issubclass(the_type, str):
            return the_type(text)  # type: ignore

        if not text:
            return None

        if the_type is bool:
            # Booleans are transmitted as integers. Zero is False
            return int(text) != 0  # type: ignore

        if issubclass(the_type, enum.Enum):
            # Attempt to parse an enum as text, or as int
            try:
                return the_type(text)  # type: ignore
            except ValueError:
                return the_type(int(text))  # type: ignore

        if issubclass(the_type, int):
            return the_type(text)  # type: ignore

        if issubclass(the_type, float):
            return the_type(text)  # type: ignore

        if the_type is dict:
            the_type = typing.Dict[str, str]  # type: ignore

        if the_type is list:
            the_type = typing.List[str]  # type: ignore

        if issubclass(the_type, typing.Dict):
            key_type, value_type = the_type.__args__  # type: ignore

            # We can't go straight to a dict comprehension, as that would mess up the order
            pairs = [(self.read(key_type), self.read(value_type))
                     for _ in range(int(text))]
            return dict(pairs)  # type: ignore

        if issubclass(the_type, typing.List):
            value_type, = the_type.__args__  # type: ignore
            # IB only supports str/str dicts, stored as a KVP array
            return [self.read(value_type) for _ in range(int(text))]  # type: ignore

        raise ValueError('unsupported type')


class ProtocolInterface(abc.ABC):
    def __init__(self):
        super().__init__()
        self.version = None  # type: ProtocolVersion

    @abc.abstractmethod
    def send_message(self, message_id: Outgoing, *fields: SerializableField):
        """Send a message to IB."""
        pass

    @abc.abstractmethod
    def check_feature(self, min_version: ProtocolVersion, feature: str):
        """Checks if we're using a minimal protocol level, and raisess an exception otherwise."""

    @abc.abstractmethod
    def make_future(self) -> typing.Tuple[RequestId, asyncio.Future]:
        """Generates a unique request id and associated future"""

    @abc.abstractmethod
    def resolve_future(self, request_id: RequestId, result):
        """Resolves a future identified by a request id"""


class Protocol(ProtocolInterface):
    """Encapsulates low-level communication

    This includes connecting, protocol negotiation, message and field splitting.
    """

    def __init__(self) -> None:
        super().__init__()
        self.is_connected = False
        self.optional_capabilities = None  # type: str

        self.reader = None  # type: asyncio.StreamReader
        self.writer = None  # type: asyncio.StreamWriter

        self.next_request_id = RequestId(1000)
        self._pending_responses = {}  # type: typing.Dict[RequestId, asyncio.Future]

    def make_request_id(self):
        result = self.next_request_id
        self.next_request_id += 1
        return result

    def serialize(self, field: SerializableField) -> bytes:
        """Take a single field, and turn it into the appropriate network representation"""
        if isinstance(field, enum.Enum):
            field = field.value  # Enums are sent as their underlying type

        if field is None:
            return b""

        if isinstance(field, str):  # bool type is encoded as int
            return field.encode()

        if isinstance(field, bool):  # bool type is encoded as int
            return b"1" if field else b'0'

        if isinstance(field, (float, int)):
            return str(field).encode()

        if isinstance(field, dict):
            vals = [self.serialize(len(field))]
            for key, value in field.items():
                vals.extend([self.serialize(key), self.serialize(value)])
            return b"\0".join(vals)

        if isinstance(field, list):
            vals = [self.serialize(len(field))]
            vals.extend(self.serialize(value) for value in field)
            return b"\0".join(vals)

        raise ValueError('unsupported type')

    async def connect(self, hostname: str, port: int, client_id=None):
        """Establish a connection to the TWS/IBGW server."""

        # We have not negotiated a version yet
        self.version = None

        # Establish the connection
        self.reader, self.writer = await asyncio.open_connection(hostname, port)

        delayed_messages = await self._negotiate_version(client_id)

        for message in delayed_messages:
            self.dispatch_message(message)
        asyncio.ensure_future(self._message_loop())

    async def _negotiate_version(self, client_id):
        # Negotiate a version
        versions = b"v%d..%d" % (ProtocolVersion.MIN_CLIENT, ProtocolVersion.MAX_CLIENT)
        to_send = b'API\0' + struct.pack("!I", len(versions)) + versions
        LOG.debug("SENDING %r", to_send)
        self.writer.write(to_send)

        # Wait for the negotiation response. Apparently it is also possible to receive other messages before the
        # version is negotiated, we need to delay those until the version is established.

        delayed_messages = []
        while True:
            message = await self._read_message()
            if len(message) == 2:
                self.version = ProtocolVersion(int(message[0]))

                assert self.version >= ProtocolVersion.MIN_CLIENT
                assert self.version <= ProtocolVersion.MAX_CLIENT

                LOG.info("Using protocol %s", self.version)
                LOG.info("Server time %s", message[1])
                break

            delayed_messages.append(message)

        # Confirm the negotiated version
        self.send_message(Outgoing.START_API, 2, client_id, self.optional_capabilities)

        return delayed_messages

    async def disconnect(self):
        writer = self.writer
        self.writer = None
        if self.reader:
            self.reader.feed_eof()
            self.reader = None

        if writer:
            await self.writer.write_eof()

    async def _message_loop(self):
        while self.reader:
            self.dispatch_message(await self._read_message())

    async def _read_message(self) -> typing.List[str]:
        size_buf = await self.reader.readexactly(4)
        size = struct.unpack("!I", size_buf)[0]
        message = await self.reader.readexactly(size)
        return [field.decode() for field in message[:-1].split(b'\0')]

    def dispatch_message(self, fields: typing.List[str]):
        assert len(fields) >= 1
        message = IncomingMessage(fields, protocol_version=self.version)

        # Find a general-purpose handler
        handler = (getattr(self, "_handle_%s" % message.message_type.name.lower(), None) or
                   getattr(self, "_handle_%s_v%i" % (message.message_type.name.lower(), message.message_version),
                           None))

        if handler:
            message.invoke_handler(handler)
        else:
            LOG.debug('no handler for %s v%i', message.message_type, message.message_version)

    def send_message(self, message_id: Outgoing, *fields: SerializableField):
        encoded_fields = b"\0".join(self.serialize(field) for field in fields)
        message = b'%i\0%b\0' % (message_id.value, encoded_fields)

        LOG.debug("sending %s (%s)", message_id, encoded_fields)
        to_send = struct.pack("!I", len(message)) + message
        self.writer.write(to_send)

    def check_feature(self, min_version: ProtocolVersion, feature: str = None):
        if not self.version:
            raise NotConnectedError()

        if self.version < min_version:
            raise OutdatedServerError(feature)

    # ---- Futures handling ----

    def make_future(self) -> typing.Tuple[RequestId, asyncio.Future]:
        request_id = self.make_request_id()
        future = asyncio.Future()  # type: asyncio.Future
        self._pending_responses[request_id] = future
        return request_id, future

    def resolve_future(self, request_id: RequestId, result):
        future = self._pending_responses.pop(request_id, None)
        future.set_result(result)

    # ---- Generic handlers ----

    def _handle_err_msg(self, request_id: RequestId, error_code: int, error_message: str):
        future = self._pending_responses.pop(request_id, None)
        if future:
            future.set_exception(ApiException(error_code, error_message))
        else:
            LOG.warning("Received error#%i from TWS: %s", error_code, error_message)
