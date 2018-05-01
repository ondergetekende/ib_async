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
                          instrument.contract_id,
                          instrument.symbol,
                          instrument.security_type,
                          instrument.last_trade_date or instrument.contract_month,
                          instrument.strike,
                          instrument.right,
                          instrument.multiplier,
                          instrument.exchange,
                          instrument.primary_exchange,
                          instrument.currency,
                          instrument.local_symbol,
                          instrument.trading_class,
                          include_expired,
                          security_id_type,
                          security_id)
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
        contract = self._pending_contract_updates.get(request_id)
        if not contract:
            contract = self._pending_contract_updates[request_id] = Instrument(self)

        contract.symbol = message.read(str)
        contract.security_type = message.read(SecurityType)
        contract.last_trade_date = message.read(str)
        contract.strike = message.read(float)
        contract.right = message.read(str)
        contract.exchange = message.read(str)
        contract.currency = message.read(str)
        contract.local_symbol = message.read(str)
        contract.market_name = message.read(str)
        contract.trading_class = message.read(str)
        contract.contract_id = message.read(int)
        contract.minimum_tick = message.read(float)

        contract.market_data_size_multiplier = message.read(str, min_version=ProtocolVersion.MD_SIZE_MULTIPLIER)

        contract.multiplier = message.read(str)
        contract.order_types = message.read(str).split(',')
        contract.valid_exchanges = message.read(str).split(',')
        contract.price_magnifier = message.read(int)
        contract.underlying_contract_id = message.read(int)
        contract.long_name = message.read(str)
        contract.primary_exchange = message.read(str)
        contract.contract_month = message.read(str)
        contract.industry = message.read(str)
        contract.category = message.read(str)
        contract.subcategory = message.read(str)
        contract.time_zone = message.read(str)
        contract.trading_hours = message.read(str)
        contract.liquid_hours = message.read(str)
        contract.ev_rule = message.read(str)
        contract.ev_multiplier = message.read(str)
        contract.security_ids = message.read(typing.Dict[SecurityIdentifierType, str])

        contract.aggregated_group = message.read(str, min_version=ProtocolVersion.AGG_GROUP)

        contract.underlying_symbol = message.read(str, min_version=ProtocolVersion.UNDERLYING_INFO)
        contract.underlying_security_type = message.read(SecurityType)

        contract.market_rule_ids = message.read(str, min_version=ProtocolVersion.MARKET_RULES)
        contract.real_expiration_date = message.read(str, min_version=ProtocolVersion.REAL_EXPIRATION_DATE)

    def _handle_contract_data_end(self, request_id: RequestId):
        contract = self._pending_contract_updates.get(request_id)
        self.resolve_future(request_id, contract)
