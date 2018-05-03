import enum
import logging
import typing

from ib_async import protocol, tick_types
from ib_async.bar import Bar, BarType

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

MarketDepthEntry = typing.NamedTuple('MarketDepthEntry', (
    ('price', float),
    ('size', int),
    ('market_maker', str)
))


class SecurityType(str, enum.Enum):
    UNSPECIFIED = ''

    Stock = 'STK'
    Cash = 'CASH'
    Future = 'FUT'
    Index = 'IND'
    Bag = 'BAG'


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


class Instrument(protocol.Serializable):
    def __init__(self, parent: protocol.ProtocolInterface) -> None:
        self._parent = parent
        self._market_data_request_id = None  # type: protocol.RequestId
        self._realtime_bars_request_id = None  # type: protocol.RequestId
        self._historical_data_request_id = None  # type: protocol.RequestId
        self._market_depth_request_id = None  # type: protocol.RequestId
        self.market_data_timeliness = tick_types.MarketDataTimeliness.RealTime
        self._tick_data = {}  # type: typing.Dict[tick_types.TickType, typing.Any]
        self._tick_attributes = {}  # type: typing.Dict[tick_types.TickType, tick_types.TickAttributes]

        self.market_depth_ask = []  # type: typing.List[MarketDepthEntry]
        self.market_depth_bid = []  # type: typing.List[MarketDepthEntry]

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

    def serialize(self, protocol_version):
        # This is the most common (but not the only) way to serialize instruments.
        yield self.contract_id
        yield self.symbol
        yield self.security_type
        yield self.last_trade_date or self.contract_month
        yield self.strike
        yield self.right
        yield self.multiplier
        yield self.exchange
        yield self.primary_exchange
        yield self.currency
        yield self.local_symbol
        yield self.trading_class

    def deserialize(self, message: protocol.IncomingMessage):
        # There are several ways a contract is deserialized. I have yet to determine the most common one.
        raise NotImplementedError()

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

    def handle_realtime_bar(self, bar: Bar):
        pass

    def get_historic_bars(self, end_date, duration, bar_size,
                          what_to_show=BarType.Midpoint) -> typing.Awaitable[typing.List[Bar]]:
        from .functionality.realtime_bars import RealtimeBarsMixin
        parent = typing.cast(RealtimeBarsMixin, self._parent)
        return parent.get_historical_bars(self, end_date, duration, bar_size=bar_size, what_to_show=what_to_show)

    def subscribe_market_depth(self, num_rows):
        from .functionality.market_depth import MarketDepthMixin
        parent = typing.cast(MarketDepthMixin, self._parent)
        parent.subscribe_market_depth(self, num_rows)

    def unsubscribe_market_depth(self):
        from .functionality.market_depth import MarketDepthMixin
        parent = typing.cast(MarketDepthMixin, self._parent)
        parent.unsubscribe_market_depth(self)

    def handle_market_depth(self, position: int, market_maker: str, operation: int, side: int, price: float,
                            size: int):
        depth_list = self.market_depth_bid if side else self.market_depth_ask

        if operation == 0:  # Insert
            depth_list.insert(position, MarketDepthEntry(price=price, size=size, market_maker=market_maker))
        elif operation == 1:  # Update
            depth_list[position] = MarketDepthEntry(price=price, size=size, market_maker=market_maker)
        else:  # Delete
            assert operation == 2
            del depth_list[position]
