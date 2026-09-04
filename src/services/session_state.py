from datetime import datetime, time
import pytz
import config
from src.utils.timezones import ET
from src.scheduler.calendar import is_trading_day

CUTOFF = time(config.CUTOFF_HOUR, config.CUTOFF_MINUTE)
BROADCAST = time(config.BROADCAST_HOUR, config.BROADCAST_MINUTE)


def is_submission_open() -> bool:
    if config.TEST_MODE:
        return True
    now = datetime.now(ET)
    today = now.date()
    if not is_trading_day(today):
        return False
    current_time = now.time()
    return BROADCAST <= current_time <= CUTOFF
