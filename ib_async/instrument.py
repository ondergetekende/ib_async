import enum
import logging
import typing

from ib_async import protocol, tick_types

LOG = logging.getLogger(__name__)

# lookup table for accompanying sizes for price ticks
_tick_type_size_lookup = {
    tick_types.TickType.Bid: tick_types.TickType.BidSize,
    tick_types.TickType.Ask: tick_types.TickType.AskSize,
    tick_types.TickType.Last: tick_types.TickType.LastSize,
    tick_types.TickType.DelayedBid: tick_types.TickType.DelayedBidSize,
    tick_types.TickType.DelayedAsk: tick_types.TickType.DelayedAskSize,
    tick_types.TickType.DelayedLast: tick_types.TickType.DelayedLastSize,
}


class SecurityType(str, enum.Enum):
    UNSPECIFIED = ''

    Stock = 'STK'
    Future = 'FUT'
    Index = 'IND'


class SecurityIdentifierType(str, enum.Enum):
    UNSPECIFIED = ''

    CUSIP = "CUSIP"
    SEDOL = "SEDOL"
    ISIN = "ISIN"
    RIC = "RIC"


class UnderlyingComponent(protocol.Serializable):
    def __init__(self):
        self.contract_id = 0
        self.delta = 0.0
        self.price = 0.0

    def serialize(self, protocol_version):
        return self.contract_id, self.delta, self.price

    def deserialize(self, message: protocol.IncomingMessage):
        self.contract_id = message.read(int)
        self.delta = message.read(float)
        self.price = message.read(float)


class Instrument:
    def __init__(self, parent: protocol.ProtocolInterface) -> None:
        self._parent = parent
        self._market_data_request_id = None  # type: protocol.RequestId
        self._realtime_bars_request_id = None  # type: protocol.RequestId
        self.market_data_timeliness = tick_types.MarketDataTimeliness.RealTime
        self._tick_data = {}  # type: typing.Dict[tick_types.TickType, typing.Any]
        self._tick_attributes = {}  # type: typing.Dict[tick_types.TickType, tick_types.TickAttributes]

        self.symbol = ""
        self.security_type = SecurityType.UNSPECIFIED
        self.last_trade_date = ""
        self.strike = 0.0
        self.right = ""
        self.exchange = ""
        self.currency = ""
        self.local_symbol = ""
        self.market_name = ""
        self.trading_class = ""
        self.contract_id = 0
        self.minimum_tick = 0.0
        self.market_data_size_multiplier = ""
        self.multiplier = ""
        self.order_types = []  # type: typing.List[str]
        self.valid_exchanges = []  # type: typing.List[str]
        self.price_magnifier = 0
        self.underlying_contract_id = 0
        self.long_name = ""
        self.primary_exchange = ""
        self.contract_month = ""
        self.industry = ""
        self.category = ""
        self.subcategory = ""
        self.time_zone = ""
        self.trading_hours = ""
        self.liquid_hours = ""
        self.ev_rule = ""
        self.ev_multiplier = ""
        self.security_ids = {}  # type: typing.Dict[SecurityIdentifierType, str]
        self.aggregated_group = ""
        self.underlying_symbol = ""
        self.underlying_security_type = SecurityType.UNSPECIFIED
        self.market_rule_ids = ""
        self.real_expiration_date = ""
        self.underlying_component = None  # type: UnderlyingComponent

    def tick(self, tick_type: tick_types.TickType, value: typing.Any, size: float = None,
             attributes: tick_types.TickAttributes = None):

        if size is not None:
            try:
                self._tick_data[_tick_type_size_lookup[tick_type]] = size
            except KeyError:
                if size:
                    LOG.warning('received tick %s with size, but have no way to store it')

        self._tick_data[tick_type] = value
        if attributes is not None:
            self._tick_attributes[tick_type] = attributes

    def fetch_market_data(self, tick_types: typing.Iterable[tick_types.TickTypeGroup] = ()):
        """Retrieve a single snaphot of market data for this contract."""
        from .functionality.market_data import MarketDataMixin
        parent = typing.cast(MarketDataMixin, self._parent)
        return parent.get_market_data(self, tick_types, snapshot=True, regulatory_snapshot=False)

    def subscribe_market_data(self, tick_types: typing.Iterable[tick_types.TickTypeGroup] = ()):
        """Subscribe to market data for this contract."""
        from .functionality.market_data import MarketDataMixin
        parent = typing.cast(MarketDataMixin, self._parent)
        return parent.get_market_data(self, tick_types, snapshot=False, regulatory_snapshot=False)

    def unsubscribe_market_data(self):
        if self._market_data_request_id:
            from .functionality.market_data import MarketDataMixin
            parent = typing.cast(MarketDataMixin, self._parent)
            parent.cancel_market_data(self)

    def subscribe_realtime_bars(self):
        from .functionality.realtime_bars import RealtimeBarsMixin
        parent = typing.cast(RealtimeBarsMixin, self._parent)
        parent.subscribe_realtime_bars(self)

    def unsubscribe_realtime_bars(self):
        from .functionality.realtime_bars import RealtimeBarsMixin
        parent = typing.cast(RealtimeBarsMixin, self._parent)
        parent.unsubscribe_realtime_bars(self)

    def handle_realtime_bar(self, time: int, open: float, high: float, low: float, close: float,
                            volume: int, average: float, count: int):
        pass
