"""Unit tests for SQLiteStorage."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from password_entry import PasswordEntry  # noqa: E402
from sqlite_storage import SQLiteStorage  # noqa: E402


class TestSQLiteStorage(unittest.TestCase):
    """Each test gets a fresh, isolated SQLite database."""

    def setUp(self):
        # Each test gets its own temp DB file.
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.storage = SQLiteStorage(self.db_path)
        self.storage.initialize()

    def tearDown(self):
        os.unlink(self.db_path)

    # --- meta ---

    def test_load_meta_returns_none_when_empty(self):
        self.assertIsNone(self.storage.load_meta())

    def test_save_and_load_meta(self):
        salt = b"sixteen-bytes!!!"
        verifier = b"some verifier bytes"
        self.storage.save_meta(salt, verifier)

        loaded = self.storage.load_meta()
        self.assertEqual(loaded, (salt, verifier))

    def test_save_meta_overwrites_existing(self):
        self.storage.save_meta(b"old-salt-aaaaaaa", b"old-verifier")
        self.storage.save_meta(b"new-salt-bbbbbbb", b"new-verifier")

        salt, verifier = self.storage.load_meta()
        self.assertEqual(salt, b"new-salt-bbbbbbb")
        self.assertEqual(verifier, b"new-verifier")

    # --- entries ---

    def test_add_entry_assigns_id(self):
        entry = PasswordEntry("github", "elvinas", "pw")
        saved = self.storage.add_entry(entry)
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.service, "github")

    def test_get_all_entries_when_empty(self):
        self.assertEqual(self.storage.get_all_entries(), [])

    def test_get_all_entries_returns_added(self):
        self.storage.add_entry(PasswordEntry("github", "user1", "pw1"))
        self.storage.add_entry(PasswordEntry("gmail", "user2", "pw2"))

        entries = self.storage.get_all_entries()
        self.assertEqual(len(entries), 2)
        services = {e.service for e in entries}
        self.assertEqual(services, {"github", "gmail"})

    def test_update_entry_persists_change(self):
        saved = self.storage.add_entry(
            PasswordEntry("github", "user", "old_pw")
        )
        saved.update_password("new_pw")
        self.storage.update_entry(saved)

        reloaded = self.storage.get_all_entries()
        self.assertEqual(reloaded[0].password, "new_pw")

    def test_delete_entry_removes_row(self):
        saved = self.storage.add_entry(PasswordEntry("svc", "user", "pw"))
        self.storage.delete_entry(saved.id)

        self.assertEqual(self.storage.get_all_entries(), [])


if __name__ == "__main__":
    unittest.main()
