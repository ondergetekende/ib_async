import enum
import typing


class SecurityType(str, enum.Enum):
    UNSPECIFIED = ''

    Stock = 'STK'
    Future = 'FUT'
    Index = 'IND'


class SecurityIdentifierType(str, enum.Enum):
    UNSPECIFIED = ''

    CUSIP = "CUSIP"
    SEDOL = "SEDOL"
    ISIN = "ISIN"
    RIC = "RIC"


class Instrument:
    def __init__(self) -> None:
        self.symbol = ""
        self.security_type = SecurityType.UNSPECIFIED
        self.last_trade_date = ""
        self.strike = 0.0
        self.right = ""
        self.exchange = ""
        self.currency = ""
        self.local_symbol = ""
        self.market_name = ""
        self.trading_class = ""
        self.contract_id = 0
        self.minimum_tick = 0.0
        self.market_data_size_multiplier = ""
        self.multiplier = ""
        self.order_types = []  # type: typing.List[str]
        self.valid_exchanges = []  # type: typing.List[str]
        self.price_magnifier = 0
        self.underlying_contract_id = 0
        self.long_name = ""
        self.primary_exchange = ""
        self.contract_month = ""
        self.industry = ""
        self.category = ""
        self.subcategory = ""
        self.time_zone = ""
        self.trading_hours = ""
        self.liquid_hours = ""
        self.ev_rule = ""
        self.ev_multiplier = ""
        self.security_ids = {}  # type: typing.Dict[SecurityIdentifierType, str]
        self.aggregated_group = ""
        self.underlying_symbol = ""
        self.underlying_security_type = SecurityType.UNSPECIFIED
        self.market_rule_ids = ""
        self.real_expiration_date = ""
