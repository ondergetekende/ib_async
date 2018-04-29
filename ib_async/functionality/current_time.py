import asyncio
import logging
import typing

from ib_async.messages import Outgoing
from ib_async.protocol import ProtocolInterface

LOG = logging.getLogger(__name__)


class CurrentTimeMixin(ProtocolInterface):
    def __init__(self):
        super().__init__()
        self._current_time_future = asyncio.Future()

    def _handle_current_time(self, current_time: float):
        self._current_time_future.set_result(current_time)

    def current_time(self) -> typing.Awaitable[float]:
        """Asks the current system time on the server side."""
        self._current_time_future = asyncio.Future()
        self.send_message(Outgoing.REQ_CURRENT_TIME, 1)
        return self._current_time_future
