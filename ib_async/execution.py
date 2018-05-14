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


class CommissionReport(protocol.Serializable):
    def __init__(self, parent: protocol.ProtocolInterface) -> None:
        self._parent = parent
        self.execution_id = ""
        self.commission = 0.0
        self.currency = ""
        self.realized_pnl = 0.0
        self.income = 0.0
        self.yield_redemption_date = 0.0

    @classmethod
    def get_instance_from(cls, source: protocol.IncomingMessage):
        return cls(source.source)

    def deserialize(self, message: protocol.IncomingMessage):
        self.execution_id = message.read(str)
        self.commission = message.read(float)
        self.currency = message.read(str)
        self.realized_pnl = message.read(float)
        self.income = message.read(float)
        self.yield_redemption_date = message.read(float)

    def serialize(self, message: protocol.OutgoingMessage):
        raise NotImplementedError()
