"""members repo — add/deactivate/re-add flow."""
from src.db.repositories import members
from src.db.connection import get_conn


def test_add_new_member(db):
    members.add("100", "alice", "ICT", "twitter")
    m = members.get_by_discord_id("100")
    assert m is not None
    assert m.username == "alice"
    assert m.active == 1


def test_deactivate_hides_from_get_by_discord_id(db):
    members.add("200", "bob", "SMC", "friend")
    members.deactivate("200")
    assert members.get_by_discord_id("200") is None  # filter: active=TRUE


def test_deactivate_keeps_row_in_db(db):
    """Row survives deactivate — we only flip active=FALSE."""
    members.add("200", "bob", "SMC", "friend")
    members.deactivate("200")
    with get_conn() as conn:
        rows = conn.execute("SELECT discord_id, active FROM members").fetchall()
    assert len(rows) == 1
    assert rows[0]["active"] == 0


# Regression — the UNIQUE-constraint bug you hit trying to re-add yourself
def test_readd_after_deactivate_reactivates_in_place(db):
    members.add("300", "carl", "ICT", "self")
    original_id = members.get_by_discord_id("300").id
    members.deactivate("300")
    # Before the fix this would raise sqlite3.IntegrityError: UNIQUE constraint failed.
    members.add("300", "carl_v2", "SMC", "x")
    m = members.get_by_discord_id("300")
    assert m is not None
    assert m.id == original_id  # same row, foreign keys intact
    assert m.username == "carl_v2"  # fields refreshed
    assert m.framework == "SMC"
    assert m.source == "x"
    assert m.active == 1


def test_add_existing_active_member_refreshes_fields(db):
    """Re-adding an already-active member updates fields rather than erroring."""
    members.add("400", "dan", "ICT", "self")
    members.add("400", "dan_renamed", "SMC", "referral")
    m = members.get_by_discord_id("400")
    assert m.username == "dan_renamed"
    assert m.framework == "SMC"
    # Only one row, not two
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM members WHERE discord_id='400'").fetchone()[0]
    assert count == 1


def test_get_all_includes_inactive(db):
    members.add("500", "eve", "ICT", "self")
    members.add("501", "fran", "SMC", "self")
    members.deactivate("500")
    assert len(members.get_all()) == 2
    assert len(members.get_all_active()) == 1
