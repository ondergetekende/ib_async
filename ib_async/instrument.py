import enum
import logging
import typing
import weakref

from ib_async import protocol, tick_types
from ib_async.bar import Bar, BarType
from ib_async.event import Event

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
        self._contract_id = 0
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

    @property
    def contract_id(self):
        return self._contract_id

    @contract_id.setter
    def contract_id(self, value):
        if value != self._contract_id:
            try:
                registry = self._parent.__instruments  # type: ignore
            except AttributeError:
                registry = self._parent.__instruments = weakref.WeakValueDictionary()  # type: ignore

            assert not registry.get(value)
            registry.pop(self._contract_id, None)
            registry[value] = self
            self._contract_id = value

    @classmethod
    def get_instance_from(cls, msg: protocol.IncomingMessage):
        try:
            registry = msg.source.__instruments  # type: ignore
        except AttributeError:
            registry = msg.source.__instruments = weakref.WeakValueDictionary()  # type: ignore

        contract_id = msg.peek(int)
        try:
            return registry[contract_id]
        except KeyError:
            pass

        result = cls(parent=msg.source)
        result.contract_id = contract_id
        return result

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
        # This is the most common (but not the only) way to serialize instruments.
        self.contract_id = message.read(int)
        self.symbol = message.read(str)
        self.security_type = message.read(str)
        self.last_trade_date = self.contract_month = message.read(str)
        self.strike = message.read(float)
        self.right = message.read(str)
        self.multiplier = message.read(int)
        self.exchange = message.read(str)
        self.primary_exchange = message.read(str)
        self.currency = message.read(str)
        self.local_symbol = message.read(str)
        self.trading_class = message.read(str)

    # ------ Equality ------

    def __hash__(self):
        return hash((self._parent, self._contract_id))

    def __eq__(self, other):
        return other._contract_id == self._contract_id and other._parent == self._parent

    # ------ Market data ------

    on_market_data = Event()  # type: Event[tick_types.TickType]
    _market_data_tick_types = ()  # type: typing.Sequence[tick_types.TickTypeGroup]

    @property
    def market_data_tick_types(self) -> typing.Sequence[tick_types.TickTypeGroup]:
        # Determines what market data to subscribe to.
        return self._market_data_tick_types

    @market_data_tick_types.setter
    def market_data_tick_types(self, value: typing.Iterable[typing.Union[tick_types.TickTypeGroup, int]]):
        self._market_data_tick_types = tuple(tick_types.TickTypeGroup(v) for v in value)

        if self.on_market_data.has_subscribers:
            self.on_market_data.on_subscribe()

    @on_market_data.on_subscribe
    def __on_market_data_sub(self):
        from .functionality.market_data import MarketDataMixin
        parent = typing.cast(MarketDataMixin, self._parent)
        parent.get_market_data(self, self._market_data_tick_types, snapshot=False, regulatory_snapshot=False)

    @on_market_data.on_unsubscribe
    def __on_market_data_unsub(self):
        from .functionality.market_data import MarketDataMixin
        parent = typing.cast(MarketDataMixin, self._parent)
        parent.cancel_market_data(self)

    def handle_market_data(self, tick_type: tick_types.TickType, value: typing.Any, size: float = None,
                           attributes: tick_types.TickAttributes = None):

        size_tick_type = None
        if size is not None:
            try:
                size_tick_type = _tick_type_size_lookup[tick_type]
            except KeyError:
                if size:
                    LOG.warning('received tick %s with size, but have no way to store it')
            else:
                self._tick_data[size_tick_type] = size

        self._tick_data[tick_type] = value
        if attributes is not None:
            self._tick_attributes[tick_type] = attributes

        self.on_market_data(tick_type)
        if size_tick_type:
            self.on_market_data(size_tick_type)

    def fetch_market_data(self, tick_types: typing.Iterable[tick_types.TickTypeGroup] = ()
                          ) -> typing.Awaitable[None]:
        """Retrieve a single snapshot of market data for this instrument."""
        from .functionality.market_data import MarketDataMixin
        parent = typing.cast(MarketDataMixin, self._parent)
        return parent.get_market_data(self, tick_types, snapshot=True, regulatory_snapshot=False)

    # ------ OHLCV Bars ------

    on_bar = Event()  # type: Event[Bar]

    @on_bar.on_subscribe
    def __on_bar_sub(self):
        from .functionality.realtime_bars import RealtimeBarsMixin
        parent = typing.cast(RealtimeBarsMixin, self._parent)
        parent.subscribe_realtime_bars(self)

    @on_bar.on_unsubscribe
    def __on_bar_unsub(self):
        from .functionality.realtime_bars import RealtimeBarsMixin
        parent = typing.cast(RealtimeBarsMixin, self._parent)
        parent.unsubscribe_realtime_bars(self)

    def handle_realtime_bar(self, bar: Bar):
        self.on_bar(bar)

    def get_historic_bars(self, end_date, duration, bar_size,
                          what_to_show=BarType.Midpoint) -> typing.Awaitable[typing.List[Bar]]:
        from .functionality.realtime_bars import RealtimeBarsMixin
        parent = typing.cast(RealtimeBarsMixin, self._parent)
        return parent.get_historical_bars(self, end_date, duration, bar_size=bar_size, what_to_show=what_to_show)

    # ------ Market depth ------

    on_market_depth = Event()  # type: Event[None]
    _market_depth_rows = 50

    @property
    def market_depth_rows(self) -> int:
        return self._market_depth_rows

    @market_depth_rows.setter
    def market_depth_rows(self, value: int):
        self._market_depth_rows = value
        if self.on_market_depth.has_subscribers:
            self.on_market_depth.on_subscribe()

    @on_market_depth.on_subscribe
    def __on_market_depth_sub(self):
        from .functionality.market_depth import MarketDepthMixin
        parent = typing.cast(MarketDepthMixin, self._parent)
        parent.subscribe_market_depth(self, self._market_depth_rows)

    @on_market_depth.on_unsubscribe
    def __on_market_depth__unsub(self):
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

        self.on_market_depth(None)

    # ------ Tick by Tick ------

    on_tick_by_tick_last = Event()  # type: Event[tick_types.LastTick]
    on_tick_by_tick_all = Event()  # type: Event[tick_types.LastTick]
    on_tick_by_tick_bidask = Event()  # type: Event[tick_types.BidAskTick]
    on_tick_by_tick_midpoint = Event()  # type: Event[tick_types.MidpointTick]

    @on_tick_by_tick_last.on_subscribe
    def __on_tick_by_tick_last__subscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.subscribe_tick_by_tick(self, 'Last')

    @on_tick_by_tick_last.on_unsubscribe
    def __on_tick_by_tick_last__unsubscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.unsubscribe_tick_by_tick(self, 'Last')

    @on_tick_by_tick_all.on_subscribe
    def __on_tick_by_tick_all__subscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.subscribe_tick_by_tick(self, 'AllLast')

    @on_tick_by_tick_all.on_unsubscribe
    def __on_tick_by_tick_all__unsubscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.unsubscribe_tick_by_tick(self, 'AllLast')

    @on_tick_by_tick_bidask.on_subscribe
    def __on_tick_by_tick_bidask__subscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.subscribe_tick_by_tick(self, 'BidAsk')

    @on_tick_by_tick_bidask.on_unsubscribe
    def __on_tick_by_tick_bidask__unsubscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.unsubscribe_tick_by_tick(self, 'BidAsk')

    @on_tick_by_tick_midpoint.on_subscribe
    def __on_tick_by_tick_midpoint__subscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.subscribe_tick_by_tick(self, 'Midpoint')

    @on_tick_by_tick_midpoint.on_unsubscribe
    def __on_tick_by_tick_midpoint__unsubscribe(self):
        from .functionality.tickbytick import TickByTickMixin
        parent = typing.cast(TickByTickMixin, self._parent)
        parent.unsubscribe_tick_by_tick(self, 'Midpoint')
