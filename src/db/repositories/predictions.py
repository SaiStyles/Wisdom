import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional
from src.db.connection import get_conn


@dataclass
class Prediction:
    id: int
    date: date
    member_id: int
    prediction: int
    confidence: int
    submitted_at: datetime


def save(member_id: int, prediction: int, confidence: int, today: date) -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO predictions (date, member_id, prediction, confidence, submitted_at) VALUES (?, ?, ?, ?, ?)",
                (today.isoformat(), member_id, prediction, confidence, datetime.now(timezone.utc))
            )
        return True
    except sqlite3.IntegrityError:
        return False


def has_submitted(member_id: int, today: date) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM predictions WHERE date = ? AND member_id = ?",
            (today.isoformat(), member_id)
        ).fetchone()
    return row is not None


def get_for_date(today: date) -> list[Prediction]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE date = ?",
            (today.isoformat(),)
        ).fetchall()
    return [Prediction(**dict(r)) for r in rows]
