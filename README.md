# manipulation-game
Code repository for Apart Research's AI Manipulation Hackathon.

## OpenRouter sample
`openrouter_sample.py` demonstrates:
- OpenRouter OpenAI-compatible calls (GPT/Claude/Gemini)
- Tool calling with a SymPy verification tool
- Per-run JSONL logging in `logs/openrouter_run_*.jsonl`
- SQLite response cache in `logs/openrouter_cache.sqlite3`

### Setup
1) Create a `.env` with `OPENROUTER_API_KEY=...`
2) Install deps: `uv sync`

### Run
- `uv run python openrouter_sample.py`

### View logs
- `uv run python log_viewer.py logs/openrouter_run_YYYYMMDDTHHMMSSZ.jsonl`

### Tests
Install dev deps:
- `uv sync --extra dev`

Run unit tests (no network):
- `uv run pytest -m "not integration"`

Run integration test (network + OpenRouter key required):
- `uv run pytest -m integration`
