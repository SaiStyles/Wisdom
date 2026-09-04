"""calendar.is_trading_day — weekday/holiday/skip logic (cases 15, 16)."""
from datetime import date
from src.scheduler.calendar import is_trading_day
from src.db.connection import get_conn


def test_weekday_is_trading(db):
    # 2026-04-23 is a Thursday, not on NYSE_HOLIDAYS
    assert is_trading_day(date(2026, 4, 23)) is True


def test_saturday_not_trading(db):
    assert is_trading_day(date(2026, 4, 25)) is False


def test_sunday_not_trading(db):
    assert is_trading_day(date(2026, 4, 26)) is False


def test_nyse_holiday_not_trading(db):
    # 2026-01-01 = New Year's Day (Thursday, on NYSE_HOLIDAYS)
    assert is_trading_day(date(2026, 1, 1)) is False


# Case 15 — /skip_today inserts skip row → is_trading_day False
def test_skip_row_closes_trading_day(db):
    today = date(2026, 4, 23)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO skips (date, reason) VALUES (?, 'admin skip')",
            (today.isoformat(),)
        )
    assert is_trading_day(today) is False


# Case 16 — /test_reset DELETEs skip row → is_trading_day True again
def test_skip_removed_restores_trading_day(db):
    today = date(2026, 4, 23)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO skips (date, reason) VALUES (?, 'admin skip')",
            (today.isoformat(),)
        )
        conn.execute("DELETE FROM skips WHERE date = ?", (today.isoformat(),))
    assert is_trading_day(today) is True


def test_skips_other_dates_dont_affect_today(db):
    today = date(2026, 4, 23)
    tomorrow = date(2026, 4, 24)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO skips (date, reason) VALUES (?, 'admin skip')",
            (tomorrow.isoformat(),)
        )
    assert is_trading_day(today) is True
    assert is_trading_day(tomorrow) is False
