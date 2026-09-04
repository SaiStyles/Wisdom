CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY,
    discord_id TEXT UNIQUE NOT NULL,
    username TEXT,
    framework TEXT,
    source TEXT,
    joined_date DATE,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    member_id INTEGER REFERENCES members(id),
    prediction INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    submitted_at TIMESTAMP NOT NULL,
    UNIQUE(date, member_id)
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    actual_outcome INTEGER NOT NULL,
    consensus_prediction INTEGER,
    consensus_percentage FLOAT,
    avg_confidence FLOAT,
    total_submissions INTEGER,
    signal_type TEXT
);

CREATE TABLE IF NOT EXISTS daily_aggregates (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    expansion_up_count INTEGER DEFAULT 0,
    expansion_down_count INTEGER DEFAULT 0,
    expansion_both_count INTEGER DEFAULT 0,
    range_count INTEGER DEFAULT 0,
    avg_confidence FLOAT,
    total_submissions INTEGER,
    leading_option INTEGER,
    leading_pct FLOAT,
    signal_type TEXT,
    posted_to_group BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS skips (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS broadcast_log (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    member_id INTEGER REFERENCES members(id),
    delivered BOOLEAN DEFAULT FALSE,
    delivered_at TIMESTAMP,
    UNIQUE(date, member_id)
);
