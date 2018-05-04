import asyncio
import pytest

from ib_async.event import Event


def test_simple():
    class EventParent:
        on_whatever = Event()

    assert isinstance(EventParent.on_whatever, Event)

    instance = EventParent()

    messages = []

    async def consumer():
        async for message in instance.on_whatever:
            assert not messages
            messages.append(message)

    cons_handle = asyncio.ensure_future(consumer())
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))

    instance.on_whatever("Test")
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))

    cons_handle.cancel()

    assert len(messages) == 1


def test_subs():
    class EventParent:
        subscribed = False
        unsubscribed = False

        on_whatever = Event()

        @on_whatever.on_subscribe
        def whatever_subscribe(self):
            assert not self.subscribed
            self.subscribed = True

        @on_whatever.on_unsubscribe
        def whatever_unsubscribe(self):
            assert not self.unsubscribed
            self.unsubscribed = True

    instance = EventParent()

    async def consumer():
        it = instance.on_whatever.__aiter__()
        msg = await it.__anext__()
        assert msg == 'Test'

    cons_handle = asyncio.ensure_future(consumer())
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))

    assert instance.on_whatever.has_subscribers
    assert instance.subscribed
    assert not instance.unsubscribed

    instance.on_whatever("Test")

    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))
    assert cons_handle.done()

    assert not instance.on_whatever.has_subscribers
    assert instance.subscribed
    assert instance.unsubscribed


def test_with_func_handler():
    class EventParent:
        on_whatever = Event()

    msg = None

    def handler(arg):
        nonlocal msg
        assert not msg
        msg = arg

    instance = EventParent()
    instance.on_whatever += handler
    assert instance.on_whatever.has_subscribers

    instance.on_whatever('Test')
    assert msg == 'Test'

    del handler
    assert not instance.on_whatever.has_subscribers


def test_with_handler_remove():
    class EventParent:
        on_whatever = Event()

    msg = []

    def handler(arg):
        msg.append(arg)

    instance = EventParent()
    instance.on_whatever += handler
    instance.on_whatever += handler
    assert instance.on_whatever.has_subscribers

    instance.on_whatever('Test')
    assert msg == ['Test', 'Test']

    instance.on_whatever -= handler
    assert instance.on_whatever.has_subscribers

    instance.on_whatever -= handler
    assert not instance.on_whatever.has_subscribers

    with pytest.raises(KeyError):
        instance.on_whatever -= handler


def test_with_method_handler():
    class EventParent:
        on_whatever = Event()

    class HandlerHolder:
        def handler(self, arg):
            nonlocal msg
            assert not msg
            msg = arg

    msg = None

    instance = EventParent()
    handler_holder = HandlerHolder()
    instance.on_whatever += handler_holder.handler
    assert instance.on_whatever.has_subscribers

    instance.on_whatever('Test')
    assert msg == 'Test'

    del handler_holder
    assert not instance.on_whatever.has_subscribers
