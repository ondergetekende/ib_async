import abc
import asyncio
import datetime
import enum
import inspect
import logging
import struct
import typing

from ib_async.errors import OutdatedServerError, NotConnectedError, ApiException, warning_codes
from ib_async.messages import Outgoing, Incoming, messages_with_version
from ib_async.protocol_versions import ProtocolVersion

LOG = logging.getLogger(__name__)
LOG_MESSAGES = LOG.getChild('messages')

RequestId = typing.NewType('RequestId', int)
SerializableField = typing.Union[str, float, int, RequestId,
                                 typing.Dict[str, str],
                                 typing.List[str], bool,
                                 enum.Enum, None,
                                 "Serializable"]

T = typing.TypeVar('T')
TK = typing.TypeVar('TK')
TV = typing.TypeVar('TV')


class IncomingMessage:
    def __init__(self, fields: typing.Iterable[str], source: "ProtocolInterface") -> None:
        self.fields = list(fields)
        self.field_parsed = typing.cast(typing.List[SerializableField], fields)
        self.idx = 0
        self.source = source
        self.message_type = None  # type: Incoming
        self.message_version = 0

        self.reset()

    @property
    def protocol_version(self):
        return self.source.version

    def reset(self):
        self.idx = 0
        self.message_type = self.read(Incoming)

        if self.protocol_version < messages_with_version.get(self.message_type, 0):
            self.message_version = self.read(int)
        else:
            self.message_version = int(self.protocol_version)

    def invoke_handler(self, handler: typing.Callable) -> typing.Any:
        signature = inspect.signature(handler)
        call_data = []  # type: typing.List[typing.Any]

        for parameter in signature.parameters.values():
            if parameter.kind == 2:
                call_data.extend(self.fields[self.idx:])
                break

            assert parameter.annotation != inspect.Parameter.empty, "Untyped parameter %s:%s" % (
                handler.__name__, parameter.name)

            assert parameter.kind in (0, 1)
            if parameter.annotation == IncomingMessage:
                call_data.append(self)
            else:
                call_data.append(self.read(parameter.annotation))

        return handler(*call_data)

    @property
    def is_eof(self):
        return self.idx == len(self.fields)

    def peek(self, the_type: typing.Type[T], *,
             min_version: ProtocolVersion = None, max_version: ProtocolVersion = None,
             min_message_version: int = None, max_message_version: int = None,
             default: typing.Optional[T] = None):

        idx = self.idx
        try:
            return self.read(the_type, min_version=min_version, max_version=max_version,
                             min_message_version=min_message_version, max_message_version=max_message_version,
                             default=default)
        finally:
            self.idx = idx

    def read(self, the_type: typing.Type[T] = str, *,  # type: ignore
             min_version: ProtocolVersion = None, max_version: ProtocolVersion = None,
             min_message_version: int = None, max_message_version: int = None,
             default: typing.Optional[T] = None):

        # Apply message version restrictions
        if min_version and min_version > self.protocol_version:
            return default

        if max_version and max_version <= self.protocol_version:
            return default

        if min_message_version and min_message_version > self.message_version:
            return default

        if max_message_version and max_message_version <= self.message_version:
            return default

        idx = self.idx
        result = self._read_inner(the_type)
        self.field_parsed[idx] = result  # type:ignore
        return result

    def _read_inner(self, the_type: typing.Type[T]) -> T:  # type: ignore
        """Consume one or more network-representation fields, and turn it into the provided python type."""

        if inspect.isclass(the_type) and issubclass(the_type, Serializable):
            result = the_type.get_instance_from(self)
            result.deserialize(self)
            return result  # type: ignore

        # Start reading a field
        text = self.fields[self.idx]
        self.idx += 1

        if the_type == RequestId:
            return RequestId(int(text))  # type: ignore

        if inspect.isclass(the_type) and issubclass(the_type, str):
            return the_type(text)  # type: ignore

        if not text:
            return None

        if the_type.__class__ == typing.Union:
            # Unpack optionals (which are actually unions with None)
            args = set(the_type.__args__)  # type: ignore  # noqa
            args = args.difference({type(None)})  # Remove the NoneType
            if len(args) == 1:
                the_type = args.pop()

        if the_type is bool:
            # Booleans are transmitted as integers. Zero is False
            return int(text) != 0  # type: ignore

        if issubclass(the_type, enum.Enum):
            # Attempt to parse an enum as text, or as int
            try:
                return the_type(text)  # type: ignore
            except ValueError:
                pass
            try:
                return the_type(int(text))  # type: ignore
            except ValueError:
                pass
            return text  # type: ignore

        if issubclass(the_type, datetime.datetime):
            return the_type.strptime(text, "%Y%m%d  %H:%M:%S")  # type: ignore

        if issubclass(the_type, datetime.date):
            return datetime.datetime.strptime(text, "%Y%m%d").date()  # type: ignore

        if issubclass(the_type, int):
            result = the_type(text)
            return None if result >= 2147483647 else result  # type: ignore

        if issubclass(the_type, float):
            result = the_type(text)  # type: ignore
            return None if result >= 1.7976931348623157E308 else result  # type: ignore

        if the_type is dict:
            the_type = typing.Dict[str, str]  # type: ignore

        if the_type is list:
            the_type = typing.List[str]  # type: ignore

        if issubclass(the_type, typing.Dict):
            key_type, value_type = the_type.__args__  # type: ignore

            # We can't go straight to a dict comprehension, as that would mess up the order
            pairs = [(self._read_inner(key_type), self._read_inner(value_type))
                     for _ in range(int(text))]  # type: ignore
            return dict(pairs)  # type: ignore

        if issubclass(the_type, typing.List):
            value_type, = the_type.__args__  # type: ignore
            # IB only supports str/str dicts, stored as a KVP array
            return [self._read_inner(value_type) for _ in range(int(text))]  # type: ignore

        raise ValueError('unsupported type: %s' % the_type)

    def __repr__(self):
        return "IncomingMessage(%s, %s, protocol_version=%s)" % (
            self.field_parsed[0], ", ".join(repr(f) for f in self.field_parsed[1:]),
            self.protocol_version)


class OutgoingMessage:
    def __init__(self, message_type: Outgoing, *fields,
                 protocol_version: ProtocolVersion = None) -> None:
        self.fields_encoded = []  # type: typing.List[bytes]
        self.fields = []  # type: typing.List[SerializableField]
        self.protocol_version = protocol_version

        self.message_type = Outgoing(int(message_type))

        self.add(self.message_type)
        for field in fields:
            self.add(field)

    def add(self, *fields: SerializableField,
            min_version: ProtocolVersion = None,
            max_version: ProtocolVersion = None):
        if min_version and self.protocol_version < min_version:
            pass
        elif max_version and self.protocol_version >= max_version:
            pass
        else:
            for field in fields:
                self._add_field(field)

    def _add_field(self, field: SerializableField, raw_field=None):
        if isinstance(field, Serializable):
            field.serialize(self)
            return

        self.fields.append(raw_field if raw_field is not None else field)

        if isinstance(field, enum.Enum):
            field = field.value  # Enums are sent as their underlying type

        if field is None:
            self.fields_encoded.append(b"")
        elif isinstance(field, str):  # bool type is encoded as int
            self.fields_encoded.append(field.encode())
        elif isinstance(field, bool):  # bool type is encoded as int
            self.fields_encoded.append(b"1" if field else b'0')
        elif isinstance(field, (float, int)):
            self.fields_encoded.append(str(field).encode())
        elif isinstance(field, datetime.datetime):
            # 20180201 10:00:00 GMT
            if field.tzinfo:
                field = field.strftime("%Y%m%d  %H:%M:%S %Z")
            else:
                field = field.strftime("%Y%m%d  %H:%M:%S")
            self.fields_encoded.append(str(field).encode())
        elif isinstance(field, datetime.date):
            self.fields_encoded.append(field.strftime("%Y%m%d").encode())
        elif isinstance(field, dict):
            self._add_field(len(field), field)
            for key, value in field.items():
                self._add_field(key)
                self._add_field(value)
        elif isinstance(field, list):
            self._add_field(len(field), field)
            for value in field:
                self._add_field(value)
        else:
            raise ValueError('unsupported type')

    def serialize(self) -> bytes:
        encoded_message = b"\x00".join(self.fields_encoded) + b'\x00'
        return struct.pack("!I", len(encoded_message)) + encoded_message

    def __repr__(self):
        return "OutgoingMessage(%s, %s)" % (self.fields[0], ", ".join(repr(f) for f in self.fields[1:]))


class Serializable(abc.ABC):
    @classmethod
    def get_instance_from(cls, source: IncomingMessage):
        return cls()

    @abc.abstractmethod
    def serialize(self, message: OutgoingMessage):
        """Return serializable fields in network-order"""
        raise NotImplementedError()

    @abc.abstractmethod
    def deserialize(self, message: IncomingMessage):
        """Read this object from a network-message"""
        raise NotImplementedError()


class ProtocolInterface(abc.ABC):
    def __init__(self):
        super().__init__()
        self.version = None  # type: ProtocolVersion

    def send_message(self, message_id: Outgoing, *fields: SerializableField):
        self.send(OutgoingMessage(message_id, *fields, protocol_version=self.version))

    @abc.abstractmethod
    def send(self, message: OutgoingMessage):
        """Send a prebuilt message to IB."""
        pass

    @abc.abstractmethod
    def check_feature(self, min_version: ProtocolVersion, feature: str):
        """Checks if we're using a minimal protocol level, and raisess an exception otherwise."""

    @abc.abstractmethod
    def make_request_id(self) -> RequestId:
        """Generates a unique request id and associated future"""

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
        LOG_MESSAGES.debug("SENDING %r", to_send)
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
        message = IncomingMessage(fields, source=self)

        # Find a general-purpose handler
        handler = getattr(self, "_handle_%s" % message.message_type.name.lower(), None)

        if handler:
            try:
                message.invoke_handler(handler)
            finally:
                LOG_MESSAGES.debug('received %r', message)
        else:
            LOG.debug('no handler for %r (v%i)', message, message.message_version)

    def send(self, message: OutgoingMessage):
        LOG_MESSAGES.debug('send %r', message)
        self.writer.write(message.serialize())

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
        if future and not future.done():
            future.set_result(result)

    # ---- Generic handlers ----

    def _handle_err_msg(self, request_id: RequestId, error_code: int, error_message: str):
        if error_code in warning_codes:
            LOG.info("Received warning#%i from TWS: %s", error_code, error_message)
        else:
            future = self._pending_responses.pop(request_id, None)
            if future:
                future.set_exception(ApiException(error_code, error_message))
            else:
                LOG.warning("Received error#%i from TWS: %s", error_code, error_message)
