from datetime import date
from src.db.connection import get_conn

# NYSE holidays (observed dates) for 2025-2026
NYSE_HOLIDAYS = {
    date(2025, 1, 1),
    date(2025, 1, 20),
    date(2025, 2, 17),
    date(2025, 4, 18),
    date(2025, 5, 26),
    date(2025, 6, 19),
    date(2025, 7, 4),
    date(2025, 9, 1),
    date(2025, 11, 27),
    date(2025, 12, 25),
    date(2026, 1, 1),
    date(2026, 1, 19),
    date(2026, 2, 16),
    date(2026, 4, 3),
    date(2026, 5, 25),
    date(2026, 6, 19),
    date(2026, 7, 3),
    date(2026, 9, 7),
    date(2026, 11, 26),
    date(2026, 12, 25),
}


def is_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    if d in NYSE_HOLIDAYS:
        return False
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM skips WHERE date = ?", (d.isoformat(),)
        ).fetchone()
    return row is None
