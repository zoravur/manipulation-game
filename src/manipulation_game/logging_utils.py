import json
from pathlib import Path


def log_event(event: dict, log_file: Path) -> None:
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")
