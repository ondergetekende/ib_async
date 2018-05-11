import asyncio
import logging
import typing

from ib_async.errors import UnsupportedFeature, ApiException
from ib_async.order import Order, Action, OrderType, TimeInForce, OrderOrigin
from ib_async.instrument import Instrument, UnderlyingComponent
from ib_async.messages import Outgoing
from ib_async.protocol import ProtocolInterface, IncomingMessage, ProtocolVersion
from ib_async.utils import wrap_immediate_future

LOG = logging.getLogger(__name__)

OrderEvent = typing.NamedTuple("OrderEvent", [
    ('instrument', Instrument),
    ('size', float),
    ('average_cost', typing.Optional[float])

])


def _dummy_handler__for_get_orders(PositionEvent):
    # This event handler is just used as a dummy to trigger the event subscribe/unsubscribe mechanisms
    pass


class OrdersMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self.__orders = {}  # type: typing.Dict[int, Order]
        self._next_order_id = 1
        self.__submitted_future = {}
        self.__open_orders_future = None

    def get_open_orders(self) -> typing.Awaitable[typing.List[Order]]:
        if not self.__open_orders_future:
            self.__open_orders_future = asyncio.Future()

        self.send_message(Outgoing.REQ_ALL_OPEN_ORDERS, 1)
        return self.__open_orders_future

    def _handle_open_order_end(self):
        if self.__open_orders_future:
            self.__open_orders_future.set_result(self.__orders.values())
            self.__open_orders_future = None

    def create_market_order(self, instrument: Instrument, quantity: float, action: Action = None,
                            time_in_force=TimeInForce.GoodTillCancel,
                            place=True) -> "asyncio.Future[Order]":
        order = Order(self)
        order.instrument = instrument

        order.order_type = OrderType.Market
        order.time_in_force = time_in_force
        if action is None:
            order.action = Action.Buy if quantity > 0 else Action.Sell
            order.total_quantity = abs(quantity)
        else:
            order.action = action
            order.total_quantity = quantity

        if place:
            return self.place_order(order)
        else:
            return wrap_immediate_future(order)

    def create_limit_order(self, instrument: Instrument, quantity: float, limit: float, action: Action = None,
                           time_in_force=TimeInForce.GoodTillCancel,
                           place=True) -> "asyncio.Future[Order]":
        order = Order(self)
        order.instrument = instrument
        order.order_type = OrderType.Limit
        order.limit_price = limit
        order.time_in_force = time_in_force

        if action is None:
            order.action = Action.Buy if quantity > 0 else Action.Sell
            order.total_quantity = abs(quantity)
        else:
            order.action = action
            order.total_quantity = quantity

        if place:
            return self.place_order(order)
        else:
            return wrap_immediate_future(order)

    def place_order(self, order: Order) -> "asyncio.Future[Order]":
        if not order.order_id:
            order.order_id = self._next_order_id

        self.__orders[order.order_id] = order
        self.__submitted_future[order.order_id] = asyncio.Future()
        self.send_message(Outgoing.PLACE_ORDER, 45, order)

        return self.__submitted_future[order.order_id]

    def _handle_order_status(self, order_id: int, status: str, filled: float, remaining: float,
                             average_fill_price: float,
                             perm_id: int, parent_id: int, last_fill_price: int, client_id: int, why_held: str,
                             market_cap_price: float = None):
        order = self.__orders.get(order_id)
        if order:
            order.status = status
            order.filled = filled
            order.remaining = remaining
            order.average_fill_price = average_fill_price
            order.perm_id = perm_id
            order.parent_id = parent_id
            order.last_fill_price = last_fill_price
            order.client_id = client_id
            order.why_held = why_held
            order.market_cap_price = market_cap_price

            order.updated(None)

            submitted_fut = self.__submitted_future.pop(order_id, None)
            if submitted_fut:
                submitted_fut.set_result(order)

    def _handle_open_order(self, order_id: int, instrument: Instrument,
                           action: Action, total_quantity: float, order_type: OrderType,
                           limit_price: float, aux_price: float,
                           time_in_force: TimeInForce, oca_group: str, account: str, open_close: str,
                           origin: OrderOrigin, order_ref: str, client_id: int, perm_id: int,
                           outside_regular_trading_hours: bool, hidden: bool, discretionary_amount: float,
                           good_after_time: str,
                           _deprecated_shares_allocation: str,
                           fa_group: str, fa_method: str, fa_percentage: str, fa_profile: str, msg: IncomingMessage):
        order = self.__orders.get(order_id)
        if not order:
            order = self.__orders[order_id] = Order(self)
            order.order_id = order_id

        order.order_id = order_id
        order.perm_id = perm_id
        order.instrument = instrument
        order.action = action
        order.total_quantity = total_quantity
        order.order_type = order_type
        order.limit_price = limit_price
        order.aux_price = aux_price
        order.time_in_force = time_in_force
        order.oca_group = oca_group
        order.account = account
        order.open_close = open_close
        order.origin = origin
        order.order_ref = order_ref
        order.client_id = client_id
        order.outside_regular_trading_hours = outside_regular_trading_hours
        order.hidden = hidden
        order.discretionary_amount = discretionary_amount
        order.good_after_time = good_after_time
        order.fa_group = fa_group
        order.fa_method = fa_method
        order.fa_percentage = fa_percentage
        order.fa_profile = fa_profile

        order.model_code = msg.read(min_version=ProtocolVersion.MODELS_SUPPORT)
        order.good_till_date = msg.read()
        order.rule80a = msg.read()
        order.percent_offset = msg.read(float)
        order.settling_firm = msg.read()
        order.short_sale_slot = msg.read(int)
        order.designated_location = msg.read()
        order.exempt_code = msg.read(int)
        order.auction_strategy = msg.read()
        order.starting_price = msg.read(float)
        order.stock_ref_price = msg.read(float)
        order.delta = msg.read(float)
        order.stock_range_lower = msg.read(float)
        order.stock_range_upper = msg.read(float)
        order.display_size = msg.read(float)

        order.block_order = msg.read(bool)
        order.sweep_to_fill = msg.read(bool)
        order.all_or_none = msg.read(bool)
        order.min_quantity = msg.read(float)
        order.oca_type = msg.read(int)
        order.etrade_only = msg.read(bool)
        order.firm_quote_only = msg.read(bool)
        order.nbbo_price_cap = msg.read(float)
        order.parent_id = msg.read(int)
        order.trigger_method = msg.read(int)
        order.volatility = msg.read(float)
        order.volatility_type = msg.read(int)
        order.delta_neutral_order_type = msg.read()
        order.delta_neutral_aux_price = msg.read(float)

        if order.delta_neutral_order_type:  # pragma: no cover  (I don't have actual examples of these)
            order.delta_neutral_contract_id = msg.read(int)
            order.delta_neutral_settling_firm = msg.read()
            order.delta_neutral_clearing_account = msg.read()
            order.delta_neutral_clearing_intent = msg.read()
            order.delta_neutral_open_close = msg.read()
            order.delta_neutral_short_sale = msg.read(bool)
            order.delta_neutral_short_sale_slot = msg.read(int)
            order.delta_neutral_designated_location = msg.read()

        order.continuous_update = msg.read(bool)
        order.reference_price_type = msg.read(int)
        order.trail_stop_price = msg.read(float)
        order.trailing_percent = msg.read(float)
        order.basis_points = msg.read(float)
        order.basis_points_type = msg.read(int)
        order.combo_legs_description = msg.read(str)

        if msg.read(int):  # pragma: no cover  (Not implemented)
            raise UnsupportedFeature("combo legs")

        if msg.read(int):  # pragma: no cover  (Not implemented)
            raise UnsupportedFeature("order combo legs")

        order.smart_combo_routing_params = msg.read(typing.Dict[str, str])
        order.scale_init_level_size = msg.read(int)
        order.scale_subs_level_size = msg.read(int)
        order.scale_price_increment = msg.read(float)

        if order.scale_price_increment:  # pragma: no cover  (I don't have actual examples of these)
            order.scale_price_adjust_value = msg.read(float, min_message_version=28)
            order.scale_price_adjust_interval = msg.read(int, min_message_version=28)
            order.scale_profit_offset = msg.read(float, min_message_version=28)
            order.scale_auto_reset = msg.read(bool, min_message_version=28)
            order.scale_init_position = msg.read(int, min_message_version=28)
            order.scale_init_fill_quantity = msg.read(int, min_message_version=28)
            order.scale_random_percent = msg.read(float, min_message_version=28)

        order.hedge_type = msg.read(str, min_message_version=24)
        if order.hedge_type:  # pragma: no cover  (I don't have actual examples of these)
            order.hedge_param = msg.read(str)

        order.opt_out_smart_routing = msg.read(bool, min_message_version=25)

        order.clearing_account = msg.read(str)
        order.clearing_intent = msg.read(str)

        order.not_held = msg.read(bool, min_message_version=22)

        if msg.read(bool, min_message_version=20):  # pragma: no cover  (I don't have actual examples of these)
            order.instrument.underlying_component = msg.read(UnderlyingComponent)

        order.algo_strategy = msg.read(str, min_message_version=21)
        if order.algo_strategy:  # pragma: no cover  (I don't have actual examples of these)
            order.algo_parameters = msg.read(dict)

        order.solicited = msg.read(bool, min_message_version=33)

        order.what_if = msg.read(bool)

        order.status = msg.read()
        order.inital_margin = msg.read()
        order.maintenance_margin = msg.read()
        order.equity_with_loan = msg.read()
        order.commission = msg.read(float)
        order.min_commission = msg.read(float)
        order.max_commission = msg.read(float)
        order.commission_currency = msg.read()
        order.warning_text = msg.read()

        order.randomize_size = msg.read(bool, min_message_version=34)
        order.randomize_price = msg.read(bool, min_message_version=34)

        if order.order_type == "PEG BENCH":  # pragma: no cover  (I don't have actual examples of these)
            order.reference_contract_id = msg.read(int, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
            order.is_pegged_change_amount_decrease = msg.read(bool, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
            order.pegged_change_amount = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
            order.reference_change_amount = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
            order.reference_exchange_id = msg.read(min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)

        if msg.read(int, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK):  # pragma: no cover  (not implemented)
            raise UnsupportedFeature("order conditions")

        order.adjusted_order_type = msg.read(min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.trigger_price = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.trail_stop_price = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.limit_price_offset = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.adjusted_stop_price = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.adjusted_stop_limit_price = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.adjusted_trailing_amount = msg.read(float, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)
        order.adjustable_trailing_unit = msg.read(int, min_version=ProtocolVersion.PEGGED_TO_BENCHMARK)

        order.soft_dollar_tier_name = msg.read(min_version=ProtocolVersion.SOFT_DOLLAR_TIER)
        order.soft_dollar_tier_value = msg.read(min_version=ProtocolVersion.SOFT_DOLLAR_TIER)
        order.soft_dollar_tier_display_name = msg.read(min_version=ProtocolVersion.SOFT_DOLLAR_TIER)

        order.cash_quantity = msg.read(float, min_version=ProtocolVersion.CASH_QTY)

        submitted_fut = self.__submitted_future.pop(order_id, None)
        if submitted_fut:
            submitted_fut.set_result(order)

        order.updated(None)

    def _handle_next_valid_id(self, next_order_id: int):
        self._next_order_id = next_order_id

    def _handle_err_msg(self, request_id: int, error_code: int, error_message: str):
        # We need to specially handle this case, as order_ids are reused.
        fut = self.__submitted_future.pop(request_id, None)

        if fut:
            fut.set_exception(ApiException(error_code, error_message))
        else:
            super()._handle_err_msg(request_id, error_code, error_message)  # type: ignore  # noqa
