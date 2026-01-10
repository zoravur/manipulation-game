from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_FILE = LOG_DIR / f"openrouter_run_{RUN_ID}.jsonl"
CACHE_DB = LOG_DIR / "openrouter_cache.sqlite3"
REQUEST_SEED = 1236
MAX_TOKENS = 10_000
