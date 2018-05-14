import asyncio
import datetime
import logging
import typing

from ib_async.event import Event
from ib_async.instrument import Instrument
from ib_async.messages import Outgoing
from ib_async.protocol import ProtocolInterface, IncomingMessage

LOG = logging.getLogger(__name__)


class Account:
    def __init__(self, account_id):
        self.account_id = account_id
        self.positions = {}  # type: typing.Dict[Instrument, float]
        self.avg_position_cost = {}  # type: typing.Dict[Instrument, float]


PositionEvent = typing.NamedTuple("PositionEvent", [
    ('account', Account),
    ('instrument', Instrument),
    ('size', float),
    ('average_cost', typing.Optional[float])

])


def _dummy_handler__for_get_positions(PositionEvent):
    # This event handler is just used as a dummy to trigger the event subscribe/unsubscribe mechanisms
    pass


class PositionMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self.__position_future = asyncio.Future()
        self.accounts = {}  # type: typing.Dict[str, Account]

    on_position = Event()  # type: Event[PositionEvent]

    @on_position.on_subscribe
    def __on_position__subscribe(self):
        if not self.__position_future.done():
            self.__position_future.cancel()
        self.__position_future = asyncio.Future()
        return self.send_message(Outgoing.REQ_POSITIONS, 1)

    @on_position.on_unsubscribe
    def __on_position__unsubscribe(self):
        return self.send_message(Outgoing.CANCEL_POSITIONS, 1)

    def get_positions(self) -> typing.Awaitable[None]:
        if self.on_position.has_subscribers:
            # Already subscribed. Data is up-to-date
            return self.__position_future
        else:
            self.on_position += _dummy_handler__for_get_positions

            def conditional_unsubscribe(fut):
                self.on_position -= _dummy_handler__for_get_positions

            self.__position_future.add_done_callback(conditional_unsubscribe)

        return self.__position_future

    def _handle_position_data(self, account_id: str, message: IncomingMessage):
        instrument = Instrument.get_instance_from(message)

        instrument.contract_id = message.read(int)
        instrument.symbol = message.read(str)
        instrument.security_type = message.read(str)
        instrument.last_trade_date = instrument.contract_month = message.read(datetime.date)
        instrument.strike = message.read(float)
        instrument.right = message.read(str)
        instrument.multiplier = message.read(int)
        instrument.exchange = message.read(str)
        instrument.currency = message.read(str)
        instrument.local_symbol = message.read(str)
        if message.message_version >= 2:
            instrument.trading_class = message.read(str)

        try:
            account = self.accounts[account_id]
        except KeyError:
            account = self.accounts[account_id] = Account(account_id)

        size = account.positions[instrument] = message.read(float)
        if message.message_version >= 3:
            average_cost = account.avg_position_cost[instrument] = message.read(float)
        else:
            average_cost = None

        self.on_position(PositionEvent(account, instrument, size, average_cost))

    def _handle_position_end(self):
        if not self.__position_future.done():
            self.__position_future.set_result(None)
