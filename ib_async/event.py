import asyncio
import typing
import weakref

T = typing.TypeVar('T')


class _EventQueue:
    def __init__(self):
        self.queue = []
        self.future = asyncio.Future()

    def push(self, value):
        self.queue.append(value)
        if not self.future.done():
            self.future.set_result(None)

    async def __anext__(self):
        if not self.queue:
            await self.future
            self.future = asyncio.Future()

        head = self.queue[0]
        self.queue = self.queue[1:]
        return head


class EventInstance(typing.Generic[T]):
    def __init__(self, on_subscribe: typing.Callable[[], None],
                 on_unsubscribe: typing.Callable[[], None]) -> None:
        self.on_subscribe = on_subscribe
        self.on_unsubscribe = on_unsubscribe
        self._handlers = []  # type: typing.List[weakref.ref]

    def _live_handlers(self, remove=None) -> typing.List[typing.Callable[[T], typing.Any]]:
        """Returns a list of event handlers that are not garbage collected."""

        had_handlers = len(self._handlers)

        live_handlers = []  # type: typing.List[weakref.ref]
        result = []
        for handler_ref in self._handlers:
            handler = handler_ref()
            if handler == remove:
                remove = None  # only allow one removal per round
            elif handler is not None:
                live_handlers.append(handler_ref)
                result.append(handler)

        self._handlers = live_handlers

        if had_handlers and not self._handlers and self.on_unsubscribe:
            self.on_unsubscribe()

        if remove:
            # removal was requested, but didn't happen
            raise KeyError(remove)

        return result

    @property
    def has_subscribers(self):
        return len(self._live_handlers()) > 0

    def __call__(self, arg: T):
        for handler in self._live_handlers():
            handler(arg)

    def __aiter__(self):
        queue = _EventQueue()
        self.__iadd__(queue.push)
        return queue

    def __iadd__(self, other: typing.Callable[[T], typing.Any]):
        had_handlers = len(self._handlers)
        try:
            handler_ref = weakref.WeakMethod(other)  # type: ignore
        except TypeError:  # apparently other isn't a method. Use weakref instead
            handler_ref = weakref.ref(other)  # type: ignore

        self._handlers.append(handler_ref)

        if not had_handlers and self.on_subscribe:
            self.on_subscribe()
        return self

    def __isub__(self, other: typing.Callable[[T], typing.Any]):
        self._live_handlers(other)
        return self


class Event(typing.Generic[T]):
    def __init__(self):
        self._attribute = "__evt_%x" % abs(id(self))
        self._on_subscribe = None
        self._on_unsubscribe = None

    def __get__(self, instance, owner) -> EventInstance[T]:
        if not instance:
            return self  # type: ignore  # noqa

        try:
            event = getattr(instance, self._attribute)
        except AttributeError:
            event = EventInstance(
                (lambda: self._on_subscribe(instance)) if self._on_subscribe else None,
                (lambda: self._on_unsubscribe(instance)) if self._on_unsubscribe else None,
            )
            setattr(instance, self._attribute, event)

        return event

    def on_subscribe(self, fn: typing.Callable[[typing.Any], None]):
        """Decorator to add a handler for the first data consumer.

        Can be used to initiate a data stream."""
        assert not self._on_subscribe, 'only one handler allowed'
        self._on_subscribe = fn
        return self

    def on_unsubscribe(self, fn: typing.Callable[[typing.Any], None]):
        """Decorator to add a handler when th last data consumer loses interest.

        Can be used to terminate a data stream."""
        assert not self._on_unsubscribe, 'only one handler allowed'
        self._on_unsubscribe = fn
        return self
