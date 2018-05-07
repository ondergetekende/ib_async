from ib_async.functionality.tickbytick import TickByTickMixin
from ib_async.protocol import Outgoing, Incoming, ProtocolVersion
from ib_async.tick_types import LastTick, BidAskTick, MidpointTick
from .utils import FunctionalityTestHelper


class Fixture(TickByTickMixin, FunctionalityTestHelper):
    pass


def test_subscribe():
    t = Fixture()
    t.version = ProtocolVersion.MAX_CLIENT
    instrument = t.test_instrument

    ticks_received = []

    def tick_hander(tick):
        ticks_received.append(tick)

    # adding a handler should trigger a subscription message
    instrument.on_tick_by_tick_last += tick_hander
    t.assert_one_message_sent(Outgoing.REQ_TICK_BY_TICK_DATA, 43, 172604153, 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'EBS', 'CHF', 'LLOY', 'LLOY', 'Last')
    instrument.on_tick_by_tick_all += tick_hander
    t.assert_one_message_sent(Outgoing.REQ_TICK_BY_TICK_DATA, 44, 172604153, 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'EBS', 'CHF', 'LLOY', 'LLOY', 'AllLast')
    instrument.on_tick_by_tick_bidask += tick_hander
    t.assert_one_message_sent(Outgoing.REQ_TICK_BY_TICK_DATA, 45, 172604153, 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'EBS', 'CHF', 'LLOY', 'LLOY', 'BidAsk')
    instrument.on_tick_by_tick_midpoint += tick_hander
    t.assert_one_message_sent(Outgoing.REQ_TICK_BY_TICK_DATA, 46, 172604153, 'LLOY', 'STK', '', 0.0, '', '',
                              'SMART', 'EBS', 'CHF', 'LLOY', 'LLOY', 'Midpoint')

    # Test if ticks actually arrive
    t.fake_incoming(Incoming.TICK_BY_TICK, 43, 1,
                    1525245478, 42, 13, 3, "NYSE", "")
    assert ticks_received[-1] == LastTick(1525245478, 42.0, 13, True, True, 'NYSE', '')

    t.fake_incoming(Incoming.TICK_BY_TICK, 44, 2,
                    1525245479, 43, 13, 3, "NYSE", "")
    assert ticks_received[-1] == LastTick(1525245479, 43.0, 13, True, True, 'NYSE', '')

    t.fake_incoming(Incoming.TICK_BY_TICK, 45, 3,
                    1525245478, 44, 44, 13, 13, 0)
    assert ticks_received[-1] == BidAskTick(1525245478, 44.0, 44.0, 13, 13, False, False)

    t.fake_incoming(Incoming.TICK_BY_TICK, 46, 4,
                    1525245478, 45, 13, 3, "NYSE", "")
    assert ticks_received[-1] == MidpointTick(1525245478, 45.0)

    assert len(ticks_received) == 4

    # adding a handler should trigger a subscription message
    instrument.on_tick_by_tick_last -= tick_hander
    t.assert_one_message_sent(Outgoing.CANCEL_TICK_BY_TICK_DATA, 43)
    instrument.on_tick_by_tick_all -= tick_hander
    t.assert_one_message_sent(Outgoing.CANCEL_TICK_BY_TICK_DATA, 44)
    instrument.on_tick_by_tick_bidask -= tick_hander
    t.assert_one_message_sent(Outgoing.CANCEL_TICK_BY_TICK_DATA, 45)
    instrument.on_tick_by_tick_midpoint -= tick_hander
    t.assert_one_message_sent(Outgoing.CANCEL_TICK_BY_TICK_DATA, 46)
