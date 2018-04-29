
from ib_async.functionality.matching_symbols import MatchingSymbolsMixin
from ib_async.instrument import Instrument, SecurityType
from .utils import FunctionalityTestHelper


class FixtureMatchingSymbolsMixin(MatchingSymbolsMixin, FunctionalityTestHelper):
    pass


def test_single_no_result():
    t = FixtureMatchingSymbolsMixin()

    fut = t.matching_symbols('AAPL')
    assert not fut.done()

    t.dispatch_message(['79', '43', '0'])
    assert fut.done()
    assert fut.result() == []


def test_single_one_result():
    t = FixtureMatchingSymbolsMixin()

    fut = t.matching_symbols('AAPL')
    assert not fut.done()

    t.dispatch_message(['79', '43', '1',
                        '42', 'AAPL', 'STK', 'NASDAQ', 'USD', ''])
    assert fut.done()
    assert len(fut.result()) == 1

    instrument: Instrument = fut.result()[0]
    assert instrument.contract_id == 42
    assert instrument.symbol == 'AAPL'
    assert instrument.security_type == SecurityType.Stock
    assert instrument.primary_exchange == 'NASDAQ'
    assert instrument.currency == 'USD'
