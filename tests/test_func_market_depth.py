from ib_async.functionality.market_depth import MarketDepthMixin
from ib_async.messages import Incoming, Outgoing

from .utils import FunctionalityTestHelper


class MixinFixture(MarketDepthMixin, FunctionalityTestHelper):
    pass


def test_subscribe():
    t = MixinFixture()
    instrument = t.test_instrument

    # Initial subscription
    instrument.subscribe_market_depth(100)
    t.assert_one_message_sent(Outgoing.REQ_MKT_DEPTH, 5, 43, '172604153', 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'CHF', 'LLOY', 'LLOY', 100, 0)

    # Change parameter, or a resubscribe
    instrument.subscribe_market_depth(150)
    t.assert_one_message_sent(Outgoing.REQ_MKT_DEPTH, 5, 43, '172604153', 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'CHF', 'LLOY', 'LLOY', 150, 0)

    # Incoming data insert
    t.fake_incoming(Incoming.MARKET_DEPTH, 0, 43, 0, 0, 0, 20, 21)
    t.fake_incoming(Incoming.MARKET_DEPTH_L2, 0, 43, 0, "ne", 0, 1, 21, 21)
    assert len(instrument.market_depth_bid) == 1
    assert len(instrument.market_depth_ask) == 1
    assert instrument.market_depth_ask[0].price == 20

    # Incoming data update
    t.fake_incoming(Incoming.MARKET_DEPTH, 0, 43, 0, 1, 0, 22, 21)
    assert len(instrument.market_depth_ask) == 1
    assert instrument.market_depth_ask[0].price == 22

    # Incoming data delete
    t.fake_incoming(Incoming.MARKET_DEPTH, 0, 43, 0, 2, 0, 22, 21)
    assert len(instrument.market_depth_ask) == 0

    # Unsubscribe
    instrument.unsubscribe_market_depth()
    t.assert_one_message_sent(Outgoing.CANCEL_MKT_DEPTH, 0, 43)

    # Repeated unsubscribe
    instrument.unsubscribe_market_depth()
    assert len(t.sent) == 0
