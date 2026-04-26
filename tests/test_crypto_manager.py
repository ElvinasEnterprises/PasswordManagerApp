"""Unit tests for CryptoManager."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crypto_manager import CryptoManager  # noqa: E402


class TestSaltAndKey(unittest.TestCase):

    def test_salt_is_16_bytes(self):
        self.assertEqual(len(CryptoManager.generate_salt()), 16)

    def test_salt_is_different_each_time(self):
        self.assertNotEqual(
            CryptoManager.generate_salt(),
            CryptoManager.generate_salt(),
        )

    def test_derive_key_returns_44_bytes(self):
        # Fernet keys are 32 bytes base64-encoded → 44 ASCII bytes
        salt = CryptoManager.generate_salt()
        key = CryptoManager.derive_key("hunter7", salt)
        self.assertEqual(len(key), 44)

    def test_derive_key_is_deterministic(self):
        salt = CryptoManager.generate_salt()
        key1 = CryptoManager.derive_key("hunter7", salt)
        key2 = CryptoManager.derive_key("hunter7", salt)
        self.assertEqual(key1, key2)

    def test_different_password_yields_different_key(self):
        salt = CryptoManager.generate_salt()
        key1 = CryptoManager.derive_key("hunter7", salt)
        key2 = CryptoManager.derive_key("different", salt)
        self.assertNotEqual(key1, key2)

    def test_different_salt_yields_different_key(self):
        key1 = CryptoManager.derive_key("hunter7", CryptoManager.generate_salt())
        key2 = CryptoManager.derive_key("hunter7", CryptoManager.generate_salt())
        self.assertNotEqual(key1, key2)


class TestEncryptDecrypt(unittest.TestCase):

    def setUp(self):
        salt = CryptoManager.generate_salt()
        key = CryptoManager.derive_key("test-password", salt)
        self.crypto = CryptoManager(key)

    def test_roundtrip_preserves_plaintext(self):
        plaintext = "my super secret password"
        ciphertext = self.crypto.encrypt(plaintext)
        self.assertEqual(self.crypto.decrypt(ciphertext), plaintext)

    def test_ciphertext_differs_from_plaintext(self):
        plaintext = "secret"
        ciphertext = self.crypto.encrypt(plaintext)
        self.assertNotIn(plaintext.encode(), ciphertext)

    def test_empty_key_raises(self):
        with self.assertRaises(ValueError):
            CryptoManager(b"")

    def test_wrong_key_cannot_decrypt(self):
        # Encrypt with one key, try to decrypt with another
        ciphertext = self.crypto.encrypt("secret")

        wrong_key = CryptoManager.derive_key(
            "wrong-password", CryptoManager.generate_salt()
        )
        wrong_crypto = CryptoManager(wrong_key)

        with self.assertRaises(Exception):
            wrong_crypto.decrypt(ciphertext)


if __name__ == "__main__":
    unittest.main()
