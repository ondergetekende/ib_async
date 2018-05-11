import typing

from ib_async import instrument
from ib_async import protocol


class Execution:
    def __init__(self, parent: protocol.ProtocolInterface, instrument: instrument.Instrument) -> None:
        self._parent = parent
        self.instrument = instrument
        self.order_id = 0
        self.execution_id = ""
        self.time = ""
        self.account_number = ""
        self.exchange = ""
        self.side = ""
        self.share = 0.0
        self.price = 0.0
        self.perm_id = 0
        self.client_id = 0
        self.liquidation = 0
        self.cumulative_quantity = 0.0
        self.average_price = 0.0
        self.order_ref = ""
        self.ev_rule = ""
        self.ev_multiplier = 0.0
        self.model_code = ""
        self.last_liquidity = 0

    @property
    def order(self):
        import ib_async.functionality.orders

        parent = typing.cast(ib_async.functionality.orders.OrdersMixin, self._parent)
        return parent.get_order(self.order_id)
