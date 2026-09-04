"""stats.overall_accuracy — case 11 (bug #1 regression) + case 12."""
from datetime import date, timedelta
from src.db.repositories import results
from src.domain.stats import overall_accuracy


def test_empty_results_zero_accuracy(db):
    s = overall_accuracy()
    assert s == {"total": 0, "correct": 0, "accuracy_pct": 0.0}


# Case 11 — bug #1: if consensus_prediction stored as date this assert fails.
def test_perfect_accuracy(db):
    today = date.today()
    results.save(today, actual_outcome=1, consensus_prediction=1,
                 consensus_percentage=70.0, avg_confidence=7.5,
                 total_submissions=10, signal_type="HIGH")
    s = overall_accuracy()
    assert s["total"] == 1
    assert s["correct"] == 1
    assert s["accuracy_pct"] == 100.0


# Case 12 — flipping outcome to not-match yields 0%
def test_zero_accuracy_when_outcome_differs(db):
    today = date.today()
    results.save(today, actual_outcome=2, consensus_prediction=1,
                 consensus_percentage=60.0, avg_confidence=7.0,
                 total_submissions=10, signal_type="MODERATE")
    s = overall_accuracy()
    assert s["total"] == 1
    assert s["correct"] == 0
    assert s["accuracy_pct"] == 0.0


def test_mixed_accuracy_over_multiple_days(db):
    d1 = date.today()
    d2 = d1 - timedelta(days=1)
    d3 = d1 - timedelta(days=2)
    results.save(d1, 1, 1, 70.0, 7.0, 10, "HIGH")       # correct
    results.save(d2, 2, 1, 60.0, 7.0, 10, "MODERATE")   # wrong
    results.save(d3, 4, 4, 80.0, 8.0, 10, "HIGH")       # correct
    s = overall_accuracy()
    assert s["total"] == 3
    assert s["correct"] == 2
    assert s["accuracy_pct"] == 66.7


def test_null_consensus_not_counted_correct(db):
    """If consensus_prediction is NULL (e.g. from skip), it must not count as correct
    even if actual_outcome happens to be 0/falsy."""
    today = date.today()
    results.save(today, actual_outcome=1, consensus_prediction=None,
                 consensus_percentage=None, avg_confidence=None,
                 total_submissions=None, signal_type="NO_SIGNAL")
    s = overall_accuracy()
    assert s["correct"] == 0
