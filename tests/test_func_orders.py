import pytest

from ib_async.errors import ApiException
from ib_async.functionality.orders import OrdersMixin, Action
from ib_async.protocol import Incoming, ProtocolVersion
from .utils import FunctionalityTestHelper


class MixinFixture(OrdersMixin, FunctionalityTestHelper):
    pass


def test_mk_limit():
    client = MixinFixture()
    client.version = ProtocolVersion.MAX_CLIENT

    instrument = client.test_instrument

    # Place the order
    fut = client.create_limit_order(instrument, -1, 100, place=False)
    assert not client.sent
    assert fut.result().total_quantity == 1

    fut = client.create_limit_order(instrument, 1, 100, action=Action.Sell)
    client.assert_one_message_sent(3, 45, 1, 172604153, "LLOY", "STK", "", 0.0, "", "", "SMART", "EBS", "CHF",
                                   "LLOY", "LLOY", "ISIN", "GB0008706128", "SELL", 1, "LMT", 100, "", "GTC", "", "",
                                   "O", 0, "", 1, 0, 0, 0, 0, 0, 0, 0, "", 0.0, "", "", "", "", "", "", "", 0, "", -1,
                                   0, "", "", 0, "", "", 1, 1, "", 0, "", "", "", "", "", 0, "",

                                   "", "", "", 0, "", "",
                                   "", "", "", "", "", "", "", "", 0, "", "", 0, 0, "", "", 0, "", 0, 0, 0, 0, "",
                                   "1.7976931348623157e+308", "1.7976931348623157e+308", "1.7976931348623157e+308",
                                   "1.7976931348623157e+308", "1.7976931348623157e+308", 0, "", "", "",
                                   "1.7976931348623157e+308", "", "", "", "")
    assert not fut.done()

    # IB would first report this as an open order
    client.fake_incoming(Incoming.OPEN_ORDER, 34, 1, 265598, 'AAPL', 'STK', '', 0, '?', '', 'SMART', 'USD',
                         'AAPL', 'NMS', 'SELL', 1, 'LMT', '183.0', '0.0', 'GTC', '', 'DU228241', 'O', 0, '', 1,
                         176952797, 0, 0, 0, '', '176952797.0/DU228241/100', '', '', '', '', '', '', '', '', '',
                         0, '', '-1', 0, '', '', '', '', '', '', 0, 0, 0, '', 3, 1, 1, '', 0, 0, '',
                         0, 'None', '', 0, '', '', '', '?', 0, 0, '', 0, 0, '', '', '', '', '', 0, 0,
                         0, '', '', '', '', 0, '', 'IB', 0, 0, '', 0, 0, 'Submitted',
                         '1.7976931348623157E308', '1.7976931348623157E308', '1.7976931348623157E308', '', '', '', '',
                         '', 0, 0, 0, 'None', '1.7976931348623157E308', '184.0', '1.7976931348623157E308',
                         '1.7976931348623157E308', '1.7976931348623157E308', '1.7976931348623157E308', 0, '', '', '',
                         '1.7976931348623157E308')

    assert fut.done()
    order = fut.result()
    assert order.action == Action.Sell
    assert order.instrument.symbol == 'AAPL'

    # And then it would update the status
    client.fake_incoming(Incoming.ORDER_STATUS, 1, 'Submitted', 0, 1, 0, 176952797, 0, 0, 1, '', 0)


def test_mk_market():
    client = MixinFixture()
    client.version = ProtocolVersion.MAX_CLIENT

    # Place the order
    fut = client.create_market_order(client.test_instrument, -1, place=False)
    assert not client.sent
    assert fut.result().total_quantity == 1
    assert fut.result().action == Action.Sell

    fut = client.create_market_order(client.test_instrument, 1, action=Action.Sell)
    assert not fut.done()
    client.assert_one_message_sent(3, 45, 1, 172604153, "LLOY", "STK", "", 0.0, "", "", "SMART", "EBS", "CHF",
                                   "LLOY", "LLOY", "ISIN", "GB0008706128", "SELL", 1, "MKT", "", "", "GTC", "", "",
                                   "O", 0, "", 1, 0, 0, 0, 0, 0, 0, 0, "", 0.0, "", "", "", "", "", "", "", 0, "", -1,
                                   0, "", "", 0, "", "", 1, 1, "", 0, "", "", "", "", "", 0, "",

                                   "", "", "", 0, "", "",
                                   "", "", "", "", "", "", "", "", 0, "", "", 0, 0, "", "", 0, "", 0, 0, 0, 0, "",
                                   "1.7976931348623157e+308", "1.7976931348623157e+308", "1.7976931348623157e+308",
                                   "1.7976931348623157e+308", "1.7976931348623157e+308", 0, "", "", "",
                                   "1.7976931348623157e+308", "", "", "", "")
    assert not fut.done()
    client.fake_incoming(Incoming.ORDER_STATUS, 1, 'Submitted', 0, 1, 0, 176952797, 0, 0, 1, '', 0)
    assert fut.done()

    assert fut.result().action == Action.Sell


def test_mk_error():
    client = MixinFixture()
    client.version = ProtocolVersion.MAX_CLIENT

    # Place the order
    fut = client.create_market_order(client.test_instrument, -1, place=False)
    assert not client.sent
    assert fut.result().total_quantity == 1
    assert fut.result().action == Action.Sell

    fut = client.create_market_order(client.test_instrument, 1, action=Action.Sell)
    assert not fut.done()
    # post error unrelated to open order
    client.fake_incoming(Incoming.ERR_MSG, 1, 44, -10, "Something went wrong")
    assert not fut.done()

    # post error related to open order
    client.fake_incoming(Incoming.ERR_MSG, 1, 1, -10, "Something went wrong")
    assert fut.done()

    with pytest.raises(ApiException) as e:
        fut.result()
    assert e.value.error_code == -10


def test_next_valid_id():
    client = MixinFixture()
    client.version = ProtocolVersion.MAX_CLIENT

    client.fake_incoming(Incoming.NEXT_VALID_ID, 1, 9)

    assert client._next_order_id == 9


def test_get_orders_empty():
    client = MixinFixture()
    client.version = ProtocolVersion.MAX_CLIENT

    fut = client.get_open_orders()
    assert not fut.done()
    client.fake_incoming(Incoming.OPEN_ORDER_END, 1)
    assert fut.done()
    assert list(fut.result()) == []


def test_get_orders_1():
    client = MixinFixture()
    client.version = ProtocolVersion.MAX_CLIENT

    fut = client.get_open_orders()
    assert not fut.done()

    # IB would first report this as an open order
    client.fake_incoming(Incoming.OPEN_ORDER, 34, 1, 265598, 'AAPL', 'STK', '', 0, '?', '', 'SMART', 'USD',
                         'AAPL', 'NMS', 'BUY', 1, 'LMT', '183.0', '0.0', 'GTC', '', 'DU228241', 'O', 0, '', 1,
                         176952797, 0, 0, 0, '', '176952797.0/DU228241/100', '', '', '', '', '', '', '', '', '',
                         0, '', '-1', 0, '', '', '', '', '', '', 0, 0, 0, '', 3, 1, 1, '', 0, 0, '',
                         0, 'None', '', 0, '', '', '', '?', 0, 0, '', 0, 0, '', '', '', '', '', 0, 0,
                         0, '', '', '', '', 0, '', 'IB', 0, 0, '', 0, 0, 'Submitted',
                         '1.7976931348623157E308', '1.7976931348623157E308', '1.7976931348623157E308', '', '', '', '',
                         '', 0, 0, 0, 'None', '1.7976931348623157E308', '184.0', '1.7976931348623157E308',
                         '1.7976931348623157E308', '1.7976931348623157E308', '1.7976931348623157E308', 0, '', '', '',
                         '1.7976931348623157E308')
    assert not fut.done()
    client.fake_incoming(Incoming.OPEN_ORDER_END, 1)
    assert fut.done()
    assert len(fut.result()) == 1
