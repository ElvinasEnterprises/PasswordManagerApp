import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from cryptography.fernet import Fernet


class CryptoManager:
    """Handles encryption, decryption, and key derivation."""
    
    ITERATIONS = 200_000
    
    @staticmethod
    def generate_salt() -> bytes:
        return secrets.token_bytes(16)
    
    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=CryptoManager.ITERATIONS,
            )
        password_bytes = master_password.encode("utf-8")
        raw_key = kdf.derive(password_bytes)

        return base64.urlsafe_b64encode(raw_key)
    
    def __init__(self, key: bytes):
        if not key:
            raise ValueError("key cannot be empty")
        
        self._fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode("utf-8"))
    
    def decrypt(self, ciphertext: bytes) -> str:
        return self._fernet.decrypt(ciphertext).decode("utf-8")