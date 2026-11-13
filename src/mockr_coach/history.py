"""Single-user SQLite history with deterministic topic and score aggregation."""

import json
import sqlite3
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path


class History:
    def __init__(self, path: Path | str):
        if str(path) != ":memory:":
            Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            path = str(Path(path).expanduser())
        self.db = sqlite3.connect(path)
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError("Unsupported history schema version")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, record TEXT NOT NULL)"
        )
        self.db.execute("PRAGMA user_version=1")
        self.db.commit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def save(self, record: dict) -> None:
        created = datetime.now(UTC).isoformat(timespec="microseconds")
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO sessions VALUES (?, ?, ?)",
                    (record["id"], created, json.dumps(record)),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Session already saved") from exc

    def get(self, session_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT created_at, record FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        return dict(json.loads(row[1]), created_at=row[0]) if row else None

    def summary(self) -> dict:
        rows = self.db.execute(
            "SELECT created_at, record FROM sessions ORDER BY created_at, rowid"
        ).fetchall()
        groups = defaultdict(list)
        trend = []
        sessions = []
        for created, raw in rows:
            r = json.loads(raw)
            score = r["scorecard"]["overall"]
            groups[(r["kind"], r["topic"])].append(score)
            trend.append(
                {
                    "id": r["id"],
                    "created_at": created,
                    "kind": r["kind"],
                    "score": score,
                    "provider": r["provider"],
                }
            )
            sessions.append(
                {
                    "id": r["id"],
                    "created_at": created,
                    "title": r["title"],
                    "kind": r["kind"],
                    "topic": r["topic"],
                    "score": score,
                    "provider": r["provider"],
                }
            )
        weak = [
            {
                "kind": kind,
                "topic": topic,
                "mean": round(sum(scores) / len(scores), 2),
                "sessions": len(scores),
            }
            for (kind, topic), scores in groups.items()
        ]
        weak.sort(key=lambda r: (r["mean"], r["kind"], r["topic"]))
        return {
            "count": len(rows),
            "weak_topics": weak,
            "trend": trend[-50:],
            "sessions": list(reversed(sessions[-50:])),
        }
