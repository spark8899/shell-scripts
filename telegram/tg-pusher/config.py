import os
from dotenv import load_dotenv

load_dotenv()

# ===== Bot configuration =====
BOTS = {
    "bot1": {
        "token": os.getenv("BOT1_TOKEN"),
        "min_interval": 60,   # Minimum delay between messages (seconds)
        "jitter": 15,         # Random jitter added to delay
    },
    "bot2": {
        "token": os.getenv("BOT2_TOKEN"),
        "min_interval": 60,
        "jitter": 15,
    },
}

# ===== Group configuration =====
GROUPS = [
    {
        "group_id": -1001111222233,
        "bot": "bot1",
        "address": "id_a",
        "cron": "0 * * * *",       # every hour
    },
    {
        "group_id": -1002222333344,
        "bot": "bot2",
        "address": "id_b",
        "cron": "*/15 * * * *",    # every 15 minutes
    },
]

# ===== Retry strategy =====
BACKOFF = [300, 900, 3600, 21600]  # Retry delays in seconds
MAX_RETRY = 4                     # Maximum retry attempts
