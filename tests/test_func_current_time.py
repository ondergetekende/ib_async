from ib_async.functionality.current_time import CurrentTimeMixin
from .utils import FunctionalityTestHelper


class MixinFixture(CurrentTimeMixin, FunctionalityTestHelper):
    pass


def test_current_time():
    t = MixinFixture()

    fut = t.current_time()
    assert not fut.done()

    t.dispatch_message(["49", "1", "1524957956"])
    assert fut.done()
    assert fut.result() == 1524957956
