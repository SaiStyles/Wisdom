"""
Bulk-add members from CSV, or add a single member via CLI args.

Usage:
    # Single member:
    python scripts/add_roster.py <discord_id> <username> <framework> <source>

    # Bulk from CSV (scripts/roster.csv with headers: discord_id,username,framework,source):
    python scripts/add_roster.py

Existing members (duplicate discord_id) are skipped; the script never updates or
overwrites. Safe to re-run.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db.migrations import ensure_schema
from src.db.repositories.members import add

CSV_PATH = os.path.join(os.path.dirname(__file__), "roster.csv")
REQUIRED = ("discord_id", "username", "framework", "source")


def _add_one(discord_id: str, username: str, framework: str, source: str) -> bool:
    try:
        add(discord_id, username, framework, source)
        print(f"  added  {username:<20} ({framework})  id={discord_id}")
        return True
    except Exception as e:
        print(f"  skip   {username:<20} ({framework})  reason={e}")
        return False


def _from_args(argv: list[str]) -> None:
    discord_id, username, framework, source = argv
    _add_one(discord_id, username, framework, source)


def _from_csv(path: str) -> None:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = set(REQUIRED) - set(reader.fieldnames or [])
        if missing:
            print(f"CSV missing columns: {sorted(missing)}")
            sys.exit(1)
        added = total = 0
        for row in reader:
            total += 1
            if _add_one(
                row["discord_id"].strip(),
                row["username"].strip(),
                row["framework"].strip(),
                row["source"].strip(),
            ):
                added += 1
        print(f"\n{added}/{total} added.")


def main() -> None:
    ensure_schema()

    args = sys.argv[1:]
    if len(args) == 4:
        _from_args(args)
        return
    if len(args) == 0:
        if not os.path.exists(CSV_PATH):
            print(f"No args given and {CSV_PATH} not found.")
            print("Copy scripts/roster.csv.example to scripts/roster.csv and fill it in,")
            print("or pass: <discord_id> <username> <framework> <source>")
            sys.exit(1)
        _from_csv(CSV_PATH)
        return

    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    main()
