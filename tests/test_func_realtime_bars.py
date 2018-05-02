import unittest.mock

from ib_async.functionality.realtime_bars import RealtimeBarsMixin
from ib_async.protocol import Outgoing, Incoming
from .utils import FunctionalityTestHelper


class FixtureMatchingSymbolsMixin(RealtimeBarsMixin, FunctionalityTestHelper):
    pass


def test_subscribe():
    t = FixtureMatchingSymbolsMixin()
    instrument = t.test_instrument

    instrument.subscribe_realtime_bars()
    t.assert_one_message_sent(Outgoing.REQ_REAL_TIME_BARS, 3, 43, 172604153, 'LLOY', 'STK', partial_match=True)

    instrument.handle_realtime_bar = unittest.mock.MagicMock()

    t.fake_incoming(Incoming.REAL_TIME_BARS, 2, 43, 1525245478, 4.0, 5.0, 6.0, 7.0, 10, 5.5, 1)
    instrument.handle_realtime_bar.assert_called_once_with(1525245478, 4.0, 5.0, 6.0, 7.0, 10, 5.5, 1)
    instrument.handle_realtime_bar.reset_mock()

    instrument.unsubscribe_realtime_bars()
    t.assert_one_message_sent(Outgoing.CANCEL_REAL_TIME_BARS, 3, 43)

    t.fake_incoming(Incoming.REAL_TIME_BARS, 2, 43, 1525245478, 4.0, 5.0, 6.0, 7.0, 10, 5.5, 1)
    instrument.handle_realtime_bar.assert_not_called()

    instrument.unsubscribe_realtime_bars()
    assert len(t.sent) == 0
