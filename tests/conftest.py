import os
import sys

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_DISCORD_ID", "1")
os.environ.setdefault("GUILD_ID", "1")
os.environ.setdefault("GROUP_CHANNEL_ID", "1")
os.environ.setdefault("TEST_MODE", "true")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import config
from src.db.migrations import ensure_schema
from src.db.connection import get_conn


@pytest.fixture
def db(tmp_path, monkeypatch):
    db_file = tmp_path / "council.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_file))
    ensure_schema()
    yield str(db_file)


@pytest.fixture
def seeded_members(db):
    """Insert 10 active members. Returns list of member row ids."""
    ids = []
    with get_conn() as conn:
        for i in range(1, 11):
            cur = conn.execute(
                "INSERT INTO members (discord_id, username, framework, source, joined_date, active) "
                "VALUES (?, ?, 'ICT', 'test', date('now'), 1)",
                (f"t{i}", f"u{i}"),
            )
            ids.append(cur.lastrowid)
    return ids
