"""
Seed the founding roster into the database.

By default this adds only the admin (read from ADMIN_DISCORD_ID in your .env)
so a fresh install has exactly one member. Add the rest of the roster with
`scripts/add_roster.py`, or by editing EXTRA_MEMBERS below.

Usage: python scripts/seed_members.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import config
from src.db.migrations import ensure_schema
from src.db.repositories.members import add

# (discord_id, username, framework, source)
EXTRA_MEMBERS: list[tuple[str, str, str, str]] = []


def main():
    ensure_schema()
    members = [(str(config.ADMIN_DISCORD_ID), "admin", "ICT", "self")] + EXTRA_MEMBERS
    for discord_id, username, framework, source in members:
        try:
            add(discord_id, username, framework, source)
            print(f"Added: {username} ({framework})")
        except Exception as e:
            print(f"Skipped {username}: {e}")
    print("Done.")


if __name__ == "__main__":
    main()
