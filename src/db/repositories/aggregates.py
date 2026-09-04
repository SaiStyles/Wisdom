from dataclasses import dataclass
from datetime import date
from typing import Optional
from src.db.connection import get_conn


@dataclass
class DailyAggregate:
    id: int
    date: date
    expansion_up_count: int
    expansion_down_count: int
    expansion_both_count: int
    range_count: int
    avg_confidence: float
    total_submissions: int
    leading_option: Optional[int]
    leading_pct: Optional[float]
    signal_type: Optional[str]
    posted_to_group: bool


def save(
    today: date,
    up: int,
    down: int,
    both: int,
    range_: int,
    avg_confidence: float,
    total: int,
    leading_option: Optional[int] = None,
    leading_pct: Optional[float] = None,
    signal_type: Optional[str] = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO daily_aggregates
                 (date, expansion_up_count, expansion_down_count, expansion_both_count,
                  range_count, avg_confidence, total_submissions,
                  leading_option, leading_pct, signal_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(date) DO UPDATE SET
                 expansion_up_count=excluded.expansion_up_count,
                 expansion_down_count=excluded.expansion_down_count,
                 expansion_both_count=excluded.expansion_both_count,
                 range_count=excluded.range_count,
                 avg_confidence=excluded.avg_confidence,
                 total_submissions=excluded.total_submissions,
                 leading_option=excluded.leading_option,
                 leading_pct=excluded.leading_pct,
                 signal_type=excluded.signal_type""",
            (today.isoformat(), up, down, both, range_, avg_confidence, total,
             leading_option, leading_pct, signal_type)
        )


def mark_posted(today: date) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE daily_aggregates SET posted_to_group = TRUE WHERE date = ?",
            (today.isoformat(),)
        )


def get_for_date(today: date) -> Optional[DailyAggregate]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM daily_aggregates WHERE date = ?", (today.isoformat(),)
        ).fetchone()
    return DailyAggregate(**dict(row)) if row else None
