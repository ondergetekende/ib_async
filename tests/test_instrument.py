from unittest.mock import MagicMock
import weakref

import ib_async.protocol
import ib_async.instrument
from .utils import FunctionalityTestHelper


def test_serialize_underlying_component():
    mock_protocol = MagicMock()
    mock_protocol.version = ib_async.protocol.ProtocolVersion.MIN_CLIENT

    msg = ib_async.protocol.IncomingMessage(['10', '0',
                                             '5', '5.1', '2.1'], mock_protocol)

    comp = msg.read(ib_async.instrument.UnderlyingComponent)
    assert comp.contract_id == 5
    assert comp.delta == 5.1
    assert comp.price == 2.1

    m = ib_async.protocol.OutgoingMessage(ib_async.protocol.Outgoing.PLACE_ORDER,
                                          protocol_version=ib_async.protocol.ProtocolVersion.MIN_CLIENT)

    comp.serialize(m)
    assert m.fields[1] == 5
    assert m.fields[2] == 5.1
    assert m.fields[3] == 2.1


def test_serialize_instrument():
    proto = FunctionalityTestHelper()

    message = ib_async.protocol.IncomingMessage([10, 0,
                                                 172604153, 'LLOY', 'STK', '', 0.0, '',
                                                 '', 'SMART', 'EBS', 'CHF', 'LLOY', 'LLOY'], proto)

    i1 = message.read(ib_async.instrument.Instrument)
    message.reset()
    i2 = message.read(ib_async.instrument.Instrument)

    message = ib_async.protocol.IncomingMessage([10, 0,
                                                 123456, 'LLOY', 'STK', '', 0.0, '',
                                                 '', 'SMART', 'EBS', 'CHF', 'LLOY', 'LLOY'], proto)
    i3 = message.read(ib_async.instrument.Instrument)

    assert i1 is i2  # Check that successive reads result in the same instrument
    assert i1 is not i3  # Check that different contract IDs produce distinct objects

    i3_ref = weakref.ref(i3)
    del i3, message
    assert not i3_ref()  # Check that the protocol does not hold a strong reference
