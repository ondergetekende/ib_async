from unittest.mock import MagicMock

from ib_async.instrument import Instrument
from ib_async.functionality.executions import ExecutionsMixin
from ib_async.functionality.orders import OrdersMixin
from ib_async.protocol import Incoming, Outgoing, ProtocolVersion

from .utils import FunctionalityTestHelper


class MixinFixture(OrdersMixin, ExecutionsMixin, FunctionalityTestHelper):
    pass


def test_get_executions():
    client = MixinFixture()
    client.version = ProtocolVersion.MIFID_EXECUTION
    client.on_execution = cli_exec = MagicMock()

    order_fut = client.create_market_order(client.test_instrument, 1)
    client.fake_incoming(Incoming.ORDER_STATUS, 1, 'Submitted', 0, 1, 0, 176952797, 0, 0, 1, '', 0)
    client.sent = []
    order = order_fut.result()
    order.on_execution = ord_exec = MagicMock()

    instrument = Instrument(client)
    instrument.contract_id = 265598
    instrument.on_execution = inst_exec = MagicMock()

    fut = client.get_executions()
    client.assert_one_message_sent(Outgoing.REQ_EXECUTIONS, 3, 43, 0, '', '', '', '', '', '')
    assert not fut.done()

    client.fake_incoming(Incoming.EXECUTION_DATA, 43, 1, 265598, 'AAPL', 'STK', '', '0.0', '', '', 'IBKRATS',
                         'USD', 'AAPL', 'NMS', '0001b25e.5af587e4.01.01', '20180511  19:17:00', 'DU226959', 'IBKRATS',
                         'BOT', 1, '188.46', 2037003807, 0, 0, 1, '188.46', '', '', '', '', 2)
    assert not fut.done()

    assert ord_exec .call_count == 1
    assert cli_exec.call_count == 1
    assert inst_exec.call_count == 1

    client.fake_incoming(Incoming.EXECUTION_DATA_END, 1, 43)
    assert fut.done()
    assert len(fut.result()) == 1
    assert fut.result()[0].instrument is instrument


def test_executions_unsolicited():
    client = MixinFixture()
    client.version = ProtocolVersion.MIFID_EXECUTION
    client.on_execution = cli_exec = MagicMock()

    client.fake_incoming(Incoming.EXECUTION_DATA, 43, 1, 265598, 'AAPL', 'STK', '', '0.0', '', '', 'IBKRATS',
                         'USD', 'AAPL', 'NMS', '0001b25e.5af587e4.01.01', '20180511  19:17:00', 'DU226959', 'IBKRATS',
                         'BOT', 1, '188.46', 2037003807, 0, 0, 1, '188.46', '', '', '', '', 2)

    assert cli_exec.call_count == 1
