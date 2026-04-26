"""Tkinter GUI for the password manager.

This module wraps the existing backend (Vault, AuthManager, CryptoManager,
SQLiteStorage) in a graphical interface. The backend is unchanged — the GUI
is just another presentation layer over the same business logic.

Run with:  python3 gui_app.py
"""

import tkinter as tk
from tkinter import messagebox, ttk

from auth_manager import AuthError, AuthManager
from password_generator import PasswordGenerator
from sqlite_storage import SQLiteStorage
from vault import Vault


PASSWORD_MASK = "•" * 10


class PasswordManagerGUI:
    """Top-level GUI controller — owns the root window and shared services."""

    def __init__(self, db_path: str = "vault.db"):
        self._storage = SQLiteStorage(db_path)
        self._storage.initialize()
        self._auth = AuthManager(self._storage)
        self._generator = PasswordGenerator()
        self._vault: Vault | None = None

        self._root = tk.Tk()
        self._root.title("Password Manager")
        self._root.geometry("820x540")
        self._root.minsize(640, 420)
        self._current_frame: tk.Frame | None = None

    def run(self) -> None:
        self._show_login()
        self._root.mainloop()

    def _swap_frame(self, new_frame: tk.Frame) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = new_frame
        self._current_frame.pack(fill="both", expand=True)

    def _show_login(self) -> None:
        self._swap_frame(LoginFrame(
            self._root, self._auth, on_success=self._on_login_success
        ))

    def _on_login_success(self, crypto) -> None:
        self._vault = Vault(self._storage, crypto)
        self._show_main()

    def _show_main(self) -> None:
        self._swap_frame(MainFrame(
            self._root, self._vault, self._generator, on_logout=self._on_logout
        ))

    def _on_logout(self) -> None:
        self._vault = None
        self._show_login()


class LoginFrame(tk.Frame):
    """Initial screen — handles either setup (first run) or login."""

    def __init__(self, parent, auth: AuthManager, on_success):
        super().__init__(parent, padx=40, pady=40)
        self._auth = auth
        self._on_success = on_success
        self._is_setup = not auth.is_initialized()
        self._show_password = False
        self._build_ui()

    def _build_ui(self) -> None:
        title = "Create Your Vault" if self._is_setup else "Unlock Your Vault"
        ttk.Label(self, text=title, font=("Helvetica", 22, "bold")).pack(
            pady=(40, 8)
        )

        subtitle = (
            "Choose a strong master password — you'll need it every time."
            if self._is_setup
            else "Enter your master password."
        )
        ttk.Label(self, text=subtitle).pack(pady=(0, 24))

        form = ttk.Frame(self)
        form.pack()

        ttk.Label(form, text="Master password:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self._pw_entry = ttk.Entry(form, show="•", width=32)
        self._pw_entry.grid(row=0, column=1, padx=8)
        self._pw_entry.focus_set()

        if self._is_setup:
            ttk.Label(form, text="Confirm password:").grid(
                row=1, column=0, sticky="w", pady=4
            )
            self._confirm_entry = ttk.Entry(form, show="•", width=32)
            self._confirm_entry.grid(row=1, column=1, padx=8)
        else:
            self._confirm_entry = None

        # Show / hide toggle
        self._show_btn = ttk.Button(
            self, text="Show password", command=self._toggle_password
        )
        self._show_btn.pack(pady=(12, 0))

        button_text = "Create Vault" if self._is_setup else "Unlock"
        ttk.Button(self, text=button_text, command=self._submit).pack(pady=16)

        # Pressing Enter submits
        self._pw_entry.bind("<Return>", lambda e: self._submit())
        if self._confirm_entry is not None:
            self._confirm_entry.bind("<Return>", lambda e: self._submit())

        self._status = ttk.Label(self, text="", foreground="red")
        self._status.pack()

    def _toggle_password(self) -> None:
        self._show_password = not self._show_password
        new_show = "" if self._show_password else "•"
        self._pw_entry.config(show=new_show)
        if self._confirm_entry is not None:
            self._confirm_entry.config(show=new_show)
        self._show_btn.config(
            text="Hide password" if self._show_password else "Show password"
        )

    def _submit(self) -> None:
        pw = self._pw_entry.get()
        if not pw:
            self._status.config(text="Master password cannot be empty.")
            return

        if self._confirm_entry is not None:
            if pw != self._confirm_entry.get():
                self._status.config(text="Passwords do not match.")
                return

        try:
            if self._is_setup:
                crypto = self._auth.setup(pw)
            else:
                crypto = self._auth.login(pw)
            self._on_success(crypto)
        except (AuthError, ValueError) as e:
            self._status.config(text=str(e))


class MainFrame(tk.Frame):
    """The main vault view — entry list + action buttons."""

    def __init__(self, parent, vault: Vault, generator: PasswordGenerator,
                 on_logout):
        super().__init__(parent)
        self._vault = vault
        self._generator = generator
        self._on_logout = on_logout
        self._show_passwords = False
        self._entries: list = []
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        # Toolbar
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Add", command=self._add).pack(
            side="left", padx=2
        )
        ttk.Button(toolbar, text="Edit", command=self._edit).pack(
            side="left", padx=2
        )
        ttk.Button(toolbar, text="Delete", command=self._delete).pack(
            side="left", padx=2
        )
        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=8
        )
        ttk.Button(toolbar, text="Generate Password",
                   command=self._generate_standalone).pack(side="left", padx=2)

        self._toggle_btn = ttk.Button(
            toolbar, text="Show Passwords", command=self._toggle_passwords
        )
        self._toggle_btn.pack(side="left", padx=2)

        ttk.Button(toolbar, text="Logout", command=self._on_logout).pack(
            side="right", padx=2
        )

        # Treeview + scrollbar
        tree_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        tree_frame.pack(fill="both", expand=True)

        columns = ("id", "service", "username", "password", "notes")
        self._tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse"
        )

        widths = {"id": 50, "service": 160, "username": 180,
                  "password": 200, "notes": 180}
        for col in columns:
            self._tree.heading(col, text=col.title())
            self._tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self._tree.yview
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Status bar
        self._status = ttk.Label(
            self, text="", padding=(10, 4), relief="sunken", anchor="w"
        )
        self._status.pack(fill="x", side="bottom")

        # Double-click row to edit
        self._tree.bind("<Double-Button-1>", lambda e: self._edit())

    def _refresh(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        self._entries = self._vault.list_entries()
        for entry in self._entries:
            pw_display = entry.password if self._show_passwords else PASSWORD_MASK
            self._tree.insert("", "end", iid=str(entry.id), values=(
                entry.id, entry.service, entry.username,
                pw_display, entry.notes or ""
            ))

        count = len(self._entries)
        self._status.config(
            text=f"{count} {'entry' if count == 1 else 'entries'}"
        )

    def _selected_entry(self):
        sel = self._tree.selection()
        if not sel:
            return None
        eid = int(sel[0])
        return next((e for e in self._entries if e.id == eid), None)

    # --- Actions ---

    def _add(self) -> None:
        EntryDialog(
            self, self._generator,
            on_save=self._handle_add,
            title_text="Add Entry",
        )

    def _handle_add(self, service, username, password, notes) -> None:
        try:
            self._vault.add(service, username, password, notes)
            self._refresh()
            self._status.config(text=f"Added '{service}'")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _edit(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            messagebox.showinfo("Edit", "Please select an entry first.")
            return
        EntryDialog(
            self, self._generator,
            on_save=lambda s, u, p, n: self._handle_edit(entry.id, u, p, n),
            title_text=f"Edit Entry — {entry.service}",
            initial_service=entry.service,
            initial_username=entry.username,
            initial_password=entry.password,
            initial_notes=entry.notes,
            service_locked=True,
        )

    def _handle_edit(self, entry_id, username, password, notes) -> None:
        try:
            self._vault.update_username(entry_id, username)
            self._vault.update_password(entry_id, password)
            self._vault.update_notes(entry_id, notes)
            self._refresh()
            self._status.config(text=f"Updated entry {entry_id}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _delete(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            messagebox.showinfo("Delete", "Please select an entry first.")
            return
        if messagebox.askyesno(
            "Confirm Deletion",
            f"Delete entry for '{entry.service}'?\n\nThis cannot be undone."
        ):
            self._vault.delete(entry.id)
            self._refresh()
            self._status.config(text=f"Deleted '{entry.service}'")

    def _toggle_passwords(self) -> None:
        self._show_passwords = not self._show_passwords
        self._toggle_btn.config(
            text="Hide Passwords" if self._show_passwords else "Show Passwords"
        )
        self._refresh()

    def _generate_standalone(self) -> None:
        GeneratePasswordDialog(self, self._generator)


class EntryDialog(tk.Toplevel):
    """Modal dialog for adding or editing an entry."""

    def __init__(self, parent, generator: PasswordGenerator, on_save,
                 title_text: str = "Entry",
                 initial_service: str = "",
                 initial_username: str = "",
                 initial_password: str = "",
                 initial_notes: str = "",
                 service_locked: bool = False):
        super().__init__(parent)
        self._generator = generator
        self._on_save = on_save
        self._show_password = False

        self.title(title_text)
        self.geometry("480x340")
        self.transient(parent)
        self.grab_set()

        self._build_ui(
            initial_service, initial_username, initial_password, initial_notes,
            service_locked
        )

    def _build_ui(self, service, username, password, notes, service_locked):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        # Service
        ttk.Label(frame, text="Service:").grid(row=0, column=0, sticky="w", pady=4)
        self._service_var = tk.StringVar(value=service)
        self._service_entry = ttk.Entry(
            frame, textvariable=self._service_var, width=36
        )
        self._service_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        if service_locked:
            self._service_entry.config(state="disabled")

        # Username
        ttk.Label(frame, text="Username:").grid(row=1, column=0, sticky="w", pady=4)
        self._username_var = tk.StringVar(value=username)
        ttk.Entry(frame, textvariable=self._username_var, width=36).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=4
        )

        # Password
        ttk.Label(frame, text="Password:").grid(row=2, column=0, sticky="w", pady=4)
        self._password_var = tk.StringVar(value=password)
        self._password_entry = ttk.Entry(
            frame, textvariable=self._password_var, show="•", width=36
        )
        self._password_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)

        # Show / Generate buttons
        button_row = ttk.Frame(frame)
        button_row.grid(row=3, column=1, columnspan=2, sticky="w", pady=2)
        self._show_btn = ttk.Button(
            button_row, text="Show", width=8, command=self._toggle_password
        )
        self._show_btn.pack(side="left", padx=(0, 4))
        ttk.Button(
            button_row, text="Generate", width=10, command=self._generate
        ).pack(side="left")

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=4, column=0, sticky="nw", pady=4)
        self._notes_var = tk.StringVar(value=notes)
        ttk.Entry(frame, textvariable=self._notes_var, width=36).grid(
            row=4, column=1, columnspan=2, sticky="ew", pady=4
        )

        # Save / Cancel
        action_row = ttk.Frame(frame)
        action_row.grid(row=5, column=0, columnspan=3, pady=(20, 0))
        ttk.Button(action_row, text="Save", command=self._save).pack(
            side="left", padx=4
        )
        ttk.Button(action_row, text="Cancel", command=self.destroy).pack(
            side="left", padx=4
        )

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _toggle_password(self):
        self._show_password = not self._show_password
        self._password_entry.config(show="" if self._show_password else "•")
        self._show_btn.config(text="Hide" if self._show_password else "Show")

    def _generate(self):
        self._password_var.set(self._generator.generate())

    def _save(self):
        service = self._service_var.get().strip()
        username = self._username_var.get().strip()
        password = self._password_var.get()
        notes = self._notes_var.get().strip()

        if not service:
            messagebox.showerror("Error", "Service is required.", parent=self)
            return
        if not username:
            messagebox.showerror("Error", "Username is required.", parent=self)
            return
        if not password:
            messagebox.showerror("Error", "Password is required.", parent=self)
            return

        self._on_save(service, username, password, notes)
        self.destroy()


class GeneratePasswordDialog(tk.Toplevel):
    """Standalone password generator with copy-to-clipboard."""

    def __init__(self, parent, generator: PasswordGenerator):
        super().__init__(parent)
        self._generator = generator

        self.title("Generate Password")
        self.geometry("420x200")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Length:").grid(row=0, column=0, sticky="w", pady=4)
        self._length_var = tk.IntVar(value=16)
        ttk.Spinbox(
            frame, from_=12, to=64, textvariable=self._length_var, width=6
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(frame, text="Generated:").grid(row=1, column=0, sticky="w", pady=4)
        self._password_var = tk.StringVar()
        ttk.Entry(
            frame, textvariable=self._password_var, width=36, state="readonly"
        ).grid(row=1, column=1, sticky="ew", pady=4)

        button_row = ttk.Frame(frame)
        button_row.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(button_row, text="Generate", command=self._generate).pack(
            side="left", padx=4
        )
        ttk.Button(button_row, text="Copy", command=self._copy).pack(
            side="left", padx=4
        )
        ttk.Button(button_row, text="Close", command=self.destroy).pack(
            side="left", padx=4
        )

        frame.columnconfigure(1, weight=1)
        self._generate()

    def _generate(self):
        try:
            length = int(self._length_var.get())
            self._password_var.set(self._generator.generate(length))
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _copy(self):
        pw = self._password_var.get()
        if not pw:
            return
        self.clipboard_clear()
        self.clipboard_append(pw)


def main():
    PasswordManagerGUI().run()


if __name__ == "__main__":
    main()
