import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class ResponseCache:
    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS response_cache (
                request_hash TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def get(self, request_hash: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT response_json FROM response_cache WHERE request_hash = ?",
            (request_hash,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, request_hash: str, response: dict) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO response_cache (request_hash, response_json, created_at) VALUES (?, ?, ?)",
            (
                request_hash,
                json.dumps(response, ensure_ascii=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
