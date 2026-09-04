# Deployment

The bot is a **worker process**, not a web service. It opens no port and serves no requests — it holds a Discord gateway connection and runs three cron jobs. Anything that can keep a Python process alive will host it.

The only hard requirement: **it must be running at 09:20 ET on weekdays.** A process that is asleep at 09:20 loses that day entirely — the misfire grace period is sixty seconds, deliberately, because a broadcast that fires after the 09:28 cutoff is worse than no broadcast at all.

---

## What the repo already provides

| File | For |
|---|---|
| `Procfile` | Procfile-aware hosts — declares `worker: python main.py` so no HTTP port is expected. |
| `runtime.txt` | Pins Python 3.12 for hosts that read it. |
| `requirements.txt` | The install target. |
| `run.bat` | Windows self-host launcher with a 10-second auto-restart loop. |
| `deploy/council-bot.service` | systemd unit for a Linux box: restart on failure, filesystem hardening, journal logging. |
| `deploy/update.sh` | Pull, reinstall, restart, tail the logs. |

---

## Option 1 — self-host on a machine you own

The simplest arrangement, and the one this project ran on: a PC that is already switched on during market hours.

```bat
run.bat
```

The script `cd`s to its own directory, runs `python main.py`, and relaunches after ten seconds if the process dies. Network drops don't need it — discord.py reconnects on its own — but crashes and reboots do.

Two things to get right:

- **Sleep settings.** Settings → System → Power → set *Sleep* to *Never*, at least on AC. A sleeping machine fires nothing.
- **Start on login (optional).** Win+R → `shell:startup`, and drop a shortcut to `run.bat` in the folder that opens.

Trade-off: the database persists naturally and costs nothing, but uptime is exactly as reliable as the machine and its internet connection.

---

## Option 2 — a small Linux server

Any VPS or always-on Linux box, using the supplied systemd unit.

```bash
git clone https://github.com/SaiStyles/Wisdom.git ~/Wisdom
cd ~/Wisdom
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && $EDITOR .env

sed -e "s|__USER__|$USER|g" -e "s|__HOME__|$HOME|g" \
    deploy/council-bot.service | sudo tee /etc/systemd/system/council-bot.service

sudo systemctl daemon-reload
sudo systemctl enable --now council-bot
sudo journalctl -u council-bot -f
```

Updates afterwards are `./deploy/update.sh`.

The unit runs with `NoNewPrivileges`, `PrivateTmp` and `ProtectSystem=strict`, with `data/` as the only writable path — so a compromised bot process cannot write anywhere else on the filesystem.

---

## Option 3 — a managed worker host

Railway, Fly.io, Render and similar platforms all deploy this shape of process from a Git repository. The pattern is the same everywhere:

1. Point the platform at the repo. It detects Python, installs `requirements.txt`, and starts the process from the `Procfile`.
2. Set the six environment variables in the platform's dashboard — never in the repo.
3. **Attach a persistent volume mounted at the `data/` directory.** Without one, the container's filesystem is ephemeral and the SQLite database is wiped on every redeploy, taking the prediction history with it.
4. If the platform offers no persistent storage, either bake `python scripts/seed_members.py && python main.py` into the start command so the roster is rebuilt on every boot, or move to Postgres.

Free tiers on these platforms have come and gone repeatedly; check current pricing rather than trusting any guide, this one included.

---

## Timezone

Containers almost always run on UTC. It doesn't matter here: `AsyncIOScheduler` is constructed with `timezone=America/New_York` and every `CronTrigger` carries the same timezone explicitly. No `TZ` environment variable is needed, and setting one changes nothing about when the jobs fire.

---

## Secrets

- `.env` is gitignored and must never be committed. Verify with `git ls-files | grep env` — only `.env.example` should appear.
- Set secrets through the host's environment-variable interface, not in the image or the repo.
- If a token is ever pasted anywhere shared, reset it in the Discord Developer Portal — Applications → your app → Bot → **Reset Token** — and update every environment that uses it. Rotation is cheap; a leaked bot token is not.

---

## Going live

1. Deploy with `TEST_MODE=true` and run through [docs/testing.md](testing.md) end to end.
2. Set `TEST_MODE=false` and restart.
3. Confirm the log reads `Synced 9 slash commands` — not 12. The three `/test_*` commands disappearing is the proof that production mode is active.
4. Confirm the trading-day and submission-window gates are live again: with `TEST_MODE=false`, a button tap outside 09:20–09:28 ET must be rejected.
