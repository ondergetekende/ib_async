import asyncio
import typing

import ib_async.protocol


class FunctionalityTestHelper(ib_async.protocol.ProtocolInterface):
    """A helper to allow testing the mixins outside of network conditions."""

    def __init__(self):
        super().__init__()

        self.next_id = ib_async.protocol.RequestId(42)
        self.futures = {}
        self.sent = []

    def send_message(self, message_id: ib_async.protocol.Outgoing,
                     *fields: ib_async.protocol.SerializableField):
        """Send a message to IB."""
        msg = []  # type: typing.List[typing.Any]
        msg.append(message_id)
        msg.extend(fields)
        self.sent.append(msg)

    def check_feature(self, min_version: ib_async.protocol.ProtocolVersion, feature: str):
        """Checks if we're using a minimal protocol level, and raisess an exception otherwise."""
        pass

    def make_future(self) -> typing.Tuple[ib_async.protocol.RequestId, asyncio.Future]:
        """Generates a unique request id and associated future"""
        self.next_id += 1
        self.futures[self.next_id] = asyncio.Future()
        return self.next_id, self.futures[self.next_id]

    def resolve_future(self, request_id: ib_async.protocol.RequestId, result):
        """Resolves a future identified by a request id"""
        self.futures[request_id].set_result(result)

    def dispatch_message(self, fields: typing.List[str]):
        message = ib_async.protocol.IncomingMessage(fields, protocol_version=self.version)

        msg_name = message.message_type.name.lower()
        # Find a general-purpose handler
        handler = (getattr(self, "_handle_%s" % msg_name, None) or
                   getattr(self, "_handle_%s_v%i" % (msg_name, message.message_version), None))

        message.invoke_handler(handler)
