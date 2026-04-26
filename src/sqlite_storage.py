import sqlite3
from datetime import datetime

from password_entry import PasswordEntry
from storage import VaultStorage


class SQLiteStorage(VaultStorage):
    """SQLite-backed implementation of VaultStorage."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS meta (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        salt BLOB NOT NULL,
        verifier BLOB NOT NULL
    );

    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        modified_at TEXT NOT NULL
    );
    """

    def __init__(self, db_path: str = "vault.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def initialize(self) -> None:
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def save_meta(self, salt: bytes, verifier: bytes) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (id, salt, verifier) VALUES (1, ?, ?)",
            (salt, verifier),
        )
        self._conn.commit()

    def load_meta(self) -> tuple[bytes, bytes] | None:
        row = self._conn.execute(
            "SELECT salt, verifier FROM meta WHERE id = 1"
        ).fetchone()
        if row is None:
            return None
        return (row["salt"], row["verifier"])

    def add_entry(self, entry: PasswordEntry) -> PasswordEntry:
        cursor = self._conn.execute(
            "INSERT INTO entries "
            "(service, username, password, notes, created_at, modified_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                entry.service,
                entry.username,
                entry.password,
                entry.notes,
                entry.created_at.isoformat(),
                entry.modified_at.isoformat(),
            ),
        )
        self._conn.commit()
        return PasswordEntry(
            service=entry.service,
            username=entry.username,
            password=entry.password,
            notes=entry.notes,
            id=cursor.lastrowid,
            created_at=entry.created_at,
            modified_at=entry.modified_at,
        )

    def get_all_entries(self) -> list[PasswordEntry]:
        rows = self._conn.execute(
            "SELECT id, service, username, password, notes, "
            "created_at, modified_at FROM entries ORDER BY service"
        ).fetchall()

        entries = []
        for row in rows:
            entries.append(PasswordEntry(
                service=row["service"],
                username=row["username"],
                password=row["password"],
                notes=row["notes"] or "",
                id=row["id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                modified_at=datetime.fromisoformat(row["modified_at"]),
            ))
        return entries

    def update_entry(self, entry: PasswordEntry) -> None:
        self._conn.execute(
            "UPDATE entries SET service = ?, username = ?, password = ?, "
            "notes = ?, modified_at = ? WHERE id = ?",
            (
                entry.service,
                entry.username,
                entry.password,
                entry.notes,
                entry.modified_at.isoformat(),
                entry.id,
            ),
        )
        self._conn.commit()

    def delete_entry(self, entry_id: int) -> None:
        self._conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self._conn.commit()
