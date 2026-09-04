from dataclasses import dataclass
from src.db.repositories.predictions import Prediction


@dataclass
class Aggregate:
    up: int
    down: int
    both: int
    range_: int
    total: int
    avg_confidence: float
    up_pct: float
    down_pct: float
    both_pct: float
    range_pct: float
    leading_option: int
    leading_pct: float


def aggregate(predictions: list[Prediction]) -> Aggregate:
    if not predictions:
        return Aggregate(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0)

    counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for p in predictions:
        counts[p.prediction] += 1

    total = len(predictions)
    avg_conf = sum(p.confidence for p in predictions) / total

    pcts = {k: round(v / total * 100, 1) for k, v in counts.items()}
    leading = max(counts, key=counts.get)

    return Aggregate(
        up=counts[1],
        down=counts[2],
        both=counts[3],
        range_=counts[4],
        total=total,
        avg_confidence=round(avg_conf, 1),
        up_pct=pcts[1],
        down_pct=pcts[2],
        both_pct=pcts[3],
        range_pct=pcts[4],
        leading_option=leading,
        leading_pct=pcts[leading],
    )
