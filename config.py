import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_DISCORD_ID = int(os.environ["ADMIN_DISCORD_ID"])
GUILD_ID = int(os.environ["GUILD_ID"])
GROUP_CHANNEL_ID = int(os.environ["GROUP_CHANNEL_ID"]) if os.getenv("GROUP_CHANNEL_ID") else None
DB_PATH = os.getenv("DB_PATH", "data/council.db")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

TIMEZONE = "America/New_York"

BROADCAST_HOUR = 9
BROADCAST_MINUTE = 20
CUTOFF_HOUR = 9
CUTOFF_MINUTE = 28
CONSENSUS_HOUR = 9
CONSENSUS_MINUTE = 29
SESSION_END_HOUR = 11
SESSION_END_MINUTE = 0

PREDICTION_LABELS = {
    1: "Expansion Up",
    2: "Expansion Down",
    3: "Expansion Both",
    4: "Range",
}
