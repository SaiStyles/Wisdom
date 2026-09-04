"""predictions repo — save, idempotency, TIMESTAMP round-trip (bug #4)."""
from datetime import date, datetime
from src.db.repositories import predictions
from src.db.connection import get_conn


def test_save_and_has_submitted(seeded_members):
    mid = seeded_members[0]
    today = date.today()
    assert predictions.has_submitted(mid, today) is False
    assert predictions.save(mid, 1, 7, today) is True
    assert predictions.has_submitted(mid, today) is True


# Case 21 — regression bug #4
def test_timestamp_roundtrip_via_parse_decltypes(seeded_members):
    mid = seeded_members[0]
    today = date.today()
    predictions.save(mid, 2, 8, today)
    rows = predictions.get_for_date(today)
    assert len(rows) == 1
    assert isinstance(rows[0].submitted_at, datetime)
    assert isinstance(rows[0].date, date)


# Case 6 — UNIQUE(date, member_id)
def test_duplicate_submission_rejected_by_unique_constraint(seeded_members):
    mid = seeded_members[0]
    today = date.today()
    assert predictions.save(mid, 1, 7, today) is True
    assert predictions.save(mid, 2, 9, today) is False  # UNIQUE violation → returns False
    rows = predictions.get_for_date(today)
    assert len(rows) == 1
    assert rows[0].prediction == 1
    assert rows[0].confidence == 7


def test_get_for_date_scopes_to_day(seeded_members):
    mid1, mid2 = seeded_members[0], seeded_members[1]
    today = date.today()
    predictions.save(mid1, 1, 7, today)
    predictions.save(mid2, 2, 8, today)
    rows = predictions.get_for_date(today)
    assert len(rows) == 2
    assert {r.prediction for r in rows} == {1, 2}


def test_different_members_can_both_submit_same_day(seeded_members):
    today = date.today()
    for mid in seeded_members[:5]:
        assert predictions.save(mid, 1, 6, today) is True
    assert len(predictions.get_for_date(today)) == 5
