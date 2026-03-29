import os

# ---------------------------------------------------------------------------
# Groq
# ---------------------------------------------------------------------------
# Set GROQ_API_KEY in your environment:
#   export GROQ_API_KEY="gsk_..."
# Or create a .env file and load it with python-dotenv (see app.py).
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_TEMP    = 0.2          # low temperature → consistent structured output
GROQ_MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# SQLite file lives next to app.py by default.
# Override by setting DB_PATH env variable.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "candidate_search.db"))

# ---------------------------------------------------------------------------
# Search sources (toggle defaults)
# ---------------------------------------------------------------------------
DEFAULT_SOURCES = {
    "linkedin":  True,
    "github":    True,
    "naukri":    True,
    "google":    True,
    "db_only":   False,
}

# ---------------------------------------------------------------------------
# Scraper settings
# ---------------------------------------------------------------------------
SCRAPER_DELAY_MIN = 2.0   # seconds between requests
SCRAPER_DELAY_MAX = 5.0
MAX_RESULTS_PER_SOURCE = 50
