"""Unit tests for PasswordEntry."""
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from password_entry import PasswordEntry  # noqa: E402


class TestPasswordEntryConstruction(unittest.TestCase):
    """Test creating PasswordEntry objects with various inputs."""

    def test_creates_with_required_fields(self):
        entry = PasswordEntry("github", "elvinas", "secret123")
        self.assertEqual(entry.service, "github")
        self.assertEqual(entry.username, "elvinas")
        self.assertEqual(entry.password, "secret123")
        self.assertEqual(entry.notes, "")
        self.assertIsNone(entry.id)

    def test_accepts_optional_fields(self):
        entry = PasswordEntry(
            "gmail", "user@x.com", "pw", notes="work", id=42
        )
        self.assertEqual(entry.notes, "work")
        self.assertEqual(entry.id, 42)

    def test_missing_service_raises(self):
        with self.assertRaises(ValueError):
            PasswordEntry("", "user", "pw")

    def test_missing_username_raises(self):
        with self.assertRaises(ValueError):
            PasswordEntry("svc", "", "pw")

    def test_missing_password_raises(self):
        with self.assertRaises(ValueError):
            PasswordEntry("svc", "user", "")

    def test_created_at_defaults_to_now(self):
        entry = PasswordEntry("svc", "user", "pw")
        self.assertIsNotNone(entry.created_at)

    def test_modified_at_defaults_to_created_at(self):
        entry = PasswordEntry("svc", "user", "pw")
        self.assertEqual(entry.modified_at, entry.created_at)


class TestPasswordEntryMutators(unittest.TestCase):
    """Test the update_* methods."""

    def setUp(self):
        self.entry = PasswordEntry("svc", "user", "pw", notes="old")

    def test_update_username_changes_value(self):
        self.entry.update_username("new_user")
        self.assertEqual(self.entry.username, "new_user")

    def test_update_password_changes_value(self):
        self.entry.update_password("new_pw")
        self.assertEqual(self.entry.password, "new_pw")

    def test_update_notes_changes_value(self):
        self.entry.update_notes("fresh notes")
        self.assertEqual(self.entry.notes, "fresh notes")

    def test_update_username_bumps_modified_at(self):
        original = self.entry.modified_at
        time.sleep(0.001)  # ensure clock moves
        self.entry.update_username("new")
        self.assertGreater(self.entry.modified_at, original)

    def test_update_password_bumps_modified_at(self):
        original = self.entry.modified_at
        time.sleep(0.001)
        self.entry.update_password("new")
        self.assertGreater(self.entry.modified_at, original)

    def test_update_username_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.entry.update_username("")

    def test_update_password_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.entry.update_password("")


if __name__ == "__main__":
    unittest.main()
