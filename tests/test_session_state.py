"""session_state.is_submission_open — case 17 time gate + test-mode bypass."""
from datetime import datetime
import config
import src.services.session_state as ss
from src.db.connection import get_conn


def _freeze(dt_naive: datetime):
    """Return a stand-in for session_state.datetime whose .now(tz) returns dt localized to tz."""
    class _FakeDT:
        @staticmethod
        def now(tz):
            return dt_naive.replace(tzinfo=tz)
    return _FakeDT


def test_test_mode_always_open(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", True)
    # Sunday 3am — would be closed in prod, but TEST_MODE should short-circuit.
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 26, 3, 0)))
    assert ss.is_submission_open() is True


def test_weekend_closed(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    # 2026-04-25 Saturday, 9:25 ET
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 25, 9, 25)))
    assert ss.is_submission_open() is False


def test_holiday_closed(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    # 2026-01-01 New Year (Thursday, NYSE holiday), during window
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 1, 1, 9, 25)))
    assert ss.is_submission_open() is False


def test_before_broadcast_closed(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    # 2026-04-23 Thursday, 9:19 < 9:20 broadcast start
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 23, 9, 19)))
    assert ss.is_submission_open() is False


def test_after_cutoff_closed(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    # 2026-04-23 Thursday, 9:29 > 9:28 cutoff
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 23, 9, 29)))
    assert ss.is_submission_open() is False


def test_during_window_open(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    # 2026-04-23 Thursday, 9:25 — inside [9:20, 9:28]
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 23, 9, 25)))
    assert ss.is_submission_open() is True


def test_broadcast_boundary_open(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 23, 9, 20)))
    assert ss.is_submission_open() is True


def test_cutoff_boundary_open(db, monkeypatch):
    monkeypatch.setattr(config, "TEST_MODE", False)
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 23, 9, 28)))
    assert ss.is_submission_open() is True


def test_skip_closes_even_during_window(db, monkeypatch):
    """Case 15 × 17: a skip row overrides the time-window check."""
    monkeypatch.setattr(config, "TEST_MODE", False)
    monkeypatch.setattr(ss, "datetime", _freeze(datetime(2026, 4, 23, 9, 25)))
    with get_conn() as conn:
        conn.execute("INSERT INTO skips (date, reason) VALUES ('2026-04-23', 'admin skip')")
    assert ss.is_submission_open() is False
