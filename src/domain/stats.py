from src.db.repositories import results, members
from src.db.connection import get_conn


def overall_accuracy() -> dict:
    all_results = results.get_all()
    signal_results = [
        r for r in all_results
        if r.consensus_prediction is not None and r.signal_type in ("HIGH", "MODERATE")
    ]
    if not signal_results:
        return {"total": 0, "correct": 0, "accuracy_pct": 0.0}

    correct = sum(1 for r in signal_results if r.consensus_prediction == r.actual_outcome)
    total = len(signal_results)
    return {
        "total": total,
        "correct": correct,
        "accuracy_pct": round(correct / total * 100, 1),
    }


def member_stats(member_id: int) -> dict:
    all_members = members.get_all()
    member = next((m for m in all_members if m.id == member_id), None)
    if not member:
        return {}

    with get_conn() as conn:
        broadcast_dates = {
            r["date"] for r in conn.execute("SELECT DISTINCT date FROM daily_aggregates").fetchall()
        }
        if member.joined_date:
            broadcast_dates = {d for d in broadcast_dates if d >= member.joined_date.isoformat()}
        total_trading_days = len(broadcast_dates)
        if total_trading_days == 0:
            return {
                "member_id": member_id,
                "username": member.username,
                "framework": member.framework,
                "submissions": 0,
                "total_days": 0,
                "attendance_pct": 0.0,
            }
        rows = conn.execute(
            "SELECT DISTINCT date FROM predictions WHERE member_id = ?", (member_id,)
        ).fetchall()

    submissions = len({r["date"] for r in rows} & broadcast_dates)
    attendance = round(submissions / total_trading_days * 100, 1)

    return {
        "member_id": member_id,
        "username": member.username,
        "framework": member.framework,
        "submissions": submissions,
        "total_days": total_trading_days,
        "attendance_pct": attendance,
    }
