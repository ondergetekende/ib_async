import asyncio
import typing

import pytest

import ib_async.protocol
import ib_async.instrument


class FunctionalityTestHelper(ib_async.protocol.Protocol):
    """A helper to allow testing the mixins outside of network conditions."""

    def __init__(self):
        super().__init__()

        self.next_request_id = ib_async.protocol.RequestId(43)
        self.version = ib_async.protocol.ProtocolVersion(110)
        self.futures = {}
        self.sent = []  # type: typing.List[ib_async.protocol.OutgoingMessage]

    def send(self, message: ib_async.protocol.OutgoingMessage):
        self.sent.append(message)

    def fake_incoming(self, *fields):
        # use a fake outgoing message to serialize the arguments
        msg_fake = ib_async.protocol.OutgoingMessage(
            ib_async.protocol.Outgoing.CANCEL_MKT_DATA,
            *fields
        )

        msg_encoded = msg_fake.serialize()[4:].split(b'\x00')[1:-1]

        self.dispatch_message([f.decode() for f in msg_encoded])

    def dispatch_message(self, fields: typing.List[str]):
        message = ib_async.protocol.IncomingMessage(fields, source=self)

        msg_name = message.message_type.name.lower()
        # Find a general-purpose handler
        handler = (getattr(self, "_handle_%s" % msg_name, None) or
                   getattr(self, "_handle_%s_v%i" % (msg_name, message.message_version), None))

        message.invoke_handler(handler)

    def assert_message_sent(self, *arguments, partial_match=False):
        expected_msg = ib_async.protocol.OutgoingMessage(*arguments)

        assert self.sent, "Expected a message, but none were sent"

        for sent_message in self.sent:
            if sent_message.fields_encoded[0] == expected_msg.fields_encoded[0]:
                actual_msg = sent_message
                break
        else:
            actual_msg = self.sent[0]

        # Check for full match
        if actual_msg.fields_encoded == expected_msg.fields_encoded:
            return

        prefix_length = 0
        for f0, f1 in zip(expected_msg.fields_encoded, actual_msg.fields_encoded):
            if f0 != f1:
                break
            prefix_length += 1
        else:
            if partial_match:
                return
            elif len(expected_msg.fields_encoded) > len(actual_msg.fields_encoded):
                pytest.fail("Actual message had missing fields, missing %r" % (expected_msg.fields[prefix_length:]))
            else:
                pytest.fail("Actual message had extra fields" % (actual_msg.fields[prefix_length:]))

        pytest.fail("Messages did not match, from offset %i: expected: %s != %s" % (
            prefix_length,
            ",".join(repr(x) for x in expected_msg.fields[prefix_length:prefix_length + 7]),
            ",".join(repr(x) for x in actual_msg.fields[prefix_length:prefix_length + 7:])))

    def assert_one_message_sent(self, *arguments, partial_match=False):
        if len(self.sent) != 1:
            assert False, "Expected one message to be sent, actually saw %i" % len(self.sent)

        self.assert_message_sent(*arguments, partial_match=partial_match)
        # except AssertionError:
        #     msg = [f.decode() for f in self.sent[0].split(b'\x00')[:-1]]
        #     assert False, "Got %r" % ib_async.protocol.OutgoingMessage(int(msg[0]), *msg[1:],
        #                                                                protocol_version=self.version)

        self.sent = []

    @property
    def test_instrument(self):
        try:
            return self._test_instrument  # type: ignore  # noqa
        except AttributeError:
            pass

        instrument = self._test_instrument = ib_async.instrument.Instrument(self)

        instrument.symbol = 'LLOY'
        instrument.security_type = ib_async.instrument.SecurityType.Stock
        instrument.exchange = 'SMART'
        instrument.currency = 'CHF'
        instrument.local_symbol = 'LLOY'
        instrument.market_name = 'LLOY'
        instrument.trading_class = 'LLOY'
        instrument.contract_id = 172604153
        instrument.minimum_tick = 0.0001
        instrument.market_data_size_multiplier = '1'
        instrument.multiplier = ''
        instrument.order_types = ['ACTIVETIM', 'ADJUST', 'ALERT', 'ALGOLTH', 'ALLOC', 'AVGCOST', 'BASKET', 'COND',
                                  'CONDORDER', 'CONSCOST', 'DAY', 'DEACT', 'DEACTDIS', 'DEACTEOD', 'GAT', 'GTC', 'GTD',
                                  'GTT', 'HID', 'IOC', 'LIT', 'LMT', 'LOC', 'LTH', 'MIT', 'MKT', 'MOC', 'MTL',
                                  'NGCOMB', 'NONALGO', 'OCA', 'OPG', 'PEGBENCH', 'REL', 'SNAPMID', 'SNAPMKT',
                                  'SNAPREL', 'STP', 'STPLMT', 'TRAIL', 'TRAILLIT', 'TRAILLMT', 'TRAILMIT', 'WHATIF']
        instrument.valid_exchanges = ['SMART', 'EBS'],
        instrument.price_magnifier = 1
        instrument.underlying_contract_id = 0
        instrument.long_name = 'LLOYDS BANKING GROUP PLC'
        instrument.primary_exchange = 'EBS'
        instrument.contract_month = ''
        instrument.industry = 'Financial'
        instrument.category = 'Banks'
        instrument.subcategory = 'Diversified Banking Inst'
        instrument.time_zone = 'MET',
        instrument.trading_hours = '20180501:CLOSED;20180502:0900-20180502:1732;20180503:0900-20180503:1732'
        instrument.liquid_hours = '20180501:CLOSED;20180502:0900-20180502:1720;20180503:0900-20180503:1720'
        instrument.security_ids = {ib_async.instrument.SecurityIdentifierType.ISIN: 'GB0008706128'}
        instrument.aggregated_group = '6'
        instrument.market_rule_ids = '1874,1874'
        return instrument


def run_event_loop():
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))
