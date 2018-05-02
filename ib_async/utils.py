import datetime
import typing


def to_ib_date(value: typing.Union[str, datetime.datetime, float, int]) -> str:
    if isinstance(value, (float, int)):
        value = datetime.datetime.utcfromtimestamp(value)

    if isinstance(value, datetime.datetime):
        # 20180201 10:00:00 GMT
        if value.tzinfo:
            value = value.strftime("%Y%m%d %H:%D:%S %Z")
        else:
            value = value.strftime("%Y%m%d %H:%D:%S GMT")

    return value


def to_ib_duration(value: typing.Union[str, datetime.timedelta, float, int]) -> str:
    if isinstance(value, datetime.timedelta):
        value = value.total_seconds()

    if isinstance(value, (float, int)):
        if value > 0xFFFF:
            return "%i D" % int(value / 86400)
        else:
            return "%i S" % int(value)

    return value
