import pendulum
from pendulum import DateTime


def now(tz='Asia/Shanghai') -> DateTime:
    return pendulum.now(tz)
