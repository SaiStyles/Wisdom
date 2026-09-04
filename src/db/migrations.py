import os
import sqlite3
import config


ADDITIONS = [
    ("daily_aggregates", "leading_option", "INTEGER"),
    ("daily_aggregates", "leading_pct", "FLOAT"),
    ("daily_aggregates", "signal_type", "TEXT"),
]


def ensure_schema():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    conn = sqlite3.connect(config.DB_PATH)
    conn.executescript(sql)
    for table, col, coltype in ADDITIONS:
        existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if col not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
    conn.commit()
    conn.close()
