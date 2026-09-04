from dataclasses import dataclass
from datetime import date
from typing import Optional
from src.db.connection import get_conn


@dataclass
class Member:
    id: int
    discord_id: str
    username: Optional[str]
    framework: Optional[str]
    source: Optional[str]
    joined_date: Optional[date]
    active: bool


def get_by_discord_id(discord_id: str) -> Optional[Member]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM members WHERE discord_id = ? AND active = TRUE",
            (str(discord_id),)
        ).fetchone()
    if row is None:
        return None
    return Member(**dict(row))


def get_all_active() -> list[Member]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM members WHERE active = TRUE"
        ).fetchall()
    return [Member(**dict(r)) for r in rows]


def add(discord_id: str, username: str, framework: str, source: str) -> None:
    """Add a new member, or reactivate + refresh fields if the discord_id already exists.

    We UPSERT instead of plain INSERT so that `/remove_member` (which only flips
    active=FALSE) followed by `/add_member` works without hitting UNIQUE. Preserves
    the row's id so foreign-key references in predictions/broadcast_log stay intact.
    """
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO members (discord_id, username, framework, source, joined_date, active)
               VALUES (?, ?, ?, ?, ?, TRUE)
               ON CONFLICT(discord_id) DO UPDATE SET
                 username=excluded.username,
                 framework=excluded.framework,
                 source=excluded.source,
                 active=TRUE""",
            (str(discord_id), username, framework, source, date.today().isoformat())
        )


def deactivate(discord_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE members SET active = FALSE WHERE discord_id = ?",
            (str(discord_id),)
        )


def get_all() -> list[Member]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM members").fetchall()
    return [Member(**dict(r)) for r in rows]
