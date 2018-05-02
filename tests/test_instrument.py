import ib_async.protocol
import ib_async.instrument


def test_serialize_underlying_component():
    msg = ib_async.protocol.IncomingMessage(['10', '0',
                                             '5', '5.1', '2.1'],
                                            protocol_version=ib_async.protocol.ProtocolVersion.MIN_CLIENT)

    comp = msg.read(ib_async.instrument.UnderlyingComponent)
    assert comp.contract_id == 5
    assert comp.delta == 5.1
    assert comp.price == 2.1

    m = comp.serialize(ib_async.protocol.ProtocolVersion.MIN_CLIENT)
    assert m[0] == 5
    assert m[1] == 5.1
    assert m[2] == 2.1
