import enum
import typing  # noqa

from ib_async.errors import UnsupportedFeature
from ib_async.event import Event
from ib_async import execution  # noqa
from ib_async.instrument import Instrument  # noqa
from ib_async.protocol import ProtocolInterface, Serializable, ProtocolVersion, IncomingMessage, OutgoingMessage


class OrderOrigin(enum.Enum):
    Customer = 0
    Firm = 1
    Unknown = 2


class AuctionStrategy(enum.Enum):
    Unset = 0
    Match = 1
    Improvement = 2
    Transparent = 3


class Action(str, enum.Enum):
    Buy = 'BUY'
    Sell = 'SELL'
    SShort = 'SSHORT'
    SLONG = 'SLONG'


class VolatilityType(enum.Enum):
    Daily = 1
    Annual = 2


class OrderType(str, enum.Enum):
    Undefined = ""

    BoxTop = 'BOX TOP'
    Limit = 'LMT'
    LimitIfTouched = 'LIT'
    LimitOnClose = 'LOC'
    Market = 'MKT'
    MarketIfTouched = 'MIT'
    MarketOnClose = 'MOC'
    MarketToLimit = 'MTL'
    MarketWithProtection = 'MKT PRT'
    PassiveRelative = 'PASSV REL'
    PeggedToMidpoint = 'PEG MID'
    PeggedToMarket = 'PEG MKT'
    PeggedToStock = 'PEG STK'
    PeggedToBenchmark = 'PEG BENCH'
    Relative = 'REL'
    RelativeLimitCombo = 'REL + LMT'
    RelativeMarketCombo = 'REL + MKT'
    Stop = "STP"
    StopLimit = "STP LMT"
    StopWithProtection = "STP PRT"
    TrailingStop = "TRAIL"
    TrailingStopLimit = "TRAIL LIMIT"
    Volatility = 'VOL'


class TimeInForce(str, enum.Enum):
    Day = "DAY"  # Valid for the day only.

    # Good until canceled. The order will continue to work within the system and in the marketplace until it executes
    # or is canceled. GTC orders will be automatically be cancelled under the following conditions: If a corporate
    # action on a security results in a stock split (forward or reverse), exchange for shares, or distribution of
    # shares. If you do not log into your IB account for 90 days.
    # At the end of the calendar quarter following the current quarter. For example, an order placed during the third
    # quarter of 2011 will be canceled at the end of the first quarter of 2012. If the last day is a non-trading day,
    # the cancellation will occur at the close of the final trading day of that quarter. For example, if the last day
    # of the quarter is Sunday, the orders will be cancelled on the preceding Friday.
    # Orders that are modified will be assigned a new “Auto Expire” date consistent with the end of the calendar
    # quarter following the current quarter.
    # Orders submitted to IB that remain in force for more than one day will not be reduced for dividends. To allow
    # adjustment to your order price on ex-dividend date, consider using a Good-Til-Date/Time (GTD) or
    # Good-after-Time/Date (GAT) order type, or a combination of the two.
    GoodTillCancel = "GTC"

    # Immediate or Cancel. Any portion that is not filled as soon as it becomes available in the market is canceled.
    ImmediateOrCancel = "IOC"

    # Good until Date. It will remain working within the system and in the marketplace until it executes or until the
    # close of the market on the date specified
    GoodTillDate = "GTD"
    Opening = "OPG"  # Use OPG to send a market-on-open (MOO) or limit-on-open (LOO) self

    # If the entire Fill-or-Kill order does not execute as soon as it becomes available, the entire order is canceled.
    FillOrKill = "FOK"

    DayTillCancel = "DTC"  # Day until Canceled


class Order(Serializable):
    def __init__(self, parent: ProtocolInterface) -> None:
        self._parent = parent
        self.instrument = None  # type: Instrument

        # Filled by status messages
        self.status = None  # type: str
        self.filled = None  # type: float
        self.remaining = None  # type: float
        self.average_fill_price = None  # type: float
        self.perm_id = None  # type: int
        self.parent_id = None  # type: int
        self.last_fill_price = None  # type: float
        self.client_id = None  # type: int
        self.why_held = None  # type: str
        self.market_cap_price = None  # type: float

        self.order_ref = None  # type: str
        self.combo_legs_description = None  # type: str
        self.inital_margin = None  # type: str
        self.maintenance_margin = None  # type: str
        self.equity_with_loan = None  # type: str
        self.commission = None  # type: float
        self.min_commission = None  # type: float
        self.max_commission = None  # type: float
        self.commission_currency = None  # type: str
        self.warning_text = None  # type: str

        self.order_id = 0
        self.client_id = 0
        self.perm_id = 0

        # main order fields
        self.action = None  # type: Action
        self.total_quantity = 0.0
        self.order_type = OrderType.Market

        # The LIMIT price. Used for limit, stop-limit and relative orders. In all other cases specify zero. For
        # relative orders with no limit price, also specify zero.
        self.limit_price = None  # type: float

        # Generic field to contain the stop price for STP LMT orders, trailing amount, etc.
        self.aux_price = None  # type: float

        # extended order fields
        self.time_in_force = TimeInForce.GoodTillCancel

        self.active_start_time = ""  # for GTC orders.
        self.active_stop_time = ""  # for GTC orders.

        self.oca_group = ""
        self.oca_type = 0
        self.order_reference = ""
        self.transmit = True
        self.parent_id = 0
        self.block_order = False
        self.sweep_to_fill = False
        self.display_size = 0
        self.trigger_method = 0
        self.outside_regular_trading_hours = False
        self.hidden = False
        self.good_after_time = ""
        self.good_till_date = ""
        self.rule80a = ""

        self.all_or_none = False
        self.min_quantity = None  # type: int
        self.percent_offset = None  # type: float
        self.override_percentage_constraints = False
        self.trail_stop_price = None  # type: float
        self.trailing_percent = None  # type: float

        # financial advisors only
        self.fa_group = ""
        self.fa_profile = ""
        self.fa_method = ""
        self.fa_percentage = ""

        # institutional (ie non-cleared) only
        self.open_close = "O"
        self.origin = OrderOrigin.Customer
        self.short_sale_slot = 0
        self.designated_location = ""
        self.exempt_code = -1

        # SMART routing only
        self.discretionary_amount = 0.0
        self.etrade_only = True
        self.firm_quote_only = True
        self.nbbo_price_cap = None  # type: float
        self.opt_out_smart_routing = False

        # BOX exchange orders only
        self.auction_strategy = AuctionStrategy.Unset
        self.starting_price = None  # type: float
        self.stock_ref_price = None  # type: float
        self.delta = None  # type: float

        # pegged to stock and VOL orders only
        self.stock_range_lower = None  # type: float
        self.stock_range_upper = None  # type: float

        self.randomize_price = False
        self.randomize_size = False

        # VOLATILITY ORDERS ONLY
        self.volatility = None  # type: float
        self.volatility_type = None  # type: VolatilityType
        self.delta_neutral_order_type = ""
        self.delta_neutral_aux_price = None  # type: float
        self.delta_neutral_contract_id = 0
        self.delta_neutral_settling_firm = ""
        self.delta_neutral_clearing_account = ""
        self.delta_neutral_clearing_intent = ""
        self.delta_neutral_open_close = ""
        self.delta_neutral_short_sale = False
        self.delta_neutral_short_sale_slot = 0
        self.delta_neutral_designated_location = ""
        self.continuous_update = False
        self.reference_price_type = None  # type: int # 1=Average, 2 = BidOrAsk

        # COMBO ORDERS ONLY
        self.basis_points = None  # type: float  # EFP orders only
        self.basis_points_type = None  # type: int # EFP orders only

        # SCALE ORDERS ONLY
        self.scale_init_level_size = None  # type: int
        self.scale_subs_level_size = None  # type: int
        self.scale_price_increment = None  # type: float
        self.scale_price_adjust_value = None  # type: float
        self.scale_price_adjust_interval = None  # type: int
        self.scale_profit_offset = None  # type: float
        self.scale_auto_reset = False
        self.scale_init_position = None  # type: int
        self.scale_init_fill_quantity = None  # type: int
        self.scale_random_percent = False
        self.scale_table = ""

        #
        # HEDGE ORDERS
        self.hedge_type = ""  # 'D' - delta, 'B' - beta, 'F' - FX, 'P' - pair
        self.hedge_param = ""  # 'beta=X' value for beta hedge, 'ratio=Y' for pair hedge

        # Clearing info
        self.account = ""  # IB account
        self.settling_firm = ""
        self.clearing_account = ""  # True beneficiary of the order
        self.clearing_intent = ""  # "" (Default), "IB", "Away", "PTA" (PostTrade)

        # ALGO ORDERS ONLY
        self.algo_strategy = ""
        self.algo_parameters = {}  # type: typing.Dict[str, str]
        self.smart_combo_routing_params = {}  # type: typing.Dict[str, str]

        self.algo_id = ""

        # What-if
        self.what_if = False

        # Not Held
        self.not_held = False
        self.solicited = False

        self.model_code = ""

        self.order_miscellaneous_options = {}  # type: typing.Dict[str, str]

        self.reference_contract_id = 0
        self.pegged_change_amount = 0.0
        self.is_pegged_change_amount_decrease = False
        self.reference_change_amount = 0.0
        self.reference_exchange_id = ""
        self.adjusted_order_type = OrderType.Undefined
        self.trigger_price = 1.7976931348623157e+308  # type: float
        self.limit_price_offset = 1.7976931348623157e+308  # type: float
        self.adjusted_stop_price = 1.7976931348623157e+308  # type: float
        self.adjusted_stop_limit_price = 1.7976931348623157e+308  # type: float
        self.adjusted_trailing_amount = 1.7976931348623157e+308  # type: float
        self.adjustable_trailing_unit = 0

        self.conditions = []  # type: typing.List[None]  # not suppored yet
        self.conditions_cancel_order = False
        self.conditions_ignore_regular_trading_hours = False

        self.ext_operator = ""

        self.soft_dollar_tier_name = ""
        self.soft_dollar_tier_value = ""
        self.soft_dollar_tier_display_name = ""

        # native cash quantity
        self.cash_quantity = 1.7976931348623157e+308  # type: float

        self.mifid2_decision_maker = ""
        self.mifid2_decision_algo = ""
        self.mifid2_execution_trader = ""
        self.mifid2_execution_algo = ""

    updated = Event()  # type: Event[None]
    on_execution = Event()  # type: Event[execution.Execution]

    def serialize(self, message: OutgoingMessage):
        message.add(self.order_id)
        message.add(self.instrument)

        if self.instrument.security_ids:
            security_id_type, security_id = next(iter(self.instrument.security_ids.items()))
        else:
            security_id_type = security_id = None
        message.add(security_id_type)
        message.add(security_id)

        message.add(self.action)
        message.add(self.total_quantity)
        message.add(self.order_type)

        message.add(self.limit_price)
        message.add(self.aux_price)

        message.add(self.time_in_force)
        message.add(self.oca_group)
        message.add(self.account)
        message.add(self.open_close)
        message.add(self.origin)
        message.add(self.order_reference)
        message.add(self.transmit)
        message.add(self.parent_id)

        message.add(self.block_order)
        message.add(self.sweep_to_fill)
        message.add(self.display_size)
        message.add(self.trigger_method)

        message.add(self.outside_regular_trading_hours)
        message.add(self.hidden)

        assert self.instrument.security_type != 'BAG'  # not supported

        message.add("")  # deprecated sharesAllocation field

        message.add(self.discretionary_amount)
        message.add(self.good_after_time)
        message.add(self.good_till_date)

        message.add(self.fa_group)
        message.add(self.fa_method)
        message.add(self.fa_percentage)
        message.add(self.fa_profile)

        message.add(self.model_code, min_version=ProtocolVersion.MODELS_SUPPORT)

        # institutional short saleslot data (srv v18 and above)
        message.add(self.short_sale_slot)  # # 0 for retail, 1 or 2 for institutions
        message.add(self.designated_location)  # # populate only when shortSaleSlot = 2.
        message.add(self.exempt_code)

        message.add(self.oca_type)

        message.add(self.rule80a)
        message.add(self.settling_firm)
        message.add(self.all_or_none)
        message.add(self.min_quantity)
        message.add(self.percent_offset)
        message.add(self.etrade_only)
        message.add(self.firm_quote_only)
        message.add(self.nbbo_price_cap)
        message.add(self.auction_strategy)  # AUCTION_MATCH, AUCTION_IMPROVEMENT, AUCTION_TRANSPARENT
        message.add(self.starting_price)
        message.add(self.stock_ref_price)
        message.add(self.delta)
        # Volatility orders had specific watermark price attribs in server version 26
        # double lower = (protocol_version == 26 && isVolOrder) ? DBL_MAX : selfstockRangeLower;
        # double upper = (protocol_version == 26 && isVolOrder) ? DBL_MAX : selfstockRangeUpper;
        message.add(self.stock_range_lower)
        message.add(self.stock_range_upper)

        message.add(self.override_percentage_constraints)

        # Volatility orders (srv v26 and above)
        message.add(self.volatility)
        message.add(self.volatility_type)

        message.add(self.delta_neutral_order_type)
        message.add(self.delta_neutral_aux_price)

        if self.delta_neutral_order_type:
            # pragma: no cover  (I don't have actual examples of these)
            message.add(self.delta_neutral_contract_id)
            message.add(self.delta_neutral_settling_firm)
            message.add(self.delta_neutral_clearing_account)
            message.add(self.delta_neutral_clearing_intent)

            message.add(self.delta_neutral_open_close)
            message.add(self.delta_neutral_short_sale)
            message.add(self.delta_neutral_short_sale_slot)
            message.add(self.delta_neutral_designated_location)

        message.add(self.continuous_update)

        message.add(self.reference_price_type)

        message.add(self.trail_stop_price)

        message.add(self.trailing_percent)

        # SCALE orders
        message.add(self.scale_init_level_size)
        message.add(self.scale_subs_level_size)

        message.add(self.scale_price_increment)

        if self.scale_price_increment and self.scale_price_increment > 0.0:
            # pragma: no cover  (I don't have actual examples of these)
            message.add(self.scale_price_adjust_value)
            message.add(self.scale_price_adjust_interval)
            message.add(self.scale_profit_offset)
            message.add(self.scale_auto_reset)
            message.add(self.scale_init_position)
            message.add(self.scale_init_fill_quantity)
            message.add(self.scale_random_percent)

        message.add(self.scale_table)
        message.add(self.active_start_time)
        message.add(self.active_stop_time)

        # HEDGE orders
        message.add(self.hedge_type)
        if self.hedge_type:  # pragma: no cover  (I don't have actual examples of these)
            message.add(self.hedge_param)

        message.add(self.opt_out_smart_routing)

        message.add(self.clearing_account)
        message.add(self.clearing_intent)

        message.add(self.not_held)

        message.add(bool(self.instrument.underlying_component))
        if self.instrument.underlying_component:  # pragma: no cover  (I don't have actual examples of these)
            message.add(self.instrument.underlying_component)

        message.add(self.algo_strategy)
        if self.algo_strategy:  # pragma: no cover  (I don't have actual examples of these)
            message.add(self.algo_parameters)

        message.add(self.algo_id)

        message.add(self.what_if)

        message.add("".join("%s=%s;" % (k, v) for (k, v) in self.order_miscellaneous_options.items()))

        message.add(self.solicited)

        message.add(self.randomize_size)
        message.add(self.randomize_price)

        if self.order_type == "PEG BENCH":  # pragma: no cover  (I don't have actual examples of these)
            message.add(self.reference_contract_id,
                        self.is_pegged_change_amount_decrease,
                        self.pegged_change_amount,
                        self.reference_change_amount,
                        self.reference_exchange_id,
                        min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)

        if self.conditions:  # pragma: no cover  (Not implemented)
            raise UnsupportedFeature("Order conditions")

        message.add(0,  # no conditions
                    self.adjusted_order_type,
                    self.trigger_price,
                    self.limit_price_offset,
                    self.adjusted_stop_price,
                    self.adjusted_stop_limit_price,
                    self.adjusted_trailing_amount,
                    self.adjustable_trailing_unit,
                    min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)

        message.add(self.ext_operator,
                    min_version=ProtocolVersion.EXT_OPERATOR)

        message.add(self.soft_dollar_tier_name,
                    self.soft_dollar_tier_value,
                    min_version=ProtocolVersion.SOFT_DOLLAR_TIER)

        message.add(self.cash_quantity,
                    min_version=ProtocolVersion.CASH_QTY)

        message.add(self.mifid2_decision_maker,
                    self.mifid2_decision_algo,
                    min_version=ProtocolVersion.DECISION_MAKER)

        message.add(self.mifid2_execution_trader,
                    self.mifid2_execution_algo,
                    min_version=ProtocolVersion.MIFID_EXECUTION)

    def deserialize(self, message: IncomingMessage):
        assert False, "Implemented in message handlers"
