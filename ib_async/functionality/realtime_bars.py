import enum
import logging
import typing

from ib_async.instrument import Instrument
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface, OutgoingMessage

LOG = logging.getLogger(__name__)


class BarType(enum.Enum):
    Trades = "TRADES"
    Midpoint = "MIDPOINT"
    Bid = "BID"
    Ask = "ASK"


class RealtimeBarsMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self._realtime_bar_instruments = {}  # type: typing.Dict[RequestId, Instrument]

    def subscribe_realtime_bars(self, instrument: Instrument, what_to_show=BarType.Midpoint,
                                regular_trading_hours=True) -> typing.Awaitable[None]:
        request_id, future = self.make_future()
        message = OutgoingMessage(Outgoing.REQ_REAL_TIME_BARS, 3, request_id)

        message.add(instrument.contract_id, instrument.symbol, instrument.security_type,
                    instrument.contract_month or instrument.last_trade_date,
                    instrument.strike, instrument.right, instrument.multiplier,
                    instrument.exchange, instrument.primary_exchange,
                    instrument.currency, instrument.local_symbol,
                    instrument.trading_class)

        message.add(1,  # bar size, currently ignored
                    what_to_show, regular_trading_hours,
                    None)  # realtime bars options, undocumented

        self.send(message)
        self._realtime_bar_instruments[request_id] = instrument
        instrument._realtime_bars_request_id = request_id
        return future

    def unsubscribe_realtime_bars(self, instrument):
        if instrument._realtime_bars_request_id:
            self._realtime_bar_instruments.pop(instrument._realtime_bars_request_id, None)
            self.resolve_future(instrument._realtime_bars_request_id, None)
            message = OutgoingMessage(Outgoing.CANCEL_REAL_TIME_BARS, 3, instrument._realtime_bars_request_id)
            self.send(message)
            instrument._realtime_bars_request_id = None

    def _handle_real_time_bars(self, request_id: RequestId,
                               time: int, open: float, high: float, low: float, close: float,
                               volume: int, average: float, count: int):
        self.resolve_future(request_id, None)
        instrument = self._realtime_bar_instruments.get(request_id)
        if instrument:
            instrument.handle_realtime_bar(time, open, high, low, close, volume, average, count)
