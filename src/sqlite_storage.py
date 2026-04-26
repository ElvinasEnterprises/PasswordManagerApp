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
        self._conn.row_factory = sqlite3.Row  # lets us do row["column_name"]

    def initialize(self) -> None:
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()