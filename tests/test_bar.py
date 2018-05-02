import ib_async.protocol
import ib_async.bar


def test_serialize_historic():
    msg = ib_async.protocol.IncomingMessage(['10', '0',
                                             '15000191', '10.0', '11.0', '9.0', '10.1', '5', '10.01', '1'],
                                            protocol_version=ib_async.protocol.ProtocolVersion.MAX_CLIENT)

    bar = msg.read(ib_async.bar.Bar)
    assert bar.open == 10.0
    assert bar.has_gaps == ''

    msg = ib_async.protocol.IncomingMessage(['10', '0',
                                             '15000191', '10.0', '11.0', '9.0', '10.1', '5', '10.01', 'yez', '1'],
                                            protocol_version=ib_async.protocol.ProtocolVersion.MIN_CLIENT)

    bar = msg.read(ib_async.bar.HistoricBar)
    assert bar.open == 10.0
    assert bar.has_gaps == 'yez'

    m = list(bar.serialize(ib_async.protocol.ProtocolVersion.MIN_CLIENT))
    assert m == [15000191, 10.0, 11.0, 9.0, 10.1, 5, 10.01, 'yez', 1]
    m = list(bar.serialize(ib_async.protocol.ProtocolVersion.MAX_CLIENT))
    assert m == [15000191, 10.0, 11.0, 9.0, 10.1, 5, 10.01, 1]
