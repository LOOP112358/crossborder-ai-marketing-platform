import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS history_matte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_url VARCHAR(500) NOT NULL,
    matted_url VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    category_en VARCHAR(100),
    confidence FLOAT,
    attributes VARCHAR(500),
    file_size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


class MatteRepository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        try:
            item["attributes"] = json.loads(item.get("attributes") or "{}")
        except json.JSONDecodeError:
            item["attributes"] = {}
        return item

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO history_matte
                (user_id, original_url, matted_url, category, category_en,
                 confidence, attributes, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record["user_id"], record["original_url"], record["matted_url"],
                    record["category"], record["category_en"], record["confidence"],
                    json.dumps(record["attributes"], ensure_ascii=False), record["file_size"],
                ),
            )
            row = conn.execute("SELECT * FROM history_matte WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._decode(row)

    def list(self, user_id: int, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM history_matte WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [self._decode(row) for row in rows]

    def get(self, record_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM history_matte WHERE id = ?", (record_id,)).fetchone()
        return self._decode(row) if row else None

