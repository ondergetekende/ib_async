import logging
import typing

from ib_async.instrument import Instrument, SecurityType, SecurityIdentifierType
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface, IncomingMessage
from ib_async.protocol_versions import ProtocolVersion

LOG = logging.getLogger(__name__)


class ContractDetailsMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self._pending_contract_updates = {}  # type: typing.Dict[RequestId, Instrument]

    def refresh_instrument(self, instrument: Instrument, include_expired=False) -> typing.Awaitable[Instrument]:
        request_id, future = self.make_future()

        if instrument.security_ids:
            security_id_type, security_id = next(iter(instrument.security_ids.items()))
        else:
            security_id_type = security_id = None

        self.send_message(Outgoing.REQ_CONTRACT_DATA, 8, request_id,
                          instrument,
                          include_expired, security_id_type, security_id)
        self._pending_contract_updates[request_id] = instrument

        return future

    def get_instrument_by_id(self, security_id: str,
                             security_id_type: typing.Union[SecurityIdentifierType, str],
                             include_expired=False) -> typing.Awaitable[Instrument]:
        request_id, future = self.make_future()

        self.send_message(Outgoing.REQ_CONTRACT_DATA, 8, request_id,
                          0,  # contract_id
                          "",  # symbol
                          None,  # security_type
                          None,  # last_trade_date or contract.contract_month
                          None,  # strike
                          None,  # right
                          None,  # multiplier
                          None,  # exchange
                          None,  # primary_exchange
                          None,  # currency
                          None,  # local_symbol
                          None,  # trading_class
                          include_expired,
                          SecurityIdentifierType(security_id_type),
                          security_id)

        return future

    def get_instrument_by_local_symbol(self, symbol: str, exchange: str, security_type=SecurityType.Stock,
                                       trading_class="", include_expired=False) -> typing.Awaitable[Instrument]:
        request_id, future = self.make_future()

        self.send_message(
            Outgoing.REQ_CONTRACT_DATA, 8, request_id,
            0,  # contract_id
            "",  # symbol
            security_type,  # security_type
            None,  # last_trade_date or contract.contract_month
            None,  # strike
            None,  # right
            None,  # multiplier
            exchange,  # exchange
            None,  # primary_exchange
            None,  # currency
            symbol,  # local_symbol
            trading_class,  # trading_class
            include_expired,
            None,  # security_id_type,
            None,  # security_id
        )

        return future

    def _handle_contract_data(self, request_id: RequestId, message: IncomingMessage):
        # fast forward to instrument id position, so that we avoid making new contracts when existing ones can be reused
        # This is required for proper event routing elsewhere

        instrument = self._pending_contract_updates.get(request_id)

        if not instrument:
            message.idx += 10
            instrument = Instrument.get_instance_from(message)
            self._pending_contract_updates[request_id] = instrument
            message.idx -= 10

        instrument.symbol = message.read(str)
        instrument.security_type = message.read(SecurityType)
        instrument.last_trade_date = message.read(str)
        instrument.strike = message.read(float)
        instrument.right = message.read(str)
        instrument.exchange = message.read(str)
        instrument.currency = message.read(str)
        instrument.local_symbol = message.read(str)
        instrument.market_name = message.read(str)
        instrument.trading_class = message.read(str)
        instrument.contract_id = message.read(int)
        instrument.minimum_tick = message.read(float)

        instrument.market_data_size_multiplier = message.read(str, min_version=ProtocolVersion.MD_SIZE_MULTIPLIER)

        instrument.multiplier = message.read(str)
        instrument.order_types = message.read(str).split(',')
        instrument.valid_exchanges = message.read(str).split(',')
        instrument.price_magnifier = message.read(int)
        instrument.underlying_contract_id = message.read(int)
        instrument.long_name = message.read(str)
        instrument.primary_exchange = message.read(str)
        instrument.contract_month = message.read(str)
        instrument.industry = message.read(str)
        instrument.category = message.read(str)
        instrument.subcategory = message.read(str)
        instrument.time_zone = message.read(str)
        instrument.trading_hours = message.read(str)
        instrument.liquid_hours = message.read(str)
        instrument.ev_rule = message.read(str)
        instrument.ev_multiplier = message.read(str)
        instrument.security_ids = message.read(typing.Dict[SecurityIdentifierType, str])

        instrument.aggregated_group = message.read(str, min_version=ProtocolVersion.AGG_GROUP)

        instrument.underlying_symbol = message.read(str, min_version=ProtocolVersion.UNDERLYING_INFO)
        instrument.underlying_security_type = message.read(SecurityType, min_version=ProtocolVersion.UNDERLYING_INFO)

        instrument.market_rule_ids = message.read(str, min_version=ProtocolVersion.MARKET_RULES)
        instrument.real_expiration_date = message.read(str, min_version=ProtocolVersion.REAL_EXPIRATION_DATE)

    def _handle_contract_data_end(self, request_id: RequestId):
        contract = self._pending_contract_updates.get(request_id)
        self.resolve_future(request_id, contract)
