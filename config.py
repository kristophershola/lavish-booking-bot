import os

VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
BOT_ACCOUNT_ID = os.getenv("BOT_ACCOUNT_ID")

# How many past turns (user + model pairs) to keep per sender
MAX_HISTORY_TURNS = 10

# Timezone used for all date and time calculations
TIMEZONE = "Africa/Lagos"

# Google Sheets, Phase 3
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "17-hZjuNdfEczlyLbNBEYmnWbAGLIl45-RZ1PFsNp-6Q")

APARTMENT_TABS = ["A1", "B1", "B2", "C1", "C2"]
HALL_TABS = ["HALL 1", "HALL 2"]

# Groq, replaces Gemini as the AI provider due to Gemini's free tier
# request-per-day limit being too tight for real testing volume.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
