"""results repo — UPSERT re-entrant (case 12) + persisted signal_type (bug #7)."""
from datetime import date
from src.db.repositories import results


def test_save_and_fetch(db):
    today = date.today()
    results.save(today, actual_outcome=1, consensus_prediction=1,
                 consensus_percentage=70.0, avg_confidence=7.5,
                 total_submissions=10, signal_type="HIGH")
    r = results.get_for_date(today)
    assert r is not None
    assert r.actual_outcome == 1
    assert r.consensus_prediction == 1
    assert r.signal_type == "HIGH"


# Case 12 — /add_result re-entrant
def test_upsert_overwrites_outcome_no_unique_error(db):
    today = date.today()
    results.save(today, 1, 1, 60.0, 7.0, 10, "MODERATE")
    results.save(today, 2, 1, 60.0, 7.0, 10, "MODERATE")  # flip outcome
    r = results.get_for_date(today)
    assert r.actual_outcome == 2
    assert len(results.get_all()) == 1


# Case 14 — bug #7 (signal_type persisted, not null)
def test_signal_type_persisted_not_null(db):
    today = date.today()
    results.save(today, 1, 1, 60.0, 7.0, 10, "NO_SIGNAL")
    r = results.get_for_date(today)
    assert r.signal_type == "NO_SIGNAL"


def test_consensus_prediction_is_integer_option_not_date(db):
    """Case 11 / bug #1 — consensus_prediction must be int 1-4, not the date string."""
    today = date.today()
    results.save(today, 1, 3, 50.0, 6.0, 8, "MODERATE")
    r = results.get_for_date(today)
    assert isinstance(r.consensus_prediction, int)
    assert 1 <= r.consensus_prediction <= 4


def test_get_for_date_missing_returns_none(db):
    assert results.get_for_date(date.today()) is None
