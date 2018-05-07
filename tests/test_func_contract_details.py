from ib_async.functionality.instrument_details import ContractDetailsMixin
from ib_async.instrument import SecurityIdentifierType, Instrument

from .utils import FunctionalityTestHelper


class MixinFixture(ContractDetailsMixin, FunctionalityTestHelper):
    pass


def test_by_isin():
    t = MixinFixture()
    t.version = 110

    fut = t.get_instrument_by_id('US0378331005', SecurityIdentifierType.ISIN)
    assert not fut.done()
    t.assert_message_sent(9, 8, 43, 0, '', None, None, None, None, None, None, None, None, None, None, False,
                          'ISIN', 'US0378331005')

    t.dispatch_message(["10", "1", "43",  # CONTRACT_DATA
                        'AAPL', 'STK', '', 0.0, '', 'NYSE', 'USD', 'AAPL', 'NMS', 'NMS', 265598, 0.01, '100', '',
                        'ACTIVETIM,ADJUST,ALERT,ALLOC,AVGCOST,BASKET,COND,CONDORDER,DAY,DEACT,DEACTDIS,DEACTEOD,GAT',
                        'SMART,AMEX,NYSE,CBOE,ISE,CHX,ARCA,ISLAND,VWAP,DRCTEDGE,NSX,BEX,BATS,EDGEA,CSFBALGO,IEX,PSX',
                        1, 0, 'APPLE INC', 'NASDAQ', '', 'Technology', 'Computers', 'Computers', 'EST5EDT',
                        '20180507:0700-20180507:1600;20180508:0700-20180508:1600;20180610:CLOSED',
                        '20180507:0700-20180507:1600;20180508:0700-20180508:1600;20180512:CLOSED', '', '', {}, '1', '',
                        '', '26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', ''])
    assert not fut.done()

    t.dispatch_message(["52", "1", "43"]),  # CONTRACT_DATA_END
    assert fut.done()
    instrument = fut.result()
    assert instrument.symbol == 'AAPL'
    assert instrument.exchange == 'NYSE'


def test_by_local_symbol():
    t = MixinFixture()
    t.version = 110

    fut = t.get_instrument_by_local_symbol("AAPL", "NASDAQ")
    assert not fut.done()
    t.assert_message_sent(9, 8, 43, 0, '', 'STK', None, None, None, None, 'NASDAQ', None, None, 'AAPL', '', False,
                          None, None)

    t.dispatch_message(["10", "1", "43",  # CONTRACT_DATA
                        'AAPL', 'STK', '', 0.0, '', 'NYSE', 'USD', 'AAPL', 'NMS', 'NMS', 265598, 0.01, '100', '',
                        'ACTIVETIM,ADJUST,ALERT,ALLOC,AVGCOST,BASKET,COND,CONDORDER,DAY,DEACT,DEACTDIS,DEACTEOD,GAT',
                        'SMART,AMEX,NYSE,CBOE,ISE,CHX,ARCA,ISLAND,VWAP,DRCTEDGE,NSX,BEX,BATS,EDGEA,CSFBALGO,IEX,PSX',
                        1, 0, 'APPLE INC', 'NASDAQ', '', 'Technology', 'Computers', 'Computers', 'EST5EDT',
                        '20180507:0700-20180507:1600;20180508:0700-20180508:1600;20180610:CLOSED',
                        '20180507:0700-20180507:1600;20180508:0700-20180508:1600;20180512:CLOSED', '', '', {}, '1', '',
                        '', '26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', ''])
    assert not fut.done()
    t.dispatch_message(["52", "1", "43"])  # CONTRACT_DATA_END
    assert fut.done()
    instrument = fut.result()
    assert instrument.symbol == 'AAPL'
    assert instrument.exchange == 'NYSE'


def test_update_details():
    t = MixinFixture()
    t.version = 110

    instrument = Instrument(t)
    instrument.symbol = 'AAPL'
    instrument.security_ids = {SecurityIdentifierType.ISIN: 'US0378331005'}

    fut = t.refresh_instrument(instrument)
    assert not fut.done()
    t.assert_one_message_sent(9, 8, 43, 0, 'AAPL', '', '', 0.0, '', '', '', '', '', '', '', False,
                              'ISIN', 'US0378331005')

    t.dispatch_message(["10", "1", "43",  # CONTRACT_DATA
                        'AAPL', 'STK', '', 0.0, '', 'NYSE', 'USD', 'AAPL', 'NMS', 'NMS', 265598, 0.01, '100', '',
                        'ACTIVETIM,ADJUST,ALERT,ALLOC,AVGCOST,BASKET,COND,CONDORDER,DAY,DEACT,DEACTDIS,DEACTEOD,GAT',
                        'SMART,AMEX,NYSE,CBOE,ISE,CHX,ARCA,ISLAND,VWAP,DRCTEDGE,NSX,BEX,BATS,EDGEA,CSFBALGO,IEX,PSX',
                        1, 0, 'APPLE INC', 'NASDAQ', '', 'Technology', 'Computers', 'Computers', 'EST5EDT',
                        '20180507:0700-20180507:1600;20180508:0700-20180508:1600;20180610:CLOSED',
                        '20180507:0700-20180507:1600;20180508:0700-20180508:1600;20180512:CLOSED', '', '', {}, '1', '',
                        '', '26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26,26', ''])
    assert not fut.done()
    assert instrument.symbol == 'AAPL'
    assert instrument.exchange == 'NYSE'

    t.dispatch_message(["52", "1", "43"]),  # CONTRACT_DATA_END
    assert fut.done()
    assert fut.result() is instrument
