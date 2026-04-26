# PasswordManagerApp

A secure, locally-stored password manager written in Python, built around the four pillars of object-oriented programming. The app encrypts every saved password with a key derived from your master password, stores nothing in plaintext, and ships with both a command-line interface and a graphical interface.

> University course project — Object-Oriented Programming, VilniusTECH.

---

## Features

- **Master-password protected vault** — one password unlocks everything; nothing is stored unencrypted.
- **Modern cryptography** — Fernet (AES-128-CBC + HMAC-SHA256) with keys derived via PBKDF2-HMAC-SHA256 (200,000 iterations) and a per-vault random salt.
- **Two interfaces, one backend** — choose between a CLI (`app.py`) or a tkinter GUI (`gui_app.py`). Both share the exact same `Vault`, `AuthManager`, and `Storage` layer.
- **Built-in password generator** — configurable length and character classes (lower / upper / digits / symbols).
- **Local SQLite storage** — your vault lives in a single `vault.db` file next to the app. No cloud, no network calls.
- **Show / hide password toggles** — both on the master-password screen and inside saved entries.
- **Full CRUD** — add, list, update password / username / notes, and delete entries.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.10+ | Required by the course; clean syntax for OOP. |
| Crypto | [`cryptography`](https://cryptography.io) (Fernet + PBKDF2) | Industry-standard primitives, audited library. |
| Storage | SQLite (stdlib `sqlite3`) | Embedded, zero-config, single-file database. |
| GUI | tkinter + ttk (stdlib) | Ships with Python — no extra install. |
| Tests | `unittest` (stdlib) | Standard, no third-party test runner needed. |

---

## How OOP is Used

This project was built deliberately to demonstrate the four pillars of OOP. Each pillar maps to concrete code:

| Pillar | Where it lives |
|---|---|
| **Encapsulation** | `CryptoManager` hides the `Fernet` instance behind `_fernet`; `Vault` keeps `_storage` and `_crypto` private; `PasswordEntry` exposes mutators (`update_password`, `update_username`, `update_notes`) instead of raw attribute writes so `modified_at` is always bumped correctly. |
| **Abstraction** | `VaultStorage` is an `ABC` defining *what* storage must do (`save_meta`, `add_entry`, `get_all_entries`, ...) without saying *how*. The `Vault` only ever talks to this abstract interface. |
| **Inheritance** | `SQLiteStorage` inherits from `VaultStorage` and implements every abstract method. Swapping in a `JSONStorage` or `PostgresStorage` later would just be another subclass — no changes needed in `Vault` or `AuthManager`. |
| **Polymorphism** | `Vault.__init__(storage: VaultStorage, ...)` accepts *any* concrete storage subclass. The same `vault.add(...)` call works regardless of which backend is plugged in. |

Other design patterns / principles applied:

- **Repository pattern** — `VaultStorage` isolates persistence from business logic.
- **Single Responsibility** — every class does one thing: `CryptoManager` only encrypts, `AuthManager` only verifies the master password, `Vault` only orchestrates, `PasswordGenerator` only generates.
- **Dependency Inversion** — `Vault` depends on the `VaultStorage` *abstraction*, not on `SQLiteStorage` directly.

---

## Project Structure

```
PasswordManagerApp/
├── README.md
├── src/
│   ├── password_entry.py       # Domain model (a single saved credential)
│   ├── password_generator.py   # Random password generator
│   ├── crypto_manager.py       # Salt + key derivation + encrypt / decrypt
│   ├── storage.py              # VaultStorage abstract base class
│   ├── sqlite_storage.py       # SQLite implementation of VaultStorage
│   ├── auth_manager.py         # Master-password setup + login (verifier pattern)
│   ├── vault.py                # Orchestrates storage + crypto (CRUD)
│   ├── app.py                  # CLI entry point
│   └── gui_app.py              # tkinter GUI entry point
└── tests/
    ├── test_password_entry.py
    ├── test_password_generator.py
    ├── test_crypto_manager.py
    ├── test_sqlite_storage.py
    ├── test_auth_manager.py
    └── test_vault.py
```

---

## Class Responsibilities

- **`PasswordEntry`** — a single credential record (service, username, password, optional notes, `created_at`, `modified_at`). Validates inputs and bumps `modified_at` on every change.
- **`PasswordGenerator`** — generates cryptographically random passwords using `secrets`. Configurable charset, minimum length 12.
- **`CryptoManager`** — generates a 16-byte random salt, derives a 32-byte key from a master password using PBKDF2-HMAC-SHA256 (200k iterations), and encrypts / decrypts strings with Fernet.
- **`VaultStorage`** — abstract interface defining what any storage backend must support.
- **`SQLiteStorage`** — concrete `VaultStorage` backed by a single SQLite file. Uses parameterized queries (`?` placeholders) — safe against SQL injection.
- **`AuthManager`** — handles first-time vault setup and master-password login using the *verifier pattern*: encrypt a known plaintext (`"PASSWORD_MANAGER_OK"`) on setup, decrypt it on login. Decryption only succeeds with the correct master password.
- **`Vault`** — the high-level CRUD API. Encrypts before writing, decrypts after reading, never persists plaintext.
- **`App` / `PasswordManagerGUI`** — the user-facing layer, CLI and GUI respectively.

---

## Security Model

1. The master password **never touches the disk**.
2. On first launch, a 16-byte salt is generated and stored.
3. PBKDF2-HMAC-SHA256 stretches the master password into a 32-byte key (200,000 iterations).
4. A "verifier" string is encrypted with that key and stored. On login, we try to decrypt it — if it succeeds, the password was correct.
5. Every saved password is encrypted with Fernet before being inserted into SQLite. The raw `vault.db` file shows only ciphertext (e.g. `gAAAAA...`).
6. Forgetting the master password means losing access — there is no recovery, by design.

---

## Installation

Requires Python 3.10 or newer.

```bash
# Clone the repo
git clone https://github.com/ElvinasEnterprises/PasswordManagerApp.git
cd PasswordManagerApp

# Install the one external dependency
pip install cryptography
```

Everything else (`sqlite3`, `tkinter`, `unittest`, `secrets`, `base64`) is in Python's standard library.

---

## Usage

### GUI (recommended)

```bash
python3 src/gui_app.py
```

On first launch you'll be prompted to set a master password. After that, the same command opens the login screen.

### CLI

```bash
python3 src/app.py
```

Walks you through setup / login and exposes the same actions via a numbered menu.

---

## Running the Tests

The project ships with **53 unit tests** covering every backend class.

```bash
cd PasswordManagerApp
python3 -m unittest discover tests -v
```

Each test gets its own isolated temporary SQLite database via `tempfile.mkstemp`, so tests are fully independent.

---

## Author

**Elvinas Bražionis** — VilniusTECH, Object-Oriented Programming course project, 2026.

Repository: <https://github.com/ElvinasEnterprises/PasswordManagerApp>
