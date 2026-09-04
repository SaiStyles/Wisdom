"""Scheduler jobs — the unattended cron path.

Covers cases 8, 9 (consensus to channel + idempotency), the bug #2 fan-out regression,
Case 18 Forbidden safety, and Case 19 broadcast_log dedupe — without needing live Discord.
Uses a FakeBot whose get_user/get_channel return recording stand-ins.
"""
import asyncio
from datetime import date
from types import SimpleNamespace
import discord
import config
import src.scheduler.jobs as jobs
from src.scheduler.jobs import (
    job_broadcast_question, job_post_consensus, job_session_end_reminder,
)
from src.db.connection import get_conn
from src.db.repositories import predictions, aggregates, results


def _run(coro):
    return asyncio.run(coro)


def _forbidden():
    return discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "DMs closed")


def _notfound():
    return discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "gone")


class _FakeUser:
    def __init__(self, fail_mode=None):
        self.sent = []
        self.fail_mode = fail_mode  # None | "forbidden" | "notfound" | "other"

    async def send(self, *args, **kwargs):
        if self.fail_mode == "forbidden":
            raise _forbidden()
        if self.fail_mode == "notfound":
            raise _notfound()
        if self.fail_mode == "other":
            raise RuntimeError("boom")
        self.sent.append((args, kwargs))


class _FakeChannel:
    def __init__(self):
        self.sent_embeds = []

    async def send(self, *args, **kwargs):
        self.sent_embeds.append(kwargs.get("embed"))


class _FakeBot:
    def __init__(self, default_user=None, channel=None):
        self._default_user = default_user or _FakeUser()
        self._channel = channel or _FakeChannel()

    def get_user(self, uid):
        return self._default_user

    async def fetch_user(self, uid):
        return self._default_user

    def get_channel(self, cid):
        return self._channel

    async def fetch_channel(self, cid):
        return self._channel


def _seed_active_members(n: int) -> list[int]:
    ids = []
    with get_conn() as conn:
        for i in range(1, n + 1):
            cur = conn.execute(
                "INSERT INTO members (discord_id, username, framework, source, joined_date, active) "
                "VALUES (?, ?, 'ICT', 'test', date('now'), 1)",
                (f"9900{i}", f"u{i}"),
            )
            ids.append(cur.lastrowid)
    return ids


# ---------- job_broadcast_question ----------

def test_broadcast_skips_on_weekend(db, monkeypatch):
    monkeypatch.setattr(jobs, "today_et", lambda: date(2026, 4, 25))  # Saturday
    monkeypatch.setattr(config, "TEST_MODE", False)
    _seed_active_members(3)
    bot = _FakeBot()
    _run(job_broadcast_question(bot))
    assert bot._default_user.sent == []
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM broadcast_log").fetchall()
    assert rows == []


def test_broadcast_skips_when_skip_row_exists(db, monkeypatch):
    today = date(2026, 4, 23)  # Thursday
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    monkeypatch.setattr(config, "TEST_MODE", False)
    with get_conn() as conn:
        conn.execute("INSERT INTO skips (date, reason) VALUES (?, 'admin')", (today.isoformat(),))
    _seed_active_members(3)
    bot = _FakeBot()
    _run(job_broadcast_question(bot))
    assert bot._default_user.sent == []


def test_broadcast_delivers_to_each_active_member(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    monkeypatch.setattr(config, "TEST_MODE", True)  # bypass broadcast_log filter
    member_ids = _seed_active_members(5)
    bot = _FakeBot()
    _run(job_broadcast_question(bot))
    assert len(bot._default_user.sent) == 5
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT member_id FROM broadcast_log WHERE date = ? AND delivered = 1",
            (today.isoformat(),)
        ).fetchall()
    assert {r["member_id"] for r in rows} == set(member_ids)


# Case 19 regression — dedupe via broadcast_log when NOT in TEST_MODE
def test_broadcast_log_prevents_redelivery_when_not_test_mode(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    monkeypatch.setattr(config, "TEST_MODE", False)
    _seed_active_members(3)
    bot1 = _FakeBot()
    _run(job_broadcast_question(bot1))
    assert len(bot1._default_user.sent) == 3
    bot2 = _FakeBot()
    _run(job_broadcast_question(bot2))
    assert bot2._default_user.sent == []


# Case 18 regression — Forbidden on one member must not block others or crash
def test_broadcast_forbidden_does_not_crash_or_log_delivery(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    monkeypatch.setattr(config, "TEST_MODE", True)
    _seed_active_members(3)
    bot = _FakeBot(default_user=_FakeUser(fail_mode="forbidden"))
    _run(job_broadcast_question(bot))  # must not raise
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM broadcast_log").fetchall()
    assert rows == []  # failed delivery does NOT mark as delivered


def test_broadcast_notfound_does_not_crash(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    monkeypatch.setattr(config, "TEST_MODE", True)
    _seed_active_members(2)
    bot = _FakeBot(default_user=_FakeUser(fail_mode="notfound"))
    _run(job_broadcast_question(bot))  # must not raise


# ---------- job_post_consensus ----------

def test_consensus_skips_on_non_trading_day(db, monkeypatch):
    monkeypatch.setattr(jobs, "today_et", lambda: date(2026, 4, 25))  # Saturday
    monkeypatch.setattr(config, "TEST_MODE", False)
    bot = _FakeBot()
    _run(job_post_consensus(bot))
    assert bot._channel.sent_embeds == []
    # No aggregate row created either
    assert aggregates.get_for_date(date(2026, 4, 25)) is None


# Bug #2 regression — embed goes to channel, not DM fan-out
def test_consensus_posts_embed_to_channel_not_dm(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    member_ids = _seed_active_members(10)
    for mid in member_ids[:7]:
        predictions.save(mid, 1, 8, today)
    for mid in member_ids[7:]:
        predictions.save(mid, 2, 7, today)
    bot = _FakeBot()
    _run(job_post_consensus(bot))
    assert len(bot._channel.sent_embeds) == 1
    assert bot._default_user.sent == []  # NEVER DM the members individually
    assert isinstance(bot._channel.sent_embeds[0], discord.Embed)


def test_consensus_saves_aggregate_with_signal(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    member_ids = _seed_active_members(10)
    # 7 Up conf 8, 3 Up conf 7 → 100% Up, avg 7.7 → HIGH
    for mid in member_ids[:7]:
        predictions.save(mid, 1, 8, today)
    for mid in member_ids[7:]:
        predictions.save(mid, 1, 7, today)
    bot = _FakeBot()
    _run(job_post_consensus(bot))
    a = aggregates.get_for_date(today)
    assert a is not None
    assert a.signal_type == "HIGH"
    assert a.leading_option == 1
    assert a.leading_pct == 100.0
    assert a.posted_to_group == 1


# Case 9 — idempotent
def test_consensus_idempotent_on_second_run(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    member_ids = _seed_active_members(10)
    for mid in member_ids:
        predictions.save(mid, 1, 7, today)
    bot = _FakeBot()
    _run(job_post_consensus(bot))
    assert len(bot._channel.sent_embeds) == 1
    _run(job_post_consensus(bot))
    assert len(bot._channel.sent_embeds) == 1  # still 1 — no double-post


def test_consensus_low_turnout_classified_no_signal(db, monkeypatch):
    """4 submissions on 10-member roster → NO_SIGNAL (dynamic quorum, bug #5)."""
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    member_ids = _seed_active_members(10)
    for mid in member_ids[:4]:
        predictions.save(mid, 1, 9, today)
    bot = _FakeBot()
    _run(job_post_consensus(bot))
    a = aggregates.get_for_date(today)
    assert a.signal_type == "NO_SIGNAL"
    # Still posted (NO_SIGNAL embed is a valid post)
    assert a.posted_to_group == 1
    assert len(bot._channel.sent_embeds) == 1


def test_consensus_missing_group_channel_id_does_not_crash(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    monkeypatch.setattr(config, "GROUP_CHANNEL_ID", None)
    member_ids = _seed_active_members(10)
    for mid in member_ids:
        predictions.save(mid, 1, 7, today)
    bot = _FakeBot()
    _run(job_post_consensus(bot))  # must not raise
    assert bot._channel.sent_embeds == []
    # Aggregate was saved with signal, but NOT marked posted
    a = aggregates.get_for_date(today)
    assert a is not None
    assert a.posted_to_group == 0


# ---------- job_session_end_reminder ----------

def test_reminder_skips_non_trading_day(db, monkeypatch):
    monkeypatch.setattr(jobs, "today_et", lambda: date(2026, 4, 25))
    monkeypatch.setattr(config, "TEST_MODE", False)
    bot = _FakeBot()
    _run(job_session_end_reminder(bot))
    assert bot._default_user.sent == []


def test_reminder_skips_if_result_already_recorded(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    results.save(today, 1, 1, 70.0, 7.0, 10, "HIGH")
    bot = _FakeBot()
    _run(job_session_end_reminder(bot))
    assert bot._default_user.sent == []


def test_reminder_dms_admin_when_no_result_yet(db, monkeypatch):
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    bot = _FakeBot()
    _run(job_session_end_reminder(bot))
    assert len(bot._default_user.sent) == 1
    args, _ = bot._default_user.sent[0]
    assert "add_result" in args[0]


def test_reminder_swallows_dm_failure(db, monkeypatch):
    """Scheduler must not die if admin has DMs off."""
    today = date(2026, 4, 23)
    monkeypatch.setattr(jobs, "today_et", lambda: today)
    bot = _FakeBot(default_user=_FakeUser(fail_mode="other"))
    _run(job_session_end_reminder(bot))  # must not raise
