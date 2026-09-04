"""Aggregator — pure list-of-Predictions → Aggregate math."""
from datetime import date, datetime
from src.db.repositories.predictions import Prediction
from src.domain.aggregator import aggregate


def _pred(option, conf, member_id=1):
    return Prediction(
        id=member_id, date=date.today(), member_id=member_id,
        prediction=option, confidence=conf, submitted_at=datetime.utcnow(),
    )


def test_empty_returns_zeroed_aggregate():
    agg = aggregate([])
    assert agg.total == 0
    assert agg.leading_option == 0
    assert agg.leading_pct == 0.0
    assert agg.avg_confidence == 0.0


def test_single_prediction_is_100pct_leader():
    agg = aggregate([_pred(1, 7)])
    assert agg.total == 1
    assert agg.leading_option == 1
    assert agg.leading_pct == 100.0
    assert agg.avg_confidence == 7.0
    assert agg.up == 1


def test_counts_and_pcts():
    preds = (
        [_pred(1, 8)] * 7 +   # 7 Up conf 8
        [_pred(2, 7)] * 2 +   # 2 Down conf 7
        [_pred(4, 7)] * 1     # 1 Range conf 7
    )
    agg = aggregate(preds)
    assert agg.total == 10
    assert agg.up == 7 and agg.down == 2 and agg.both == 0 and agg.range_ == 1
    assert agg.up_pct == 70.0
    assert agg.down_pct == 20.0
    assert agg.range_pct == 10.0
    assert agg.leading_option == 1
    assert agg.leading_pct == 70.0
    assert agg.avg_confidence == 7.7  # (7*8 + 2*7 + 7) / 10 = 77/10


def test_tie_picks_lowest_option_id():
    # Python max() with key=counts.get returns first key with max count
    preds = [_pred(1, 5), _pred(2, 5)]
    agg = aggregate(preds)
    assert agg.leading_option == 1  # option 1 wins ties (dict iteration order)
    assert agg.leading_pct == 50.0
