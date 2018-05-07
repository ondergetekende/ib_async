from ib_async.functionality.position import PositionMixin
from ib_async.protocol import Outgoing, Incoming
from .utils import FunctionalityTestHelper, run_event_loop


class MixinFixture(PositionMixin, FunctionalityTestHelper):
    pass


def test_subscribe():
    client = MixinFixture()

    fut = client.get_positions()
    client.assert_one_message_sent(Outgoing.REQ_POSITIONS, 1)
    client.fake_incoming(Incoming.POSITION_DATA, 3, 'DU123456', 289239602, 'DAX', 'FUT', '20180615', 0.0, '', 5, '',
                         'EUR', 'FDXM SEP 18', 'FDXM', '1', 2234.0)

    assert not fut.done()
    client.fake_incoming(Incoming.POSITION_END, 1)
    assert fut.done()
    run_event_loop()
    client.assert_one_message_sent(Outgoing.CANCEL_POSITIONS, 1)

    assert len(client.accounts['DU123456'].positions) == 1
    assert list(client.accounts['DU123456'].positions.values()) == [1.0]


def test_subscribe_event():
    client = MixinFixture()

    pos_seen = []

    def handle(pos):
        pos_seen.append(pos)

    client.on_position += handle
    client.assert_one_message_sent(Outgoing.REQ_POSITIONS, 1)

    fut = client.get_positions()
    assert client.sent == []

    client.fake_incoming(Incoming.POSITION_DATA, 1, 'DU123456', 289239602, 'DAX', 'FUT', '20180615', 0.0, '', 5, '',
                         'EUR', 'FDXM SEP 18', '1')

    assert not fut.done()
    client.fake_incoming(Incoming.POSITION_END, 1)
    assert fut.done()
    run_event_loop()
    assert client.sent == []

    assert len(client.accounts['DU123456'].positions) == 1
    assert list(client.accounts['DU123456'].positions.values()) == [1.0]

    assert len(pos_seen) == 1
    assert pos_seen[0].account.account_id == 'DU123456'
    assert pos_seen[0].instrument in client.accounts['DU123456'].positions
