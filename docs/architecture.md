# Architecture

Design notes for the Council of Wise Men bot: what each layer is responsible for, how the data model works, and which trade-offs were made deliberately.

---

## Layering

```
Discord  ──▶  bot/handlers  ──▶  db/repositories  ──▶  SQLite
                   │                    ▲
                   └──▶  domain/  ──────┘
                        (pure)
scheduler/jobs  ──▶  services/  ──▶  bot/  +  db/
```

**`src/domain/` is pure.** `aggregator`, `classifier` and (mostly) `stats` take dataclasses and return dataclasses or dicts. No Discord objects, no network, no ambient time. That is what makes the interesting rules — quorum, confidence gates, signal thresholds — testable in microseconds with no mocking.

**`src/db/repositories/` is the only code that writes SQL.** Each module owns one table and returns a dataclass, never a raw `sqlite3.Row`. Swapping SQLite for Postgres means rewriting these modules and nothing above them.

**`src/bot/handlers/` is thin on purpose.** A handler validates the caller, calls a repository, calls a domain function, and formats a reply. Anything longer than that belongs in `domain/` or `services/`.

**`src/scheduler/jobs.py` is the seam.** It is the one place where time, persistence, domain logic and Discord I/O meet, which makes it the natural place to look when something misbehaves at 09:29.

---

## Data model

| Table | Purpose | Notable constraint |
|---|---|---|
| `members` | Roster: Discord ID, display name, framework, recruiting source, join date, active flag. | `UNIQUE(discord_id)` |
| `predictions` | One vote per member per day: option 1–4 plus confidence 1–10. | `UNIQUE(date, member_id)` |
| `daily_aggregates` | The counted result of a day: per-option counts, average confidence, leading option and percentage, signal type, and whether it has been posted. | `UNIQUE(date)` |
| `results` | The actual outcome of a day, joined to the consensus that predicted it. | `UNIQUE(date)` |
| `skips` | Days the admin cancelled. | `UNIQUE(date)` |
| `broadcast_log` | Delivery receipts for the morning DM. | `UNIQUE(date, member_id)` |

Every table that represents "a fact about a day" is keyed on the date. That is what makes the whole pipeline replayable: running a job twice on the same date updates a row rather than appending a duplicate.

### Why votes are immutable

`UNIQUE(date, member_id)` on `predictions` is the load-bearing constraint of the entire project. If a member could change their vote after seeing the crowd lean, independence would be gone and the aggregate would measure conformity instead of judgement. The UI blocks a second submission, and the database refuses one — `predictions.save()` catches only `IntegrityError` and returns `False`, so a duplicate is reported to the user as "already locked in" while any *other* database error still surfaces to the global handler.

### Why removal is a soft delete

`/remove_member` flips `active = FALSE` and leaves the row. Deleting would orphan the member's prediction history and break the foreign keys in `predictions` and `broadcast_log`. Re-adding someone previously removed therefore has to be an UPSERT (`ON CONFLICT(discord_id) DO UPDATE`) rather than an INSERT — it reactivates the original row and preserves its ID, so the historical votes stay attached to the right person.

---

## Scheduling and time

Three cron jobs, all `day_of_week="mon-fri"`, all pinned to `America/New_York` at the trigger level rather than inherited from the process:

| Time (ET) | Job | Effect |
|---|---|---|
| 09:20 | `job_broadcast_question` | DM every active member the question with four buttons. |
| 09:29 | `job_post_consensus` | Aggregate, classify, persist, post the embed. |
| 11:00 | `job_session_end_reminder` | DM the admin to record the outcome, unless it's already recorded. |

The submission window closes at 09:28 — enforced by `services/session_state.is_submission_open()`, checked on both button callbacks, not just the first. A member who opened the confidence picker at 09:27:59 and taps at 09:28:30 is still rejected.

Every job carries `misfire_grace_time=60`: a job delayed by up to a minute (garbage collection, a slow event loop, a laptop waking up) still runs; one delayed longer is skipped rather than firing a broadcast into a window that has already closed.

`is_trading_day()` combines three checks — weekday, the hard-coded NYSE holiday set, and the `skips` table — so the admin can cancel a day without touching code. `TEST_MODE` bypasses all three, which is what makes a full end-to-end rehearsal possible on a weekend.

---

## Idempotency and failure modes

The bot self-hosts on a single machine, so it is assumed it will be restarted at inconvenient moments. Each job is safe to run more than once:

| Failure | What happens |
|---|---|
| Bot restarts mid-window | Persistent views are re-registered at startup with stable `custom_id`s (`pred:1`, `result:3`), so buttons in DMs sent *before* the restart still work. |
| Broadcast job runs twice | `broadcast_log` records a delivery receipt per member per day; the second run finds nobody undelivered and sends nothing. In `TEST_MODE` this filter is bypassed so a rehearsal can be repeated. |
| Consensus job runs twice | The `posted_to_group` flag on `daily_aggregates` short-circuits the second run before it posts. |
| A member has DMs closed | `discord.Forbidden` is caught per member and logged; the broadcast continues down the roster instead of dying on one bad recipient. |
| Slash command raises | The global `tree.error` handler replies to the caller and DMs the admin the exception. `on_error` does the same for event-loop exceptions. |
| Database write fails | `get_conn()` is a context manager that commits on success and rolls back on any exception, then re-raises. Partial writes are not possible. |
| `GROUP_CHANNEL_ID` unset | The consensus is still computed and persisted; only the post is skipped, with an error logged. The day's data is not lost. |

Deliveries are spaced by 50 ms to stay clear of Discord's DM rate limits.

---

## Deliberate trade-offs

**SQLite over Postgres.** One process, one machine, a few dozen writes per weekday. WAL mode plus foreign-key enforcement gives durability and integrity without operational overhead. The cost is a single-writer ceiling, accepted because the repository layer keeps the migration path short.

**Schema-file migrations over a migration framework.** `ensure_schema()` runs `schema.sql` (all `CREATE TABLE IF NOT EXISTS`) and then applies an explicit list of additive `ALTER TABLE ... ADD COLUMN` steps. Idempotent, dependency-free, and honest about its limits: it handles additions, not renames or drops. At this size, Alembic would be more machinery than the problem justifies.

**Confidence as a gate, not a weight.** Votes are counted equally; average confidence only decides whether the crowd gets to speak at all. Confidence-weighting would let a few loud, certain members dominate the aggregate — exactly the correlated-error failure mode the roster design exists to avoid.

**Accuracy measured on signal days only.** `stats.overall_accuracy()` filters to HIGH and MODERATE. Counting NO_SIGNAL days would let the bot inflate its record by declining to call anything difficult.

**Single admin.** One Discord ID in the environment, checked at the top of every privileged handler. A role-based check would be more flexible and would also mean a misconfigured role could hand a member the result-recording command.

---

## Where to look first

| Symptom | File |
|---|---|
| No DM went out this morning | `src/scheduler/jobs.py`, `src/services/broadcaster.py` |
| Buttons do nothing after a restart | `src/bot/client.py` (view registration), `src/bot/views.py` (`custom_id`s) |
| Signal looks wrong for the vote split | `src/domain/classifier.py`, `src/domain/aggregator.py` |
| Accuracy figure looks off | `src/domain/stats.py`, `src/bot/handlers/admin.py` (`handle_result`) |
| Fires at the wrong hour | `src/scheduler/runner.py`, `config.py` |
| Ran on a holiday | `src/scheduler/calendar.py` |
