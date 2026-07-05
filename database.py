import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            # Recreamos las tablas para asegurarnos de tener el esquema completo
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    location TEXT DEFAULT 'Worldwide',
                    check_interval_hours INTEGER DEFAULT 12,
                    last_search_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    keywords TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS seen_jobs (
                    job_link TEXT PRIMARY KEY,
                    user_id INTEGER,
                    notified_at TEXT NOT NULL
                );
                """
            )

    def register_user(self, telegram_id: int, username: Optional[str], first_name: Optional[str]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name;
                """,
                (telegram_id, username, first_name, _utcnow())
            )
            
            # Si el usuario no tiene ninguna búsqueda registrada, añadir una por defecto ('Canva AI')
            tracks = conn.execute("SELECT 1 FROM user_tracks WHERE user_id = ?", (telegram_id,)).fetchone()
            if not tracks:
                conn.execute(
                    "INSERT INTO user_tracks (user_id, keywords, created_at) VALUES (?, 'Canva AI', ?)",
                    (telegram_id, _utcnow())
                )

    def add_track(self, user_id: int, keywords: str) -> None:
        with self._connect() as conn:
            # Verificar si ya existe para evitar duplicados idénticos
            exists = conn.execute(
                "SELECT 1 FROM user_tracks WHERE user_id = ? AND LOWER(keywords) = LOWER(?)",
                (user_id, keywords.strip())
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO user_tracks (user_id, keywords, created_at) VALUES (?, ?, ?)",
                    (user_id, keywords.strip(), _utcnow())
                )

    def remove_track(self, user_id: int, track_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM user_tracks WHERE id = ? AND user_id = ?",
                (track_id, user_id)
            )
            return cursor.rowcount > 0

    def get_tracks(self, user_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, keywords, created_at FROM user_tracks WHERE user_id = ? ORDER BY id ASC",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_user_location(self, telegram_id: int, location: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET location = ? WHERE telegram_id = ?",
                (location.strip(), telegram_id)
            )

    def update_user_frequency(self, telegram_id: int, hours: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET check_interval_hours = ? WHERE telegram_id = ?",
                (hours, telegram_id)
            )

    def update_last_search_time(self, telegram_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET last_search_at = ? WHERE telegram_id = ?",
                (_utcnow(), telegram_id)
            )

    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT telegram_id, username, first_name, location, check_interval_hours, last_search_at, created_at FROM users WHERE telegram_id = ?",
                (telegram_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT telegram_id, username, first_name, location, check_interval_hours, last_search_at FROM users"
            ).fetchall()
            return [dict(r) for r in rows]

    def is_job_seen(self, job_link: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_jobs WHERE job_link = ?",
                (job_link,)
            ).fetchone()
            return row is not None

    def mark_job_seen(self, job_link: str, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_jobs (job_link, user_id, notified_at) VALUES (?, ?, ?)",
                (job_link, user_id, _utcnow())
            )