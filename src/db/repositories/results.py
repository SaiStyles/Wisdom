from dataclasses import dataclass
from datetime import date
from typing import Optional
from src.db.connection import get_conn


@dataclass
class Result:
    id: int
    date: date
    actual_outcome: int
    consensus_prediction: Optional[int]
    consensus_percentage: Optional[float]
    avg_confidence: Optional[float]
    total_submissions: Optional[int]
    signal_type: Optional[str]


def save(
    today: date,
    actual_outcome: int,
    consensus_prediction: Optional[int],
    consensus_percentage: Optional[float],
    avg_confidence: Optional[float],
    total_submissions: Optional[int],
    signal_type: Optional[str],
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO results (date, actual_outcome, consensus_prediction, consensus_percentage, avg_confidence, total_submissions, signal_type)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(date) DO UPDATE SET actual_outcome=excluded.actual_outcome""",
            (today.isoformat(), actual_outcome, consensus_prediction, consensus_percentage, avg_confidence, total_submissions, signal_type)
        )


def get_all() -> list[Result]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM results ORDER BY date DESC").fetchall()
    return [Result(**dict(r)) for r in rows]


def get_for_date(today: date) -> Optional[Result]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM results WHERE date = ?", (today.isoformat(),)
        ).fetchone()
    return Result(**dict(row)) if row else None
