"""daily_aggregates repo — UPSERT + new columns (bug #6)."""
from datetime import date
from src.db.repositories import aggregates


def test_save_persists_leading_and_signal(db):
    today = date.today()
    aggregates.save(today, up=7, down=2, both=0, range_=1,
                    avg_confidence=7.7, total=10,
                    leading_option=1, leading_pct=70.0, signal_type="HIGH")
    a = aggregates.get_for_date(today)
    assert a is not None
    assert a.leading_option == 1
    assert a.leading_pct == 70.0
    assert a.signal_type == "HIGH"
    assert a.posted_to_group == 0


def test_upsert_updates_in_place(db):
    today = date.today()
    aggregates.save(today, 5, 3, 2, 0, 6.0, 10, 1, 50.0, "MODERATE")
    aggregates.save(today, 7, 2, 1, 0, 7.5, 10, 1, 70.0, "HIGH")
    a = aggregates.get_for_date(today)
    assert a.expansion_up_count == 7
    assert a.signal_type == "HIGH"
    assert a.leading_pct == 70.0


def test_mark_posted_flips_flag(db):
    today = date.today()
    aggregates.save(today, 1, 0, 0, 0, 7.0, 1, 1, 100.0, "NO_SIGNAL")
    aggregates.mark_posted(today)
    a = aggregates.get_for_date(today)
    assert a.posted_to_group == 1


def test_get_for_date_missing_returns_none(db):
    assert aggregates.get_for_date(date.today()) is None
