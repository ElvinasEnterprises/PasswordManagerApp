"""Unit tests for AuthManager."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from auth_manager import AuthError, AuthManager  # noqa: E402
from sqlite_storage import SQLiteStorage  # noqa: E402


class TestAuthManager(unittest.TestCase):

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.storage = SQLiteStorage(self.db_path)
        self.storage.initialize()
        self.auth = AuthManager(self.storage)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_fresh_vault_not_initialized(self):
        self.assertFalse(self.auth.is_initialized())

    def test_setup_marks_initialized(self):
        self.auth.setup("master-password")
        self.assertTrue(self.auth.is_initialized())

    def test_setup_returns_crypto_manager(self):
        crypto = self.auth.setup("master-password")
        # Should be able to encrypt/decrypt with returned manager.
        self.assertEqual(crypto.decrypt(crypto.encrypt("hello")), "hello")

    def test_setup_rejects_empty_password(self):
        with self.assertRaises(ValueError):
            self.auth.setup("")

    def test_login_with_correct_password_succeeds(self):
        self.auth.setup("the-right-password")
        crypto = self.auth.login("the-right-password")
        # Returned crypto should work
        self.assertEqual(crypto.decrypt(crypto.encrypt("ok")), "ok")

    def test_login_with_wrong_password_raises(self):
        self.auth.setup("right-password")
        with self.assertRaises(AuthError):
            self.auth.login("wrong-password")

    def test_login_before_setup_raises(self):
        with self.assertRaises(AuthError):
            self.auth.login("anything")


if __name__ == "__main__":
    unittest.main()
