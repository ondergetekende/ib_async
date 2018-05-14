import asyncio  # noqa
import logging
import typing  # noqa

from ib_async.errors import UnsupportedFeature
from ib_async.event import Event
from ib_async.execution import Execution
from ib_async.instrument import Instrument, SecurityType
from ib_async.messages import Outgoing
from ib_async.protocol import ProtocolInterface, IncomingMessage, ProtocolVersion, RequestId

LOG = logging.getLogger(__name__)


class ExecutionsMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()

        self.__pending_execs = {}  # type: typing.Dict[RequestId, typing.List[Execution]]

    on_execution = Event()  # type: Event[Execution]

    def get_executions(self, client_id=0, account_code="", time="", symbol="", security_type=SecurityType.Unspecified,
                       exchange="", side="") -> "asyncio.Future[Execution]":
        request_id, future = self.make_future()

        self.send_message(
            Outgoing.REQ_EXECUTIONS, 3, request_id,
            client_id, account_code, time, symbol, security_type, exchange, side
        )

        self.__pending_execs[request_id] = []
        return future

    def _handle_execution_data(self, request_id: RequestId, order_id: int, message: IncomingMessage):
        if message.message_version <= 10:
            raise UnsupportedFeature("execution details before version v10")

        execution = Execution(self, message.read(Instrument))
        execution.order_id = order_id
        execution.execution_id = message.read()
        execution.time = message.read()
        execution.account_number = message.read()
        execution.exchange = message.read()
        execution.side = message.read()
        execution.share = message.read(float)
        execution.price = message.read(float)
        execution.perm_id = message.read(int)
        execution.client_id = message.read(int)
        execution.liquidation = message.read(int)
        execution.cumulative_quantity = message.read(float)
        execution.average_price = message.read(float)
        execution.order_ref = message.read()
        execution.ev_rule = message.read()
        execution.ev_multiplier = message.read(float)
        execution.model_code = message.read(min_version=ProtocolVersion.MODELS_SUPPORT)
        execution.last_liquidity = message.read(int, min_version=ProtocolVersion.LAST_LIQUIDITY)

        execs = self.__pending_execs.get(request_id)
        if execs is not None:
            execs.append(execution)

        self.on_execution(execution)

        execution.instrument.on_execution(execution)
        if execution.order:
            execution.order.on_execution(execution)

    def _handle_execution_data_end(self, request_id: RequestId):
        self.resolve_future(request_id,
                            self.__pending_execs.get(request_id) or [])
