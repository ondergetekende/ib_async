import enum
import logging

from ib_async import protocol

LOG = logging.getLogger(__name__)


class BarType(enum.Enum):
    Trades = "TRADES"
    Midpoint = "MIDPOINT"
    Bid = "BID"
    Ask = "ASK"
    BidAsk = "BID_ASK"

    HistoricalVolatility = "HISTORICAL_VOLATILITY"
    OptionImpliedVolatility = "OPTION_IMPLIED_VOLATILITY"
    FeeRate = "FEE_RATE"
    RebateRate = "REBATE_RATE"


class Bar(protocol.Serializable):
    def __init__(self):
        self.time = None  # type: int
        self.open = None  # type: float
        self.high = None  # type: float
        self.low = None  # type: float
        self.close = None  # type: float
        self.volume = None  # type: int
        self.average = None  # type: float
        self.count = None  # type: int
        self.has_gaps = ""

    def serialize(self, message: protocol.OutgoingMessage, *, serializing_historic=False):
        message.add(
            self.time,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.average,
        )

        if serializing_historic:
            message.add(self.has_gaps,
                        max_version=protocol.ProtocolVersion.SYNT_REALTIME_BARS)

        message.add(self.count)

    def deserialize(self, message: protocol.IncomingMessage, *, deserializing_historic=False):
        self.time = message.read(int)
        self.open = message.read(float)
        self.high = message.read(float)
        self.low = message.read(float)
        self.close = message.read(float)
        self.volume = message.read(int)
        self.average = message.read(float)
        if deserializing_historic:
            self.has_gaps = message.read(str, max_version=protocol.ProtocolVersion.SYNT_REALTIME_BARS)
        self.count = message.read(int)


class HistoricBar(Bar):
    def serialize(self, message: protocol.OutgoingMessage, *, serializing_historic=True):
        return super().serialize(message, serializing_historic=True)

    def deserialize(self, message: protocol.IncomingMessage, *, deserializing_historic=True):
        return super().deserialize(message, deserializing_historic=True)
