"""CLI entry point for the password manager."""

from getpass import getpass

from auth_manager import AuthError, AuthManager
from password_generator import PasswordGenerator
from sqlite_storage import SQLiteStorage
from vault import Vault


class App:
    """Interactive command-line interface for the password manager."""

    def __init__(self, db_path: str = "vault.db"):
        self._storage = SQLiteStorage(db_path)
        self._storage.initialize()
        self._auth = AuthManager(self._storage)
        self._vault: Vault | None = None
        self._generator = PasswordGenerator()

    def run(self) -> None:
        """Main entry point — handle login or setup, then enter the menu loop."""
        print("=" * 40)
        print(" Password Manager")
        print("=" * 40)

        if self._auth.is_initialized():
            self._login()
        else:
            self._setup()

        self._main_menu()

    # --- Authentication flows ---

    def _setup(self) -> None:
        print("\nNo vault found. Let's create one.")
        while True:
            pw = getpass("Choose a master password: ")
            confirm = getpass("Confirm master password: ")
            if pw != confirm:
                print("Passwords do not match. Try again.\n")
                continue
            if not pw:
                print("Password cannot be empty. Try again.\n")
                continue
            try:
                crypto = self._auth.setup(pw)
                self._vault = Vault(self._storage, crypto)
                print("Vault created.\n")
                return
            except ValueError as e:
                print(f"Error: {e}\n")

    def _login(self) -> None:
        print("\nVault found. Please log in.")
        while True:
            pw = getpass("Master password: ")
            try:
                crypto = self._auth.login(pw)
                self._vault = Vault(self._storage, crypto)
                print("Login successful.\n")
                return
            except AuthError as e:
                print(f"{e}. Try again.\n")

    # --- Main menu ---

    def _main_menu(self) -> None:
        while True:
            print("---- Menu ----")
            print("1) List entries")
            print("2) Add entry")
            print("3) Update password")
            print("4) Update username")
            print("5) Update notes")
            print("6) Delete entry")
            print("7) Generate a random password")
            print("0) Quit")
            choice = input("Choice: ").strip()
            print()

            actions = {
                "1": self._list_entries,
                "2": self._add_entry,
                "3": self._update_password,
                "4": self._update_username,
                "5": self._update_notes,
                "6": self._delete_entry,
                "7": self._generate_password,
            }

            if choice == "0":
                print("Goodbye.")
                return
            action = actions.get(choice)
            if action is None:
                print("Invalid choice.\n")
                continue
            try:
                action()
            except (ValueError, AuthError) as e:
                print(f"Error: {e}")
            print()

    # --- Menu actions ---

    def _list_entries(self) -> None:
        entries = self._vault.list_entries()
        if not entries:
            print("No entries.")
            return
        for e in entries:
            print(f"[{e.id}] {e.service}")
            print(f"     username: {e.username}")
            print(f"     password: {e.password}")
            if e.notes:
                print(f"     notes:    {e.notes}")
            print(f"     modified: {e.modified_at:%Y-%m-%d %H:%M}")

    def _add_entry(self) -> None:
        service = input("Service: ").strip()
        username = input("Username/email: ").strip()
        password = getpass("Password (leave blank to auto-generate): ")
        if not password:
            password = self._generator.generate()
            print(f"Generated password: {password}")
        notes = input("Notes (optional): ").strip()
        saved = self._vault.add(service, username, password, notes)
        print(f"Saved as id {saved.id}.")

    def _update_password(self) -> None:
        entry_id = int(input("Entry id: ").strip())
        new_pw = getpass("New password (leave blank to auto-generate): ")
        if not new_pw:
            new_pw = self._generator.generate()
            print(f"Generated password: {new_pw}")
        self._vault.update_password(entry_id, new_pw)
        print("Password updated.")

    def _update_username(self) -> None:
        entry_id = int(input("Entry id: ").strip())
        new_username = input("New username: ").strip()
        self._vault.update_username(entry_id, new_username)
        print("Username updated.")

    def _update_notes(self) -> None:
        entry_id = int(input("Entry id: ").strip())
        new_notes = input("New notes: ").strip()
        self._vault.update_notes(entry_id, new_notes)
        print("Notes updated.")

    def _delete_entry(self) -> None:
        entry_id = int(input("Entry id: ").strip())
        confirm = input(f"Delete entry {entry_id}? (y/N): ").strip().lower()
        if confirm == "y":
            self._vault.delete(entry_id)
            print("Deleted.")
        else:
            print("Cancelled.")

    def _generate_password(self) -> None:
        length_str = input("Length (default 16): ").strip()
        length = int(length_str) if length_str else 16
        print(f"Generated: {self._generator.generate(length)}")


if __name__ == "__main__":
    App().run()
