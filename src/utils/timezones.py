from datetime import datetime
import pytz
import config

ET = pytz.timezone(config.TIMEZONE)


def now_et() -> datetime:
    return datetime.now(ET)


def today_et():
    return now_et().date()
