from crypto_manager import CryptoManager
from storage import VaultStorage


class AuthError(Exception):
    """Raised when authentication fails (wrong password or no vault)."""


class AuthManager:
    """Handles first-time vault setup and master-password login.

    Uses the 'verifier' pattern: encrypt a known string with the derived
    key and store the ciphertext. On login, try to decrypt it with the
    candidate key — if it matches the known string, the password was right.
    The master password itself is never stored.
    """

    VERIFIER_PLAINTEXT = "PASSWORD_MANAGER_OK"

    def __init__(self, storage: VaultStorage):
        self._storage = storage

    def is_initialized(self) -> bool:
        """True if a vault has been set up here previously."""
        return self._storage.load_meta() is not None

    def setup(self, master_password: str) -> CryptoManager:
        """First-time setup: create salt + verifier, return ready CryptoManager."""
        if not master_password:
            raise ValueError("master password cannot be empty")

        salt = CryptoManager.generate_salt()
        key = CryptoManager.derive_key(master_password, salt)
        crypto = CryptoManager(key)
        verifier = crypto.encrypt(self.VERIFIER_PLAINTEXT)
        self._storage.save_meta(salt, verifier)
        return crypto

    def login(self, master_password: str) -> CryptoManager:
        """Verify master password and return a ready CryptoManager."""
        meta = self._storage.load_meta()
        if meta is None:
            raise AuthError("vault is not initialized")

        salt, verifier = meta
        key = CryptoManager.derive_key(master_password, salt)
        crypto = CryptoManager(key)

        try:
            decrypted = crypto.decrypt(verifier)
        except Exception:
            raise AuthError("incorrect master password")

        if decrypted != self.VERIFIER_PLAINTEXT:
            raise AuthError("incorrect master password")

        return crypto
