from src.domain.aggregator import Aggregate


def classify(agg: Aggregate, active_roster_size: int) -> str:
    """Classify aggregate into HIGH / MODERATE / NO_SIGNAL.

    active_roster_size: number of active members at classification time.
    Turnout under 50% of the roster forces NO_SIGNAL per spec.
    """
    if active_roster_size <= 0:
        return "NO_SIGNAL"
    turnout_pct = agg.total / active_roster_size
    if turnout_pct < 0.5:
        return "NO_SIGNAL"
    if agg.avg_confidence < 5:
        return "NO_SIGNAL"
    if agg.leading_pct >= 60 and agg.avg_confidence >= 7:
        return "HIGH"
    if agg.leading_pct >= 50:
        return "MODERATE"
    return "NO_SIGNAL"
