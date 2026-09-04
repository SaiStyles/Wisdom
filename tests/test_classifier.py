"""Classifier rules — pure logic, no DB."""
from src.domain.aggregator import Aggregate
from src.domain.classifier import classify


def _agg(total, leading_pct, avg_conf, leading_option=1):
    return Aggregate(
        up=total, down=0, both=0, range_=0, total=total,
        avg_confidence=avg_conf,
        up_pct=leading_pct, down_pct=0.0, both_pct=0.0, range_pct=0.0,
        leading_option=leading_option, leading_pct=leading_pct,
    )


# Case 20a
def test_high_conviction():
    assert classify(_agg(total=10, leading_pct=70.0, avg_conf=7.7), 10) == "HIGH"


# Case 20b
def test_moderate_at_50pct():
    assert classify(_agg(total=10, leading_pct=50.0, avg_conf=6.0), 10) == "MODERATE"


# Case 20c — regression bug #3
def test_no_signal_low_confidence_overrides_high_pct():
    assert classify(_agg(total=10, leading_pct=70.0, avg_conf=3.0), 10) == "NO_SIGNAL"


# Case 20d — regression bug #5 (dynamic quorum)
def test_no_signal_low_turnout():
    assert classify(_agg(total=4, leading_pct=100.0, avg_conf=9.0), 10) == "NO_SIGNAL"


def test_turnout_exactly_50pct_passes_quorum():
    assert classify(_agg(total=5, leading_pct=60.0, avg_conf=7.0), 10) == "HIGH"


def test_high_requires_both_pct_and_conf():
    # 60% leading but conf=6 → MODERATE, not HIGH
    assert classify(_agg(total=10, leading_pct=60.0, avg_conf=6.0), 10) == "MODERATE"


def test_empty_roster_returns_no_signal():
    assert classify(_agg(total=0, leading_pct=0.0, avg_conf=0.0), 0) == "NO_SIGNAL"


def test_avg_conf_4_9_gates_to_no_signal():
    # Just under the avg_conf<5 boundary
    assert classify(_agg(total=10, leading_pct=80.0, avg_conf=4.9), 10) == "NO_SIGNAL"


def test_high_boundary_60pct_conf_7():
    assert classify(_agg(total=10, leading_pct=60.0, avg_conf=7.0), 10) == "HIGH"


# Regression: split vote with mid-range confidence must NOT slip into MODERATE.
# Previously the OR-clause `leading_pct>=50 OR avg_conf<7` let leading_pct=25%
# pass as MODERATE just because confidence was 6.
def test_split_vote_with_mid_confidence_is_no_signal():
    assert classify(_agg(total=10, leading_pct=25.0, avg_conf=6.0), 10) == "NO_SIGNAL"


def test_leading_pct_just_under_50_is_no_signal():
    assert classify(_agg(total=10, leading_pct=49.9, avg_conf=8.0), 10) == "NO_SIGNAL"
