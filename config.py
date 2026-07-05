import os

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
BOT_ACCOUNT_ID = os.getenv("BOT_ACCOUNT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# How many past turns (user + model pairs) to keep per sender
MAX_HISTORY_TURNS = 10

# Timezone used for all date and time calculations
TIMEZONE = "Africa/Lagos"
