# Testing

Two layers: an automated suite that covers everything reachable without Discord, and a short manual script for the parts that need a live client and a human with a mouse.

---

## Automated suite

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

**72 tests, roughly three seconds.** No network, no Discord connection, no fixtures shared between tests — each one gets a fresh SQLite file in a `tmp_path`, so the suite is order-independent and leaves nothing on disk.

| File | Covers |
|---|---|
| `test_classifier.py` | Every branch of the signal rules, including the turnout gate, the confidence floor and the boundary values at 50/60% and confidence 5/7. |
| `test_aggregator.py` | Counts, percentages, average confidence, the leading option, and the empty-input case. |
| `test_stats.py` | Accuracy over signal days only; per-member attendance from the join date forward. |
| `test_predictions_repo.py` | Insert, duplicate rejection via `UNIQUE(date, member_id)`, timestamp round-trip. |
| `test_members_repo.py` | Add, soft delete, and the reactivating UPSERT that preserves the row ID. |
| `test_results_repo.py` | Insert and re-entrant update of a day's outcome. |
| `test_aggregates_repo.py` | Save, update-on-conflict, and the `posted_to_group` flag. |
| `test_calendar.py` | Weekends, NYSE holidays, and admin skips. |
| `test_session_state.py` | The submission window boundaries and the `TEST_MODE` bypass. |
| `test_scheduler_jobs.py` | Broadcast delivery against a stub bot, delivery-log deduplication, the trading-day gate, and consensus idempotency. |

The scheduler tests use a stub bot object rather than a mocked Discord client, which keeps them fast and free of library-version coupling.

---

## Manual script

Only needed after changes to the Discord surface — views, handlers, DM delivery, embed rendering. Run with `TEST_MODE=true`, the bot in your guild with access to the consensus channel, and yourself on the roster.

**Preflight**

- `.env` filled in, `TEST_MODE=true`.
- Developer Portal: **Server Members Intent** ON (the `discord.User` picker needs it).
- Bot invited with `bot` + `applications.commands`, and *Send Messages* / *Embed Links* / *Read Message History*.
- Startup log shows `DB schema ready.` → `Synced 12 slash commands to guild ...` → `Scheduler started.` (12 rather than 9 because `TEST_MODE` adds the three `/test_*` commands.)

**1. Liveness.** Run `/status`. On the roster: an ephemeral submission status. Off it: an ephemeral prompt to contact the admin.

**2. Onboarding.** `/add_member user:@you framework:ICT source:personal`. The `user` field must render as a user picker, not a text box. Expect an ephemeral confirmation *and* a DM containing the full welcome brief. `/welcome` should then return that same brief plus today's status.

**3. Authorisation.** From a second, non-admin account: `/stats`, `/add_member`, `/export`, `/add_result`, `/skip_today`. Each should reply `⛔ Admin only.` with nothing in the logs.

**4. Broadcast.** `/test_broadcast`. The question arrives as a **DM**, never in a channel, with four prediction buttons.

**5. Submission flow.** Tap *📈 Expansion Up* — the message should switch to a 1–10 confidence picker. Tap *7* — expect `✅ Locked in: Expansion Up — Confidence 7/10`.

**6. Immutability.** Tap a prediction button again on the original DM. Expect `✅ Already locked in. No changes.` — the database constraint doing its job through the UI.

**7. Status reflects it.** `/status` now reports submitted.

**8. Consensus.** `/test_consensus`. An **embed** appears in the consensus channel — one channel post, never a DM fan-out. Fields: four option counts with percentages, average confidence, submissions over roster size, and a colour matching the signal.

**9. Idempotency.** Run `/test_consensus` again. Nothing new should be posted.

**10. Recording the outcome.** `/add_result`, then tap an outcome. Expect `✅ Outcome recorded: <label>`. Re-run it and pick a different outcome — it should overwrite rather than error.

**11. Statistics.** `/stats` shows a real accuracy figure (not a permanent 0%). `/member_stats` lists per-member attendance and leaks no individual votes.

**12. Export.** `/export` returns a CSV attachment whose `signal_type` and `consensus_prediction` columns are populated.

**13. Restart recovery.** With a question DM still open, stop and restart the bot, then tap a button in that old DM. It should still work — persistent views re-registered with stable `custom_id`s.

**14. Error reporting.** Trigger a handler exception (for example, point `GROUP_CHANNEL_ID` at a channel the bot can't see and fire the consensus job). The admin should receive a DM containing the exception type.

**15. Cleanup.** `/test_reset` clears today's predictions, aggregates, results, skips and delivery log.

---

## Red flags

- A consensus arriving as a DM to every member instead of one channel post.
- Any message, anywhere, that reveals who voted for what.
- A submission accepted after 09:28 ET with `TEST_MODE=false`.
- `/stats` stuck at 0% — historically the symptom of the wrong column being written on `/add_result`.
- A second `/test_broadcast` in production mode re-sending DMs to members already delivered.
