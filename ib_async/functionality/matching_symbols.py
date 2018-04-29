import logging
import typing

from ib_async.instrument import Instrument, SecurityType
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface, IncomingMessage
from ib_async.protocol_versions import ProtocolVersion

LOG = logging.getLogger(__name__)


class MatchingSymbolsMixin(ProtocolInterface):

    def _handle_symbol_samples(self, request_id: RequestId, num_contracts: int, message: IncomingMessage):
        result = []
        for _ in range(num_contracts):
            contract = Instrument()

            contract.contract_id = message.read(int)
            contract.symbol = message.read(str)
            contract.security_type = SecurityType(message.read(str))
            contract.primary_exchange = message.read(str)
            contract.currency = message.read(str)

            message.read(typing.List[str])  # derivative_security_types

            result.append(contract)

        self.resolve_future(request_id, result)

    def matching_symbols(self, pattern: str) -> typing.Awaitable[typing.List[Instrument]]:
        self.check_feature(ProtocolVersion.REQ_MATCHING_SYMBOLS, "matching symbols request.")

        request_id, future = self.make_future()
        self.send_message(Outgoing.REQ_MATCHING_SYMBOLS, request_id, pattern)
        return future
