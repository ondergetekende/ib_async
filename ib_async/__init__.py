from ib_async.functionality.current_time import CurrentTimeMixin
from ib_async.functionality.matching_symbols import MatchingSymbolsMixin
from ib_async.functionality.instrument_details import ContractDetailsMixin
from ib_async.functionality.market_data import MarketDataMixin
from ib_async.functionality.market_depth import MarketDepthMixin
from ib_async.functionality.realtime_bars import RealtimeBarsMixin
from ib_async.functionality.tickbytick import TickByTickMixin
from ib_async.functionality.position import PositionMixin
from ib_async.functionality.orders import OrdersMixin

from ib_async.protocol import Protocol
from ib_async.instrument import Instrument, SecurityIdentifierType, SecurityType
from ib_async.tick_types import TickType, TickTypeGroup, MarketDataTimeliness


class IBClient(CurrentTimeMixin, MatchingSymbolsMixin, ContractDetailsMixin, MarketDataMixin, RealtimeBarsMixin,
               MarketDepthMixin, TickByTickMixin, PositionMixin, OrdersMixin,
               Protocol):
    # All of the functionality is delegated to the mixins and Protocol.
    pass


async def connect(hostname: str, port: int, client_id: int):
    client = IBClient()
    client.connect(hostname, port, client_id)


__all__ = [
    "IBClient", "connect",
    "Instrument", "SecurityIdentifierType", "SecurityType",
    "TickType", "TickTypeGroup", "MarketDataTimeliness"
]
