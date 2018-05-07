import logging
import typing  # noqa

from ib_async.instrument import Instrument
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface, IncomingMessage, ProtocolVersion
from ib_async.tick_types import LastTick, BidAskTick, MidpointTick

LOG = logging.getLogger(__name__)


class TickByTickMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self.__instruments = {}  # type: typing.Dict[RequestId, typing.Tuple[str, Instrument]]

    def __get_request_id(self, instrument: Instrument, tick_type: str):
        entry = tick_type.lower(), instrument
        for l_request_id, l_entry in self.__instruments.items():
            if l_entry == entry:
                return l_request_id

    def subscribe_tick_by_tick(self, instrument: Instrument, tick_type: str) -> None:
        self.check_feature(ProtocolVersion.TICK_BY_TICK, 'tick by tick data')

        request_id = self.__get_request_id(instrument, tick_type) or self.make_request_id()
        self.__instruments[request_id] = tick_type.lower(), instrument
        self.send_message(Outgoing.REQ_TICK_BY_TICK_DATA, request_id, instrument, tick_type)

    def unsubscribe_tick_by_tick(self, instrument: Instrument, tick_type: str) -> None:
        request_id = self.__get_request_id(instrument, tick_type)

        if request_id:
            del self.__instruments[request_id]
            self.send_message(Outgoing.CANCEL_TICK_BY_TICK_DATA, request_id)

    def _handle_tick_by_tick(self, request_id: RequestId, tick_type: int, time: int, msg: IncomingMessage):
        entry = self.__instruments.get(request_id)
        if not entry:
            return

        instrument = entry[1]

        if tick_type in (1, 2):
            price = msg.read(float)
            size = msg.read(int)
            attributes = msg.read(int)
            past_limit = bool(attributes & 0x01)
            unreported = bool(attributes & 0x02)

            exchange = msg.read(str)
            special_conditions = msg.read(str)

            tick = LastTick(time, price, size, past_limit, unreported, exchange, special_conditions)
            if tick_type == 1:
                instrument.on_tick_by_tick_last(tick)
            else:
                instrument.on_tick_by_tick_all(tick)
        elif tick_type == 3:
            bid_price = msg.read(float)
            ask_price = msg.read(float)
            bid_size = msg.read(int)
            ask_size = msg.read(int)
            attributes = msg.read(int)

            bid_past_low = bool(attributes & 0x01)
            ask_past_high = bool(attributes & 0x02)

            bidask_tick = BidAskTick(time, bid_price, ask_price, bid_size, ask_size, bid_past_low, ask_past_high)
            instrument.on_tick_by_tick_bidask(bidask_tick)
        else:
            assert tick_type == 4
            mid_point = msg.read(float)
            instrument.on_tick_by_tick_midpoint(MidpointTick(time, mid_point))
