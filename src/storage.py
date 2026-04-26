from abc import ABC, abstractmethod
from password_entry import PasswordEntry


class VaultStorage(ABC):
    """Contract for any storage backend (SQLite, JSON, in-memory, etc.)."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Create tables / set up the storage. Safe to call multiple times."""
        pass
    
    @abstractmethod
    def save_meta(self, salt: bytes, verifier: bytes) -> None:
        """Stores the salt + Verifier for authentication"""
        pass

    @abstractmethod
    def load_meta(self) -> tuple[bytes, bytes] | None:
        """Returns (salt, verifier) if the vault is initialized, else None."""
        pass

    @abstractmethod
    def add_entry(self, entry: PasswordEntry) -> PasswordEntry:
        """Saves a new password entry and returns it with an ID assigned."""
        pass

    @abstractmethod
    def get_all_entries(self) -> list[PasswordEntry]:
        """ Returns a list of every PasswordEntry in the storage"""
        pass

    @abstractmethod
    def update_entry(self, entry: PasswordEntry) -> None:
        """Updates an entry"""
        pass

    @abstractmethod
    def delete_entry(self, entry_id: int) -> None:
        """Removes an entry"""
        pass

