import logging
import typing

from ib_async.errors import UnsupportedFeature
from ib_async.instrument import Instrument
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface, OutgoingMessage
from ib_async.protocol_versions import ProtocolVersion
from ib_async.tick_types import TickTypeGroup, MarketDataTimeliness, TickType, TickAttributes

LOG = logging.getLogger(__name__)


class MarketDataMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self.__instruments = {}

    def change_market_data_timeliness(self, timeliness: MarketDataTimeliness):
        """Switches market data timeliness.

        The API can receive frozen market data from Trader Workstation. Frozen market data is the last data recorded
        in our system. During normal trading hours, the API receives real-time market data. Invoking this function
        with argument 2 requests a switch to frozen data immediately or after the close. When the market reopens the
        next data the market data type will automatically switch back to real time if available."""
        self.send_message(Outgoing.REQ_MARKET_DATA_TYPE, 1, timeliness)

    def _handle_market_data_type(self, request_id: RequestId, timeliness: MarketDataTimeliness):
        instrument = self.__instruments[request_id]
        instrument.market_data_timeliness = timeliness

    def get_market_data(self, instrument: Instrument,
                        tick_types: typing.Iterable[TickTypeGroup] = (),
                        snapshot=False, regulatory_snapshot=False,
                        market_data_options: typing.Dict[str, str] = None) -> typing.Awaitable[None]:

        if instrument._market_data_request_id:
            raise ValueError('instrument has already been subscribed for market')

        if regulatory_snapshot:
            self.check_feature(ProtocolVersion.REQ_SMART_COMPONENTS, "regulatory snapshots")

        request_id, future = self.make_future()
        message = OutgoingMessage(Outgoing.REQ_MKT_DATA, version=11, request_id=request_id,
                                  protocol_version=self.version)
        message.add(instrument)

        if instrument.security_type == 'BAG':
            raise UnsupportedFeature("BAG orders")  # We're currently missing serialization for BAG

        if instrument.underlying_component:
            message.add(True, instrument.underlying_component)
        else:
            message.add(False)

        # convert to integers using getattr with default. This way the en user can provide integers instead of
        # GenericTickType values.
        tick_type_ids = (getattr(tick_type, "value", tick_type) for tick_type in tick_types)

        message.add(','.join(str(tick_type) for tick_type in tick_type_ids))
        message.add(snapshot)

        message.add(regulatory_snapshot, min_version=ProtocolVersion.REQ_SMART_COMPONENTS)
        message.add(market_data_options)

        self.send(message)

        self.__instruments[request_id] = instrument

        if not snapshot:
            instrument._market_data_request_id = request_id
            # subscriptions are complete as soon as the request is sent.
            self.resolve_future(request_id, instrument)

        return future

    def cancel_market_data(self, instrument: Instrument):
        """Cancels a RT Market Data request."""
        message = OutgoingMessage(Outgoing.CANCEL_MKT_DATA, version=2, request_id=instrument._market_data_request_id)
        self.send(message)
        instrument._market_data_request_id = None

    def _handle_tick_price(self, request_id: RequestId, tick_type: TickType, price: float, size: float,
                           attributes: int):
        instrument = self.__instruments[request_id]
        instrument.tick(tick_type, price, size, TickAttributes.list_from_int(attributes))

    def _handle_tick_generic(self, request_id: RequestId, tick_type: TickType, value: float):
        instrument = self.__instruments[request_id]
        instrument.tick(tick_type, value)

    def _handle_tick_size(self, request_id: RequestId, tick_type: TickType, value: int):
        instrument = self.__instruments[request_id]
        instrument.tick(tick_type, value)

    def _handle_tick_string(self, request_id: RequestId, tick_type: TickType, value: str):
        instrument = self.__instruments[request_id]
        instrument.tick(tick_type, value)

    def _handle_tick_req_params(self, request_id: RequestId, min_tick: float, bbo_exchange: str,
                                snapshot_permissions: int):
        instrument = self.__instruments[request_id]

        instrument.minimum_tick = min_tick
        instrument.bbo_exchange = bbo_exchange
        instrument.snapshot_permissions = snapshot_permissions

    def _handle_tick_snapshot_end(self, request_id: RequestId):
        instrument = self.__instruments.pop(request_id)
        self.resolve_future(request_id, instrument)
