import enum
from unittest import mock
import typing

import pytest

import ib_async.errors
from ib_async.protocol import IncomingMessage, Protocol, RequestId
from ib_async.messages import Incoming, Outgoing
from ib_async.protocol_versions import ProtocolVersion


def test_message_no_version():
    msg = IncomingMessage(["77", "1"], protocol_version=ProtocolVersion.MIN_CLIENT)
    assert msg.message_type == Incoming.SOFT_DOLLAR_TIERS
    assert msg.message_version == 0


def test_message_version():
    msg = IncomingMessage(["2", "10"], protocol_version=ProtocolVersion.MIN_CLIENT)
    assert msg.message_type == Incoming.TICK_SIZE
    assert msg.message_version == 10


def test_message_read():
    def mk_message_read(the_type, *raw):
        msg = IncomingMessage(["2", "10"] + list(raw), protocol_version=ProtocolVersion.MIN_CLIENT)
        result = msg.read(the_type)
        assert msg.is_eof
        return result

    assert mk_message_read(int, "2") == 2
    assert mk_message_read(RequestId, "2") == RequestId(2)
    assert mk_message_read(float, "2") == 2.0
    assert mk_message_read(int, "") is None
    assert mk_message_read(str, "2") == "2"
    assert mk_message_read(bool, "2") is True
    assert mk_message_read(bool, "0") is False
    assert mk_message_read(list, "2", 'A', 'B') == ['A', 'B']
    assert mk_message_read(typing.List[int], "2", '1', '2') == [1, 2]
    assert mk_message_read(dict, "2", 'A', 'B', 'B', 'C') == {'A': 'B', 'B': 'C'}
    assert mk_message_read(typing.Dict[str, int], "2", 'A', '1', 'B', '2') == {'A': 1, 'B': 2}

    class StrEnum(str, enum.Enum):
        T1 = "First entry"
        T2 = "Second entry"

    assert mk_message_read(StrEnum, "Second entry") == StrEnum.T2

    class IntEnum(enum.IntEnum):
        T1 = 1
        T2 = 2

    assert mk_message_read(IntEnum, "2") == IntEnum.T2

    class UnknownClass():
        pass

    with pytest.raises(ValueError):
        mk_message_read(UnknownClass, "something")


def test_message_invoke_handler():
    result = []
    received_message = None

    def handler(arg1: int, arg2: str, arg3: typing.Dict[int, int], msg: IncomingMessage):
        nonlocal received_message
        result.extend([arg1, arg2, arg3])
        received_message = msg

    msg = IncomingMessage(["2", "10", '42', 'foo', '1', '13', '17'], protocol_version=ProtocolVersion(110))
    msg.invoke_handler(handler)
    assert msg == received_message
    assert result == [42, 'foo', {13: 17}]


def test_message_versioned():
    msg = IncomingMessage(["2", 2, "test"], protocol_version=ProtocolVersion(112))

    msg.reset()
    assert msg.read(str) == "test"

    msg.reset()
    assert msg.read(str, min_message_version=2) == "test"
    msg.reset()
    assert msg.read(str, min_message_version=3) is None
    msg.reset()
    assert msg.read(str, max_message_version=3) == "test"
    msg.reset()
    assert msg.read(str, max_message_version=2) is None

    msg.reset()
    assert msg.read(str, min_version=ProtocolVersion(112)) == "test"
    msg.reset()
    assert msg.read(str, min_version=ProtocolVersion(113)) is None
    msg.reset()
    assert msg.read(str, max_version=ProtocolVersion(113)) == "test"
    msg.reset()
    assert msg.read(str, max_version=ProtocolVersion(112)) is None


def test_protocol_serialize():
    prot = Protocol()
    assert prot.serialize("") == b''
    assert prot.serialize(1) == b'1'
    assert prot.serialize(1.01) == b'1.01'
    assert prot.serialize(True) == b'1'
    assert prot.serialize(False) == b'0'
    assert prot.serialize([""]) == b'1\0'
    assert prot.serialize({'a': 1}) == b'1\0a\x001'
    assert prot.serialize(ProtocolVersion(112)) == b'112'
    assert prot.serialize(None) == b''

    class UnknownClass():
        pass

    with pytest.raises(ValueError):
        prot.serialize(UnknownClass())


def test_protocol_futures():
    prot = Protocol()
    r_id, fut = prot.make_future()
    prot.resolve_future(r_id, "Test")
    assert fut.result() == "Test"


def test_protocol_futures_error(caplog):
    prot = Protocol()
    r_id, fut = prot.make_future()
    prot._handle_err_msg(r_id, 404, "Not found")
    ex = fut.exception()
    assert ex.error_code == 404
    assert ex.error_message == "Not found"

    assert caplog.records == []

    prot._handle_err_msg(r_id, 404, "Not found")
    assert len(caplog.records) == 1
    assert caplog.records[0].message == 'Received error#404 from TWS: Not found'


def test_protocol_send_message():
    prot = Protocol()
    prot.writer = mock.MagicMock()
    prot.writer.write = mock.MagicMock()

    prot.send_message(Outgoing.REQ_CONTRACT_DATA, 1, "foo", [42])
    prot.writer.write.assert_called_once_with(b'\x00\x00\x00\r'
                                              b'9\x00'
                                              b'1\x00'
                                              b'foo\x00'
                                              b'1\x0042\x00')


def test_protocol_check_feature():
    prot = Protocol()
    with pytest.raises(ib_async.errors.NotConnectedError) as e:
        prot.check_feature(ProtocolVersion(115), "not yet connected")

    prot.version = ProtocolVersion(110)

    prot.check_feature(ProtocolVersion(105), "105 feature")

    with pytest.raises(ib_async.errors.OutdatedServerError) as e:
        prot.check_feature(ProtocolVersion(115), "115 feature")

    assert e.value.error_code == 502
    assert str(e.value) == "The TWS is out of date and must be upgraded. It does not support 115 feature."

    with pytest.raises(ib_async.errors.OutdatedServerError) as e:
        prot.check_feature(ProtocolVersion(115))

    assert e.value.error_code == 502
    assert str(e.value) == "The TWS is out of date and must be upgraded."


def test_protocol_check_dispatch(caplog):
    protocol = Protocol()
    is_called_arg = None

    def mocked(arg: int):
        nonlocal is_called_arg
        is_called_arg = arg

    protocol._handle_tick_size = mocked
    protocol.dispatch_message(["2", "10", "42"])

    assert is_called_arg == 42

    assert caplog.records == []

    with caplog.at_level('DEBUG'):

        del protocol._handle_tick_size
        protocol.dispatch_message(["2", "10", "42"])
        assert len(caplog.records) == 1
        assert caplog.records[0].message == 'no handler for Incoming.TICK_SIZE v10'


def test_protocol_check_dispatch_versioned():
    protocol = Protocol()
    is_called_arg = None

    def mocked(arg: int):
        nonlocal is_called_arg
        is_called_arg = arg

    protocol._handle_tick_size_v10 = mocked
    protocol.dispatch_message(["2", "10", "42"])

    assert is_called_arg == 42
