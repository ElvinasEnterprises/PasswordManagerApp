"""Unit tests for PasswordGenerator."""
import os
import string
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from password_generator import PasswordGenerator  # noqa: E402


class TestPasswordGenerator(unittest.TestCase):

    def test_default_length_is_16(self):
        pw = PasswordGenerator().generate()
        self.assertEqual(len(pw), 16)

    def test_custom_length(self):
        pw = PasswordGenerator().generate(length=24)
        self.assertEqual(len(pw), 24)

    def test_minimum_length_enforced(self):
        with self.assertRaises(ValueError):
            PasswordGenerator().generate(length=8)

    def test_all_charsets_disabled_raises(self):
        with self.assertRaises(ValueError):
            PasswordGenerator(
                use_lower=False, use_upper=False,
                use_digits=False, use_symbols=False,
            )

    def test_only_lowercase(self):
        gen = PasswordGenerator(
            use_lower=True, use_upper=False,
            use_digits=False, use_symbols=False,
        )
        pw = gen.generate()
        self.assertTrue(all(c in string.ascii_lowercase for c in pw))

    def test_only_digits(self):
        gen = PasswordGenerator(
            use_lower=False, use_upper=False,
            use_digits=True, use_symbols=False,
        )
        pw = gen.generate()
        self.assertTrue(pw.isdigit())

    def test_passwords_are_random(self):
        # Two consecutive generations should virtually never match.
        gen = PasswordGenerator()
        self.assertNotEqual(gen.generate(), gen.generate())


if __name__ == "__main__":
    unittest.main()
