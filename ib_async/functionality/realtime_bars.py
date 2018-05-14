import asyncio
import logging
import typing

from ib_async.bar import Bar, BarType
from ib_async.errors import UnsupportedFeature
from ib_async.instrument import Instrument
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface, OutgoingMessage, ProtocolVersion
from ib_async.utils import to_ib_date, to_ib_duration

LOG = logging.getLogger(__name__)

_bar_sizes = {
    0: '1 sec',
    5: '5 secs',
    15: '15 secs',
    30: '30 secs',
    1 * 60: '1 min',
    2 * 60: '2 mins',
    3 * 60: '3 mins',
    5 * 60: '5 mins',
    15 * 60: '15 mins',
    30 * 60: '30 mins',
    3600: '1 hour',
    86400: '1 day',
}


class RealtimeBarsMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self._realtime_bar_instruments = {}  # type: typing.Dict[RequestId, Instrument]

    def subscribe_realtime_bars(self, instrument: Instrument, what_to_show=BarType.Midpoint,
                                regular_trading_hours=True) -> typing.Awaitable[None]:
        """Requests real time bars

        Currently, only 5 seconds bars are provided. This request is subject to the same pacing as any historical data
        request: no more than 60 API queries in more than 600 seconds. Real time bars subscriptions are also included
        in the calculation of the number of Level 1 market data subscriptions allowed in an account.
        """

        request_id, future = self.make_future()
        message = OutgoingMessage(Outgoing.REQ_REAL_TIME_BARS, 3, request_id)

        message.add(instrument,
                    1,  # bar size, currently ignored
                    what_to_show, regular_trading_hours,
                    None)  # realtime bars options, undocumented

        self.send(message)
        self._realtime_bar_instruments[request_id] = instrument
        instrument._realtime_bars_request_id = request_id
        return future

    def unsubscribe_realtime_bars(self, instrument):
        """Cancels Real Time Bars subscription."""
        if instrument._realtime_bars_request_id:
            self._realtime_bar_instruments.pop(instrument._realtime_bars_request_id, None)
            self.resolve_future(instrument._realtime_bars_request_id, None)
            message = OutgoingMessage(Outgoing.CANCEL_REAL_TIME_BARS, 3, instrument._realtime_bars_request_id)
            self.send(message)
            instrument._realtime_bars_request_id = None

    def get_historical_bars(self, instrument: Instrument,
                            end_date, duration, bar_size, what_to_show=BarType.Midpoint,
                            include_expired=True, regular_trading_hours=True
                            ) -> typing.Awaitable[typing.List[Bar]]:
        """Requests contracts' historical data.

        When requesting historical data, a finishing time and date is required along with a duration string. For
        example, having `get_historical_bars(..., end_date="20130701 23:59:59 GMT", duration="3 D")` will return three
        days of data counting backwards from July 1st 2013 at 23:59:59 GMT resulting in all the available bars of the
        last three days until the date and time specified."""

        end_date = to_ib_date(end_date)
        duration = to_ib_duration(duration)
        bar_size = _bar_sizes.get(bar_size, bar_size)

        request_id, future = self.make_future()
        message = OutgoingMessage(Outgoing.REQ_HISTORICAL_DATA, protocol_version=self.version)
        message.add(6, max_version=ProtocolVersion.SYNT_REALTIME_BARS)
        message.add(request_id)

        message.add(instrument,
                    include_expired,
                    end_date,
                    bar_size,
                    duration,
                    regular_trading_hours,
                    what_to_show,
                    2)  # format date. We'd like unix timestamps

        if instrument.security_type == 'BAG':
            raise UnsupportedFeature("BAG contracts")

        message.add(False, min_version=ProtocolVersion.SYNT_REALTIME_BARS)  # keepUpToDate
        message.add(None)  # realtime bars options, undocumented

        self.send(message)

        def _cancel_if_cancelled(fut: asyncio.Future):
            if fut.cancelled():
                self.send_message(Outgoing.CANCEL_HISTORICAL_DATA, 1, request_id)

        future.add_done_callback(_cancel_if_cancelled)
        return future

    def _handle_real_time_bars(self, request_id: RequestId, bar: Bar):
        self.resolve_future(request_id, None)
        instrument = self._realtime_bar_instruments.get(request_id)
        if instrument:
            instrument.handle_realtime_bar(bar)

    def _handle_historical_data(self, request_id: RequestId,
                                start_date: str, end_date: str,
                                bars: typing.List[Bar]):
        self.resolve_future(request_id, bars)
