from crypto_manager import CryptoManager
from password_entry import PasswordEntry
from storage import VaultStorage


class Vault:
    """The main orchestrator. Bridges Storage (where entries live) and
    CryptoManager (encryption). Outside callers always see plaintext entries;
    everything in storage is encrypted."""

    def __init__(self, storage: VaultStorage, crypto: CryptoManager):
        self._storage = storage
        self._crypto = crypto

    def add(self, service: str, username: str, password: str,
            notes: str = "") -> PasswordEntry:
        """Encrypt the password (and notes), store the entry, return it
        with its assigned id (still containing the plaintext)."""
        encrypted_pw = self._crypto.encrypt(password).decode("ascii")
        encrypted_notes = (
            self._crypto.encrypt(notes).decode("ascii") if notes else ""
        )
        encrypted_entry = PasswordEntry(
            service=service,
            username=username,
            password=encrypted_pw,
            notes=encrypted_notes,
        )
        saved = self._storage.add_entry(encrypted_entry)
        # Return a plaintext view to the caller
        return PasswordEntry(
            service=saved.service,
            username=saved.username,
            password=password,
            notes=notes,
            id=saved.id,
            created_at=saved.created_at,
            modified_at=saved.modified_at,
        )

    def list_entries(self) -> list[PasswordEntry]:
        """Load all entries and decrypt them."""
        encrypted_entries = self._storage.get_all_entries()
        plaintext_entries = []
        for e in encrypted_entries:
            decrypted_pw = self._crypto.decrypt(e.password.encode("ascii"))
            decrypted_notes = (
                self._crypto.decrypt(e.notes.encode("ascii")) if e.notes else ""
            )
            plaintext_entries.append(PasswordEntry(
                service=e.service,
                username=e.username,
                password=decrypted_pw,
                notes=decrypted_notes,
                id=e.id,
                created_at=e.created_at,
                modified_at=e.modified_at,
            ))
        return plaintext_entries

    def update_password(self, entry_id: int, new_password: str) -> None:
        """Change the password for an existing entry."""
        target = self._find_encrypted_entry(entry_id)
        target.update_password(self._crypto.encrypt(new_password).decode("ascii"))
        self._storage.update_entry(target)

    def update_username(self, entry_id: int, new_username: str) -> None:
        """Change the username for an existing entry."""
        target = self._find_encrypted_entry(entry_id)
        target.update_username(new_username)
        self._storage.update_entry(target)

    def update_notes(self, entry_id: int, new_notes: str) -> None:
        """Change the notes for an existing entry."""
        target = self._find_encrypted_entry(entry_id)
        encrypted_notes = (
            self._crypto.encrypt(new_notes).decode("ascii") if new_notes else ""
        )
        target.update_notes(encrypted_notes)
        self._storage.update_entry(target)

    def delete(self, entry_id: int) -> None:
        """Remove an entry from storage."""
        self._storage.delete_entry(entry_id)

    def _find_encrypted_entry(self, entry_id: int) -> PasswordEntry:
        """Helper: find an entry by id (returns the still-encrypted version
        from storage). Raises ValueError if not found."""
        for e in self._storage.get_all_entries():
            if e.id == entry_id:
                return e
        raise ValueError(f"entry with id {entry_id} not found")
