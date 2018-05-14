import datetime
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

    @property
    def datetime(self):
        return datetime.datetime.utcfromtimestamp(self.time)

    def serialize(self, message: protocol.OutgoingMessage):
        raise NotImplementedError()

    def deserialize(self, message: protocol.IncomingMessage):
        self.time = message.read(int)
        self.open = message.read(float)
        self.high = message.read(float)
        self.low = message.read(float)
        self.close = message.read(float)
        self.volume = message.read(int)
        self.average = message.read(float)
        if message.message_type == protocol.Incoming.HISTORICAL_DATA:
            self.has_gaps = message.read(str, max_version=protocol.ProtocolVersion.SYNT_REALTIME_BARS)
        self.count = message.read(int)

    def __str__(self):
        return "%s: close %.2f" % (self.datetime, self.close)
