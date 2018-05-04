from ib_async.functionality.market_depth import MarketDepthMixin
from ib_async.messages import Incoming, Outgoing

from .utils import FunctionalityTestHelper


class MixinFixture(MarketDepthMixin, FunctionalityTestHelper):
    pass


def test_subscribe():
    t = MixinFixture()
    instrument = t.test_instrument

    call_count = 0

    def handler(p):
        nonlocal call_count
        call_count += 1

    # Adding a handler should trigger a subscription
    instrument.market_depth_rows = 100
    instrument.on_market_depth += handler
    t.assert_one_message_sent(Outgoing.REQ_MKT_DEPTH, 5, 43, '172604153', 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'CHF', 'LLOY', 'LLOY', 100, 0)

    # Changing params should trigger a resubscription
    instrument.market_depth_rows = 40
    t.assert_one_message_sent(Outgoing.REQ_MKT_DEPTH, 5, 43, '172604153', 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'CHF', 'LLOY', 'LLOY', 40, 0)

    # Incoming data insert
    t.fake_incoming(Incoming.MARKET_DEPTH, 0, 43, 0, 0, 0, 20, 21)
    t.fake_incoming(Incoming.MARKET_DEPTH_L2, 0, 43, 0, "ne", 0, 1, 21, 21)
    assert len(instrument.market_depth_bid) == 1
    assert len(instrument.market_depth_ask) == 1
    assert instrument.market_depth_ask[0].price == 20
    assert call_count == 2

    # Incoming data update
    t.fake_incoming(Incoming.MARKET_DEPTH, 0, 43, 0, 1, 0, 22, 21)
    assert len(instrument.market_depth_ask) == 1
    assert instrument.market_depth_ask[0].price == 22
    assert call_count == 3

    # Incoming data delete
    t.fake_incoming(Incoming.MARKET_DEPTH, 0, 43, 0, 2, 0, 22, 21)
    assert len(instrument.market_depth_ask) == 0
    assert call_count == 4

    # Unsubscribe
    instrument.on_market_depth -= handler
    t.assert_one_message_sent(Outgoing.CANCEL_MKT_DEPTH, 0, 43)
