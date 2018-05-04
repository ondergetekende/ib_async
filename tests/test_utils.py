import datetime

from ib_async import utils


def test_to_ib_date():
    assert utils.to_ib_date("20170804 21:31:28 GMT") == "20170804 21:31:28 GMT"
    assert utils.to_ib_date(1501882288) == "20170804 21:31:28 GMT"
    assert utils.to_ib_date(datetime.datetime(2017, 8, 4, 21, 31, 28)) == "20170804 21:31:28 GMT"

    class Timezone(datetime.tzinfo):
        def __init__(self, name, offset):
            self.name = name
            self.offset = offset

        def tzname(self, dt):
            return self.name

        def dst(self, dt):
            return None

    assert utils.to_ib_date(datetime.datetime(2017, 8, 4, 21, 31, 28,
                                              tzinfo=Timezone("CET", -6),
                                              )) == "20170804 21:31:28 CET"


def test_to_ib_duration():
    assert utils.to_ib_duration(3600) == '3600 S'
    assert utils.to_ib_duration(86400 * 365) == '365 D'
    assert utils.to_ib_duration(datetime.timedelta(seconds=17)) == '17 S'
    assert utils.to_ib_duration("17 S") == '17 S'
