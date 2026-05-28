"""
package_subsidiary.py
=====================
Packages a subsidiary's scripts and documentation into a distributable .zip file.

Each zip contains:
    scripts/     All .py or .pyenc parser scripts
    docs/        All documentation files
    README.md    Subsidiary readme

Usage:
    python tools/package_subsidiary.py NPE
    python tools/package_subsidiary.py --all
    python tools/package_subsidiary.py NPE --output C:\\Releases\\
    python tools/package_subsidiary.py NPE --encrypt --key <base64-key>
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SUBSIDIARIES = ("NPE", "NPI", "NPC")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def package_subsidiary(
    subsidiary: str,
    output_dir: Path,
    encrypt: bool = False,
    key_b64: str = "",
) -> Path:
    """
    Create a zip package for one subsidiary.

    Parameters
    ----------
    subsidiary : str
        NPE, NPI, or NPC.
    output_dir : Path
        Directory where the .zip will be written.
    encrypt : bool
        Encrypt .py scripts before zipping.
    key_b64 : str
        Fernet key for encryption (required if encrypt=True).

    Returns
    -------
    Path
        Path to the created zip file.
    """
    root = _repo_root()
    sub = subsidiary.upper()
    sub_dir = root / "subsidiaries" / sub

    if not sub_dir.exists():
        raise FileNotFoundError(f"Subsidiary directory not found: {sub_dir}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_name = f"NLH-Scripts-{sub}_{timestamp}.zip"
    zip_path = output_dir / zip_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Optionally encrypt scripts first
    if encrypt:
        if not key_b64:
            raise ValueError("Encryption key required when --encrypt is set")
        sys.path.insert(0, str(root / "tools"))
        from script_encryptor import ScriptEncryptor
        encryptor = ScriptEncryptor(key_b64)
        scripts_dir = sub_dir / "scripts"
        encryptor.encrypt_directory(scripts_dir, delete_originals=False)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(sub_dir.rglob("*")):
            if file_path.is_file():
                # Skip manifest and pycache
                if any(p in file_path.parts for p in ("__pycache__",)):
                    continue
                if file_path.name == ".script_manifest.json":
                    continue
                arcname = file_path.relative_to(sub_dir)
                zf.write(file_path, arcname)

    print(f"Packaged {sub} → {zip_path}  ({zip_path.stat().st_size // 1024} KB)")
    return zip_path


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="NLH Subsidiary Packager – create distributable zip files"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("subsidiary", nargs="?", choices=SUBSIDIARIES,
                       help="Subsidiary to package")
    group.add_argument("--all", action="store_true",
                       help="Package all three subsidiaries")

    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent.parent / "dist",
                        help="Output directory for zip files (default: NikonLogHandler/dist/)")
    parser.add_argument("--encrypt", action="store_true",
                        help="Encrypt parser scripts before packaging")
    parser.add_argument("--key", default="",
                        help="Fernet encryption key (required with --encrypt)")

    args = parser.parse_args()
    targets = list(SUBSIDIARIES) if args.all else [args.subsidiary]

    for sub in targets:
        try:
            package_subsidiary(sub, args.output, encrypt=args.encrypt, key_b64=args.key)
        except Exception as exc:
            print(f"ERROR packaging {sub}: {exc}")


if __name__ == "__main__":
    _cli()
