import logging

from ib_async.instrument import Instrument
from ib_async.messages import Outgoing
from ib_async.protocol import RequestId, ProtocolInterface

LOG = logging.getLogger(__name__)


class MarketDepthMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self.__instruments = {}

    def subscribe_market_depth(self, instrument: Instrument, num_rows: int):
        if instrument._market_depth_request_id:
            request_id = instrument._market_depth_request_id
        else:
            request_id, future = self.make_future()
            self.resolve_future(request_id, None)

        self.send_message(Outgoing.REQ_MKT_DEPTH, 5, request_id,
                          # We cannot use the instrument serialization, as this specific message has different fields
                          instrument.contract_id, instrument.symbol, instrument.security_type,
                          instrument.contract_month or instrument.last_trade_date,
                          instrument.strike, instrument.right,
                          instrument.multiplier, instrument.exchange,
                          instrument.currency, instrument.local_symbol, instrument.trading_class,
                          num_rows,
                          {})  # options. Undocumented

        self.__instruments[request_id] = instrument
        instrument._market_depth_request_id = request_id

    def unsubscribe_market_depth(self, instrument: Instrument):
        if instrument._market_depth_request_id:
            self.send_message(Outgoing.CANCEL_MKT_DEPTH, 0, instrument._market_depth_request_id)
            self.__instruments.pop(instrument._market_depth_request_id, None)
            instrument._market_depth_request_id = None

    def _handle_market_depth(self, request_id: RequestId, position: int,
                             operation: int, side: int, price: float, size: int):
        self._handle_market_depth_l2(request_id, position, "", operation, side, price, size)

    def _handle_market_depth_l2(self, request_id: RequestId, position: int, market_maker: str,
                                operation: int, side: int, price: float, size: int):
        instrument = self.__instruments.get(request_id)
        instrument.handle_market_depth(position, market_maker, operation, side, price, size)
