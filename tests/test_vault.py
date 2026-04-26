"""Unit tests for Vault — uses real Storage + CryptoManager.

Verifies that:
  * passwords are encrypted before reaching storage,
  * the vault returns plaintext to its callers,
  * CRUD operations behave correctly end-to-end.
"""
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from auth_manager import AuthManager  # noqa: E402
from sqlite_storage import SQLiteStorage  # noqa: E402
from vault import Vault  # noqa: E402


class TestVault(unittest.TestCase):

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.storage = SQLiteStorage(self.db_path)
        self.storage.initialize()
        crypto = AuthManager(self.storage).setup("master-pw")
        self.vault = Vault(self.storage, crypto)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_add_and_list_roundtrip(self):
        self.vault.add("github", "elvinas", "secret-pw")
        entries = self.vault.list_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].service, "github")
        self.assertEqual(entries[0].password, "secret-pw")

    def test_password_is_encrypted_in_db(self):
        self.vault.add("github", "user", "plaintext-pw")

        # Bypass the vault and look at the raw DB.
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT password FROM entries").fetchone()
        conn.close()

        self.assertNotIn("plaintext-pw", row[0])
        # Fernet ciphertext starts with "gAAAAA"
        self.assertTrue(row[0].startswith("gAAAAA"))

    def test_update_password_changes_value(self):
        saved = self.vault.add("github", "user", "old-pw")
        self.vault.update_password(saved.id, "new-pw")

        entries = self.vault.list_entries()
        self.assertEqual(entries[0].password, "new-pw")

    def test_update_username_changes_value(self):
        saved = self.vault.add("github", "old-user", "pw")
        self.vault.update_username(saved.id, "new-user")

        entries = self.vault.list_entries()
        self.assertEqual(entries[0].username, "new-user")

    def test_update_notes_changes_value(self):
        saved = self.vault.add("svc", "user", "pw", notes="old notes")
        self.vault.update_notes(saved.id, "new notes")

        entries = self.vault.list_entries()
        self.assertEqual(entries[0].notes, "new notes")

    def test_delete_removes_entry(self):
        saved = self.vault.add("svc", "user", "pw")
        self.vault.delete(saved.id)

        self.assertEqual(self.vault.list_entries(), [])

    def test_update_nonexistent_entry_raises(self):
        with self.assertRaises(ValueError):
            self.vault.update_password(99999, "pw")


if __name__ == "__main__":
    unittest.main()
