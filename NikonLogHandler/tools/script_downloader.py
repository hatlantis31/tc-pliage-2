"""
script_downloader.py
====================
Downloads parser scripts and documentation from SharePoint for a given subsidiary.

Subsidiaries:
    NPE  – Nikon Precision Europe
    NPI  – Nikon Precision Inc.
    NPC  – Nikon Precision Corporation

The downloader connects to the subsidiary-specific SharePoint folder,
lists available scripts, compares them against locally installed ones,
and downloads new or updated scripts into the subsidiary's scripts/ folder.

Local documentation is read from  subsidiaries/<SUB>/docs/  and does NOT
require a SharePoint connection.

Usage (CLI):
    python script_downloader.py --subsidiary NPE
    python script_downloader.py --subsidiary NPI --force
    python script_downloader.py --all
    python script_downloader.py --list NPE

Usage (API):
    from tools.script_downloader import ScriptDownloader
    dl = ScriptDownloader("NPE")
    dl.authenticate("user@nikon.com", "password")
    dl.sync_scripts()
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Subsidiary configuration
# ---------------------------------------------------------------------------

SUBSIDIARIES: dict[str, dict] = {
    "NPE": {
        "name": "Nikon Precision Europe",
        "sharepoint_url": "https://nikonglobaleu.sharepoint.com/sites/NPE-ESHardware/",
        "sharepoint_scripts_folder": "/sites/NPE-ESHardware/Nikon%20Log%20Handler/Scripts/",
        "sharepoint_docs_folder": "/sites/NPE-ESHardware/Nikon%20Log%20Handler/Handlers_doc/",
        "local_scripts_dir": None,   # resolved at runtime
        "local_docs_dir": None,
    },
    "NPI": {
        "name": "Nikon Precision Inc.",
        "sharepoint_url": "https://nikonprecision.sharepoint.com/sites/NPI-Engineering/",
        "sharepoint_scripts_folder": "/sites/NPI-Engineering/Nikon%20Log%20Handler/Scripts/",
        "sharepoint_docs_folder": "/sites/NPI-Engineering/Nikon%20Log%20Handler/Handlers_doc/",
        "local_scripts_dir": None,
        "local_docs_dir": None,
    },
    "NPC": {
        "name": "Nikon Precision Corporation",
        "sharepoint_url": "https://nikonprecision.sharepoint.com/sites/NPC-Engineering/",
        "sharepoint_scripts_folder": "/sites/NPC-Engineering/Nikon%20Log%20Handler/Scripts/",
        "sharepoint_docs_folder": "/sites/NPC-Engineering/Nikon%20Log%20Handler/Handlers_doc/",
        "local_scripts_dir": None,
        "local_docs_dir": None,
    },
}

# ---------------------------------------------------------------------------
# Root resolution
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    """Return the NikonLogHandler root regardless of CWD."""
    return Path(__file__).resolve().parent.parent


def _resolve_paths(config: dict, subsidiary: str) -> dict:
    root = _repo_root()
    config = config.copy()
    config["local_scripts_dir"] = root / "subsidiaries" / subsidiary / "scripts"
    config["local_docs_dir"] = root / "subsidiaries" / subsidiary / "docs"
    return config


# ---------------------------------------------------------------------------
# Script manifest  (tracks installed scripts and their checksums)
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = ".script_manifest.json"


@dataclass
class ScriptEntry:
    filename: str
    checksum: str
    downloaded_at: str
    version: str = "unknown"
    subsidiary: str = ""


class ScriptManifest:
    """Tracks which scripts are installed locally and their SHA-256 checksums."""

    def __init__(self, scripts_dir: Path):
        self._path = scripts_dir / MANIFEST_FILENAME
        self._entries: dict[str, ScriptEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                for name, entry in data.items():
                    self._entries[name] = ScriptEntry(**entry)
            except Exception as exc:
                logging.warning(f"Manifest load failed: {exc} – starting fresh")

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {name: vars(e) for name, e in self._entries.items()}
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, filename: str) -> Optional[ScriptEntry]:
        return self._entries.get(filename)

    def add(self, entry: ScriptEntry) -> None:
        self._entries[entry.filename] = entry

    def remove(self, filename: str) -> None:
        self._entries.pop(filename, None)

    def all_entries(self) -> list[ScriptEntry]:
        return list(self._entries.values())

    @staticmethod
    def checksum(path: Path) -> str:
        sha = hashlib.sha256()
        sha.update(path.read_bytes())
        return sha.hexdigest()


# ---------------------------------------------------------------------------
# ScriptDownloader
# ---------------------------------------------------------------------------

@dataclass
class DownloadResult:
    downloaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


class ScriptDownloader:
    """
    Manages downloading parser scripts from SharePoint for one subsidiary.

    Parameters
    ----------
    subsidiary : str
        One of 'NPE', 'NPI', 'NPC'.
    force : bool
        When True, re-download scripts even if the checksum hasn't changed.
    """

    def __init__(self, subsidiary: str, force: bool = False):
        subsidiary = subsidiary.upper()
        if subsidiary not in SUBSIDIARIES:
            raise ValueError(f"Unknown subsidiary '{subsidiary}'. Choose from: {list(SUBSIDIARIES)}")

        self.subsidiary = subsidiary
        self.force = force
        self.config = _resolve_paths(SUBSIDIARIES[subsidiary], subsidiary)
        self._sp: Optional[object] = None  # SharePointHandler, imported lazily
        self._manifest = ScriptManifest(self.config["local_scripts_dir"])

    # ── Authentication ───────────────────────────────────────────────────────

    def authenticate(self) -> bool:
        """
        Authenticate to the subsidiary SharePoint site using interactive login.
        Returns True on success.
        """
        try:
            sys.path.insert(0, str(_repo_root() / "framework"))
            from main_app_files.function_files._sharepoint_handling import SharePointHandler
            self._sp = SharePointHandler(
                sharepoint_url=self.config["sharepoint_url"],
                auto_authenticate=True,
            )
            if not self._sp.is_authenticated:
                logging.error(f"Authentication failed: {self._sp.authentication_error}")
            return self._sp.is_authenticated
        except Exception as exc:
            logging.error(f"Authentication error: {exc}")
            return False

    # ── Script syncing ───────────────────────────────────────────────────────

    def list_remote_scripts(self) -> list[dict]:
        """
        Return a list of available scripts on SharePoint.
        Each entry: {'name': str, 'size': int}
        """
        self._require_auth()
        try:
            from office365.sharepoint.client_context import ClientContext
            folder_url = self.config["sharepoint_scripts_folder"].replace("%20", " ")
            folder = self._sp.ctx.web.get_folder_by_server_relative_url(folder_url)
            files = folder.files
            self._sp.ctx.load(files)
            self._sp.ctx.execute_query()
            return [
                {"name": f.properties["Name"], "size": f.length}
                for f in files
                if f.properties["Name"].endswith(".py")
            ]
        except Exception as exc:
            logging.error(f"Failed to list remote scripts: {exc}")
            return []

    def sync_scripts(self) -> DownloadResult:
        """
        Download new/updated scripts from SharePoint to the local scripts dir.
        Returns a DownloadResult summary.
        """
        self._require_auth()
        result = DownloadResult()
        scripts_dir: Path = self.config["local_scripts_dir"]
        scripts_dir.mkdir(parents=True, exist_ok=True)

        remote_scripts = self.list_remote_scripts()
        if not remote_scripts:
            logging.warning("No remote scripts found or listing failed.")
            return result

        remote_names = {s["name"] for s in remote_scripts}

        for script in remote_scripts:
            name = script["name"]
            local_path = scripts_dir / name
            try:
                if local_path.exists() and not self.force:
                    existing_checksum = ScriptManifest.checksum(local_path)
                    entry = self._manifest.get(name)
                    if entry and entry.checksum == existing_checksum:
                        logging.info(f"Skipping {name} – up to date")
                        result.skipped.append(name)
                        continue

                logging.info(f"Downloading {name}…")
                dest = self._sp.load_file_from_sharepoint(
                    sharepoint_folder=self.config["sharepoint_scripts_folder"],
                    file_to_download=name,
                    output_file_location=str(scripts_dir) + os.sep,
                )
                if dest.startswith("Error"):
                    logging.error(f"Download failed for {name}: {dest}")
                    result.failed.append(name)
                else:
                    checksum = ScriptManifest.checksum(local_path)
                    self._manifest.add(ScriptEntry(
                        filename=name,
                        checksum=checksum,
                        downloaded_at=datetime.utcnow().isoformat(),
                        subsidiary=self.subsidiary,
                    ))
                    result.downloaded.append(name)

            except Exception as exc:
                logging.error(f"Error downloading {name}: {exc}")
                result.failed.append(name)

        self._manifest.save()
        return result

    def download_single(self, script_name: str) -> bool:
        """Download a single named script. Returns True on success."""
        self._require_auth()
        scripts_dir: Path = self.config["local_scripts_dir"]
        scripts_dir.mkdir(parents=True, exist_ok=True)

        dest = self._sp.load_file_from_sharepoint(
            sharepoint_folder=self.config["sharepoint_scripts_folder"],
            file_to_download=script_name,
            output_file_location=str(scripts_dir) + os.sep,
        )
        if dest.startswith("Error"):
            logging.error(f"Download failed: {dest}")
            return False

        local_path = scripts_dir / script_name
        checksum = ScriptManifest.checksum(local_path)
        self._manifest.add(ScriptEntry(
            filename=script_name,
            checksum=checksum,
            downloaded_at=datetime.utcnow().isoformat(),
            subsidiary=self.subsidiary,
        ))
        self._manifest.save()
        return True

    # ── Local documentation ──────────────────────────────────────────────────

    def list_local_docs(self) -> list[dict]:
        """
        List all documentation files in the local docs/ folder.
        Returns a list of {'name': str, 'path': Path, 'size_kb': float}.
        Does NOT require SharePoint authentication.
        """
        docs_dir: Path = self.config["local_docs_dir"]
        if not docs_dir.exists():
            return []
        result = []
        for f in sorted(docs_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in {".pdf", ".docx", ".md", ".txt"}:
                result.append({
                    "name": f.name,
                    "path": f,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
        return result

    def open_doc(self, doc_name: str) -> bool:
        """Open a local documentation file with the system default app."""
        import subprocess
        docs_dir: Path = self.config["local_docs_dir"]
        doc_path = docs_dir / doc_name
        if not doc_path.exists():
            logging.error(f"Doc not found: {doc_path}")
            return False
        try:
            os.startfile(str(doc_path))
            return True
        except AttributeError:
            subprocess.run(["xdg-open", str(doc_path)], check=True)
            return True

    # ── Installed scripts ────────────────────────────────────────────────────

    def list_installed_scripts(self) -> list[ScriptEntry]:
        """Return locally installed scripts from the manifest."""
        return self._manifest.all_entries()

    def remove_script(self, script_name: str) -> bool:
        """Delete a locally installed script and remove it from the manifest."""
        scripts_dir: Path = self.config["local_scripts_dir"]
        local_path = scripts_dir / script_name
        if local_path.exists():
            local_path.unlink()
        self._manifest.remove(script_name)
        self._manifest.save()
        return True

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _require_auth(self) -> None:
        if self._sp is None or not self._sp.is_authenticated:
            raise RuntimeError(
                "Not authenticated. Call authenticate() before syncing scripts."
            )

    def report(self, result: DownloadResult) -> str:
        lines = [
            f"[{self.subsidiary}] Sync complete",
            f"  Downloaded : {len(result.downloaded)} — {result.downloaded}",
            f"  Skipped    : {len(result.skipped)}",
            f"  Failed     : {len(result.failed)} — {result.failed}",
            f"  Removed    : {len(result.removed)}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="NLH Script Downloader – sync parser scripts from SharePoint"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--subsidiary", metavar="SUB",
                       help="Subsidiary code: NPE | NPI | NPC")
    group.add_argument("--all", action="store_true",
                       help="Sync scripts for all subsidiaries")
    group.add_argument("--list", metavar="SUB",
                       help="List installed scripts for a subsidiary (no auth needed)")
    group.add_argument("--list-docs", metavar="SUB",
                       help="List local documentation files for a subsidiary")

    parser.add_argument("--force", action="store_true",
                        help="Re-download even if checksum matches")
    parser.add_argument("--download", metavar="SCRIPT",
                        help="Download a single script by name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.list:
        dl = ScriptDownloader(args.list, force=args.force)
        entries = dl.list_installed_scripts()
        if not entries:
            print(f"No scripts installed for {args.list.upper()}")
        for e in entries:
            print(f"  {e.filename}  (downloaded {e.downloaded_at[:10]})")
        return

    if args.list_docs:
        dl = ScriptDownloader(args.list_docs)
        docs = dl.list_local_docs()
        if not docs:
            print(f"No docs found for {args.list_docs.upper()}")
        for d in docs:
            print(f"  {d['name']}  ({d['size_kb']} KB)")
        return

    targets = list(SUBSIDIARIES.keys()) if args.all else [args.subsidiary]

    for sub in targets:
        print(f"\n{'='*50}")
        print(f" Syncing {sub} ({SUBSIDIARIES[sub.upper()]['name']})")
        print(f"{'='*50}")
        dl = ScriptDownloader(sub, force=args.force)

        if not dl.authenticate():
            print(f"Authentication failed for {sub}. Skipping.")
            continue

        if args.download:
            ok = dl.download_single(args.download)
            print(f"{'OK' if ok else 'FAILED'}: {args.download}")
        else:
            result = dl.sync_scripts()
            print(dl.report(result))


if __name__ == "__main__":
    _cli()
