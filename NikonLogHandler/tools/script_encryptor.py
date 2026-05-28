"""
script_encryptor.py
===================
Encrypts and decrypts NLH parser scripts using symmetric encryption (Fernet / AES-128-CBC).

Scripts are encrypted before distribution so that:
  - Only authorised NLH installations can load them.
  - The source code is not trivially readable on end-user machines.
  - A per-subsidiary key can be issued so NPE scripts are unreadable by NPI/NPC.

Encrypted file format:
    .pyenc  –  Fernet-encrypted bytes of the original .py source.

Key management:
    Keys are 32-byte secrets encoded as URL-safe base64 (Fernet standard).
    Store keys securely (environment variable, key vault, or locked file).
    Never commit keys to source control.

Usage (CLI):
    # Encrypt a single script
    python script_encryptor.py encrypt my_handler.py --key <base64-key>

    # Decrypt for local inspection
    python script_encryptor.py decrypt my_handler.pyenc --key <base64-key>

    # Generate a new key
    python script_encryptor.py keygen

    # Encrypt all scripts in a subsidiary folder
    python script_encryptor.py encrypt-all NPE --key <base64-key>

Usage (API):
    from tools.script_encryptor import ScriptEncryptor
    enc = ScriptEncryptor(key_b64="<base64-key>")
    enc.encrypt_file(Path("my_handler.py"))
    enc.decrypt_file(Path("my_handler.pyenc"))
"""

from __future__ import annotations

import argparse
import base64
import importlib
import io
import logging
import os
import sys
import types
from pathlib import Path
from typing import Optional

ENCRYPTED_EXTENSION = ".pyenc"
SUBSIDIARIES = ("NPE", "NPI", "NPC")


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def generate_key() -> str:
    """Generate a new Fernet-compatible 32-byte key, returned as base64 string."""
    try:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    except ImportError:
        # Fallback: generate a random 32-byte key encoded as URL-safe base64
        raw = os.urandom(32)
        return base64.urlsafe_b64encode(raw).decode()


def _load_fernet(key_b64: str):
    """Return a Fernet instance from a base64-encoded key string."""
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise RuntimeError(
            "The 'cryptography' package is required for encryption. "
            "Install it with: pip install cryptography"
        ) from exc
    return Fernet(key_b64.encode() if isinstance(key_b64, str) else key_b64)


# ---------------------------------------------------------------------------
# ScriptEncryptor
# ---------------------------------------------------------------------------

class ScriptEncryptor:
    """
    Encrypts and decrypts .py parser scripts.

    Parameters
    ----------
    key_b64 : str
        Fernet key as a URL-safe base64 string.  Generate one with
        ``ScriptEncryptor.generate_key()`` or the ``keygen`` CLI command.
    """

    def __init__(self, key_b64: str):
        self._fernet = _load_fernet(key_b64)

    # ── Static helpers ───────────────────────────────────────────────────────

    @staticmethod
    def generate_key() -> str:
        return generate_key()

    # ── File operations ──────────────────────────────────────────────────────

    def encrypt_file(self, source: Path, dest: Optional[Path] = None) -> Path:
        """
        Encrypt a .py file and write a .pyenc file.

        Parameters
        ----------
        source : Path
            The plaintext .py script to encrypt.
        dest : Path, optional
            Output path.  Defaults to source.with_suffix('.pyenc').

        Returns
        -------
        Path
            Path to the written .pyenc file.
        """
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        plaintext = source.read_bytes()
        ciphertext = self._fernet.encrypt(plaintext)

        if dest is None:
            dest = source.with_suffix(ENCRYPTED_EXTENSION)

        dest.write_bytes(ciphertext)
        logging.info(f"Encrypted: {source} → {dest}")
        return dest

    def decrypt_file(self, source: Path, dest: Optional[Path] = None) -> Path:
        """
        Decrypt a .pyenc file back to .py.

        Parameters
        ----------
        source : Path
            The encrypted .pyenc file.
        dest : Path, optional
            Output path.  Defaults to source.with_suffix('.py').

        Returns
        -------
        Path
            Path to the written .py file.
        """
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        ciphertext = source.read_bytes()
        plaintext = self._fernet.decrypt(ciphertext)

        if dest is None:
            dest = source.with_suffix(".py")

        dest.write_bytes(plaintext)
        logging.info(f"Decrypted: {source} → {dest}")
        return dest

    def decrypt_to_string(self, source: Path) -> str:
        """Decrypt a .pyenc file and return source code as a string."""
        ciphertext = source.read_bytes()
        return self._fernet.decrypt(ciphertext).decode("utf-8")

    def encrypt_directory(self, directory: Path, delete_originals: bool = False) -> list[Path]:
        """
        Encrypt all .py files in a directory (non-recursive, skips _ files).

        Returns list of created .pyenc paths.
        """
        created = []
        for py_file in sorted(directory.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            enc_path = self.encrypt_file(py_file)
            created.append(enc_path)
            if delete_originals:
                py_file.unlink()
                logging.info(f"Removed plaintext: {py_file}")
        return created

    def decrypt_directory(self, directory: Path) -> list[Path]:
        """Decrypt all .pyenc files in a directory. Returns list of .py paths."""
        created = []
        for enc_file in sorted(directory.glob(f"*{ENCRYPTED_EXTENSION}")):
            py_path = self.decrypt_file(enc_file)
            created.append(py_path)
        return created


# ---------------------------------------------------------------------------
# Encrypted plugin loader
# ---------------------------------------------------------------------------

class EncryptedPluginLoader:
    """
    Allows NLH's discovery system to load encrypted (.pyenc) handler scripts
    transparently, without writing the decrypted source to disk.

    Usage in discovery.py (opt-in):
        loader = EncryptedPluginLoader(key_b64=os.environ["NLH_PLUGIN_KEY"])
        module = loader.load(Path("my_handler.pyenc"), "nlh_handler.my_handler")
    """

    def __init__(self, key_b64: str):
        self._encryptor = ScriptEncryptor(key_b64)

    def load(self, enc_path: Path, module_name: str) -> types.ModuleType:
        """
        Decrypt and exec a .pyenc file, returning it as a module.
        The decrypted source is held only in memory – never written to disk.
        """
        source_code = self._encryptor.decrypt_to_string(enc_path)

        spec = importlib.util.spec_from_loader(
            module_name,
            loader=None,
            origin=str(enc_path),
        )
        module = types.ModuleType(module_name)
        module.__file__ = str(enc_path)
        module.__spec__ = spec
        sys.modules[module_name] = module

        code = compile(source_code, str(enc_path), "exec")
        exec(code, module.__dict__)  # noqa: S102

        return module


# ---------------------------------------------------------------------------
# Subsidiary key store  (simple env-var convention)
# ---------------------------------------------------------------------------

SUBSIDIARY_KEY_ENV: dict[str, str] = {
    "NPE": "NLH_KEY_NPE",
    "NPI": "NLH_KEY_NPI",
    "NPC": "NLH_KEY_NPC",
}


def get_subsidiary_key(subsidiary: str) -> Optional[str]:
    """
    Retrieve the encryption key for a subsidiary from environment variables.

    Set keys as:
        export NLH_KEY_NPE=<base64-key>
        export NLH_KEY_NPI=<base64-key>
        export NLH_KEY_NPC=<base64-key>
    """
    env_var = SUBSIDIARY_KEY_ENV.get(subsidiary.upper())
    if env_var is None:
        raise ValueError(f"Unknown subsidiary: {subsidiary}")
    key = os.environ.get(env_var)
    if not key:
        logging.warning(
            f"Key env var '{env_var}' is not set. "
            f"Encrypted scripts for {subsidiary} cannot be loaded."
        )
    return key


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="NLH Script Encryptor – encrypt/decrypt parser scripts"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # keygen
    kg = sub.add_parser("keygen", help="Generate a new encryption key")

    # encrypt
    enc_p = sub.add_parser("encrypt", help="Encrypt a single .py file")
    enc_p.add_argument("source", type=Path, help="Path to .py file")
    enc_p.add_argument("--key", required=True, help="Base64 Fernet key")
    enc_p.add_argument("--delete-original", action="store_true",
                       help="Remove original .py after encrypting")

    # decrypt
    dec_p = sub.add_parser("decrypt", help="Decrypt a single .pyenc file")
    dec_p.add_argument("source", type=Path, help="Path to .pyenc file")
    dec_p.add_argument("--key", required=True, help="Base64 Fernet key")

    # encrypt-all
    ea = sub.add_parser("encrypt-all", help="Encrypt all scripts in a subsidiary folder")
    ea.add_argument("subsidiary", choices=SUBSIDIARIES)
    ea.add_argument("--key", help="Base64 Fernet key (or set NLH_KEY_<SUB> env var)")
    ea.add_argument("--delete-originals", action="store_true")

    # decrypt-all
    da = sub.add_parser("decrypt-all", help="Decrypt all .pyenc files in a subsidiary folder")
    da.add_argument("subsidiary", choices=SUBSIDIARIES)
    da.add_argument("--key", help="Base64 Fernet key (or set NLH_KEY_<SUB> env var)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    repo_root = Path(__file__).resolve().parent.parent

    if args.command == "keygen":
        key = generate_key()
        print(f"New key: {key}")
        print("Store this securely and set as an environment variable.")
        return

    # Resolve key
    if args.command in ("encrypt", "decrypt"):
        key = args.key
    else:
        key = args.key or get_subsidiary_key(args.subsidiary)
        if not key:
            print(f"Error: no key provided. Pass --key or set {SUBSIDIARY_KEY_ENV[args.subsidiary]}")
            sys.exit(1)

    encryptor = ScriptEncryptor(key)

    if args.command == "encrypt":
        out = encryptor.encrypt_file(args.source)
        print(f"Encrypted → {out}")
        if args.delete_original:
            args.source.unlink()
            print(f"Removed {args.source}")

    elif args.command == "decrypt":
        out = encryptor.decrypt_file(args.source)
        print(f"Decrypted → {out}")

    elif args.command == "encrypt-all":
        scripts_dir = repo_root / "subsidiaries" / args.subsidiary / "scripts"
        created = encryptor.encrypt_directory(scripts_dir, delete_originals=args.delete_originals)
        print(f"Encrypted {len(created)} files in {scripts_dir}")

    elif args.command == "decrypt-all":
        scripts_dir = repo_root / "subsidiaries" / args.subsidiary / "scripts"
        created = encryptor.decrypt_directory(scripts_dir)
        print(f"Decrypted {len(created)} files in {scripts_dir}")


if __name__ == "__main__":
    _cli()
