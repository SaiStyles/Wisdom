#!/usr/bin/env bash
# Pull latest, reinstall deps if changed, restart the bot. Run on the server.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> git pull"
git pull --ff-only

echo "==> pip install"
.venv/bin/pip install -r requirements.txt --quiet

echo "==> restarting council-bot.service"
sudo systemctl restart council-bot

echo "==> tail logs ( Ctrl+C to exit )"
sudo journalctl -u council-bot -f --since "10 sec ago"
