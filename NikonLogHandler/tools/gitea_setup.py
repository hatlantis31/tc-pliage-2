"""
gitea_setup.py
==============
Creates three subsidiary Gitea repositories for NLH parser scripts
and optionally archives (removes) the legacy monorepo parsers.

Repositories created:
    NLH-Scripts-NPE  –  Nikon Precision Europe parsers
    NLH-Scripts-NPI  –  Nikon Precision Inc. parsers
    NLH-Scripts-NPC  –  Nikon Precision Corporation parsers

Each repo is pre-seeded with:
    - scripts/           Parser .py (or .pyenc) files
    - docs/              Local documentation
    - README.md          Auto-generated from subsidiary config
    - .gitignore         Appropriate Python ignores

Usage:
    python gitea_setup.py create-all --gitea-url http://your-gitea --token <pat>
    python gitea_setup.py create NPE --gitea-url http://your-gitea --token <pat>
    python gitea_setup.py delete NPE --gitea-url http://your-gitea --token <pat>
    python gitea_setup.py status --gitea-url http://your-gitea --token <pat>
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Subsidiary configuration
# ---------------------------------------------------------------------------

SUBSIDIARIES: dict[str, dict] = {
    "NPE": {
        "name": "Nikon Precision Europe",
        "repo_name": "NLH-Scripts-NPE",
        "description": "NLH parser scripts for Nikon Precision Europe (NPE-ES Hardware)",
        "topics": ["nikon", "nlh", "log-handler", "npe"],
        "gitea_org": None,   # set to org name if repos should be org-owned
    },
    "NPI": {
        "name": "Nikon Precision Inc.",
        "repo_name": "NLH-Scripts-NPI",
        "description": "NLH parser scripts for Nikon Precision Inc. (US)",
        "topics": ["nikon", "nlh", "log-handler", "npi"],
        "gitea_org": None,
    },
    "NPC": {
        "name": "Nikon Precision Corporation",
        "repo_name": "NLH-Scripts-NPC",
        "description": "NLH parser scripts for Nikon Precision Corporation",
        "topics": ["nikon", "nlh", "log-handler", "npc"],
        "gitea_org": None,
    },
}

GITIGNORE_CONTENT = """\
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.pyenc.bak
.script_manifest.json
*.log
.env
"""

README_TEMPLATE = """\
# NLH Scripts – {name} ({sub})

> **Nikon Confidential – Internal Use Only**

This repository contains parser scripts for the **Nikon Log Handler (NLH)**
framework, maintained by the {name} team.

## Repository Structure

```
scripts/      NLH parser scripts (.py or .pyenc)
docs/         Local documentation for each parser
```

## Adding a New Parser

1. Follow the [NLH Parser Development Guide](../dev_kit/HOW_TO_ADD_A_PARSER.md)
2. Place your script in `scripts/`
3. Add documentation to `docs/`
4. Open a Pull Request and fill in the Parser Request template

## Questions / Issues

Use the [NLH Bug Tracker](../bug_tracker/) or email the NLH team.
"""


# ---------------------------------------------------------------------------
# Gitea API client (thin wrapper)
# ---------------------------------------------------------------------------

class GiteaClient:
    """Minimal REST client for the Gitea API v1."""

    def __init__(self, base_url: str, token: str):
        if not REQUESTS_AVAILABLE:
            raise RuntimeError(
                "'requests' is required. Install with: pip install requests"
            )
        self.base = base_url.rstrip("/") + "/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def get_user(self) -> dict:
        return self._get("/user")

    def repo_exists(self, owner: str, repo: str) -> bool:
        resp = self.session.get(f"{self.base}/repos/{owner}/{repo}")
        return resp.status_code == 200

    def create_repo(self, name: str, description: str, private: bool = True,
                    org: Optional[str] = None) -> dict:
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True,
            "default_branch": "main",
        }
        if org:
            url = f"{self.base}/orgs/{org}/repos"
        else:
            url = f"{self.base}/user/repos"
        resp = self.session.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def delete_repo(self, owner: str, repo: str) -> bool:
        resp = self.session.delete(f"{self.base}/repos/{owner}/{repo}")
        return resp.status_code == 204

    def create_file(self, owner: str, repo: str, path: str,
                    content: str, message: str = "Initial commit") -> dict:
        import base64
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        resp = self.session.post(
            f"{self.base}/repos/{owner}/{repo}/contents/{path}",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def add_topics(self, owner: str, repo: str, topics: list[str]) -> None:
        resp = self.session.put(
            f"{self.base}/repos/{owner}/{repo}/topics",
            json={"topics": topics},
        )
        resp.raise_for_status()

    def list_repos(self, owner: str) -> list[dict]:
        return self._get(f"/users/{owner}/repos")

    def _get(self, path: str) -> dict | list:
        resp = self.session.get(f"{self.base}{path}")
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Repository manager
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


class SubsidiaryRepoManager:
    """Creates and seeds Gitea repositories for NLH subsidiaries."""

    def __init__(self, gitea_url: str, token: str):
        self.client = GiteaClient(gitea_url, token)
        self._user = self.client.get_user()
        self.owner = self._user["login"]
        logging.info(f"Authenticated as '{self.owner}'")

    def create_repo(self, subsidiary: str) -> str:
        """
        Create and seed a Gitea repo for the given subsidiary.
        Returns the clone URL.
        """
        sub = subsidiary.upper()
        cfg = SUBSIDIARIES[sub]
        org = cfg.get("gitea_org")
        owner = org or self.owner

        repo_name = cfg["repo_name"]

        if self.client.repo_exists(owner, repo_name):
            logging.warning(f"Repo '{repo_name}' already exists – skipping creation")
        else:
            data = self.client.create_repo(
                name=repo_name,
                description=cfg["description"],
                private=True,
                org=org,
            )
            logging.info(f"Created repo: {data.get('html_url')}")

            if cfg.get("topics"):
                self.client.add_topics(owner, repo_name, cfg["topics"])

        # Seed README
        self._seed_readme(owner, repo_name, sub, cfg)

        # Seed .gitignore
        try:
            self.client.create_file(
                owner, repo_name, ".gitignore",
                GITIGNORE_CONTENT,
                "chore: add .gitignore",
            )
        except Exception:
            pass  # already exists if auto_init created it

        repo_url = f"{self.client.base.replace('/api/v1', '')}/{owner}/{repo_name}"
        logging.info(f"Repo ready: {repo_url}")
        return repo_url

    def _seed_readme(self, owner: str, repo_name: str, sub: str, cfg: dict) -> None:
        content = README_TEMPLATE.format(name=cfg["name"], sub=sub)
        try:
            self.client.create_file(
                owner, repo_name, "README.md",
                content,
                f"docs: add {sub} NLH scripts README",
            )
        except Exception:
            pass  # README already exists from auto_init

        # Create placeholder dirs
        for path, msg in [
            ("scripts/.gitkeep", f"chore: create scripts/ folder for {sub}"),
            ("docs/.gitkeep", f"chore: create docs/ folder for {sub}"),
        ]:
            try:
                self.client.create_file(owner, repo_name, path, "", msg)
            except Exception:
                pass

    def push_local_scripts(self, subsidiary: str) -> None:
        """
        Push locally staged scripts to the Gitea repo via git CLI.
        Requires git to be installed.
        """
        sub = subsidiary.upper()
        cfg = SUBSIDIARIES[sub]
        org = cfg.get("gitea_org")
        owner = org or self.owner
        repo_name = cfg["repo_name"]

        local_sub_dir = _repo_root() / "subsidiaries" / sub
        if not local_sub_dir.exists():
            logging.error(f"Local directory not found: {local_sub_dir}")
            return

        # Clone and push
        base_url = self.client.base.replace("/api/v1", "")
        clone_url = f"{base_url}/{owner}/{repo_name}.git"

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(["git", "clone", clone_url, str(tmp_path)], check=True)

            # Copy local files
            import shutil
            for item in local_sub_dir.iterdir():
                dest = tmp_path / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(dest), dirs_exist_ok=True)
                else:
                    shutil.copy2(str(item), str(dest))

            subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
            subprocess.run([
                "git", "-C", str(tmp_path), "commit", "-m",
                f"feat: add {sub} parser scripts and docs"
            ], check=False)
            subprocess.run(["git", "-C", str(tmp_path), "push"], check=True)

    def delete_repo(self, subsidiary: str) -> bool:
        sub = subsidiary.upper()
        cfg = SUBSIDIARIES[sub]
        org = cfg.get("gitea_org")
        owner = org or self.owner
        repo_name = cfg["repo_name"]

        ok = self.client.delete_repo(owner, repo_name)
        if ok:
            logging.info(f"Deleted repo: {repo_name}")
        else:
            logging.warning(f"Could not delete repo: {repo_name}")
        return ok

    def status(self) -> list[dict]:
        repos = self.client.list_repos(self.owner)
        nlh_repos = [r for r in repos if "NLH-Scripts" in r.get("name", "")]
        return nlh_repos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="NLH Gitea Setup – create/manage subsidiary script repos"
    )
    parser.add_argument("--gitea-url", required=True,
                        help="Gitea base URL, e.g. http://npe-apgit01.nikonoa.net")
    parser.add_argument("--token", default=os.environ.get("GITEA_TOKEN"),
                        help="Personal access token (or set GITEA_TOKEN env var)")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("create-all", help="Create repos for all 3 subsidiaries")

    cr = sub.add_parser("create", help="Create a single subsidiary repo")
    cr.add_argument("subsidiary", choices=list(SUBSIDIARIES))

    dl = sub.add_parser("delete", help="Delete a subsidiary repo")
    dl.add_argument("subsidiary", choices=list(SUBSIDIARIES))

    sub.add_parser("status", help="List NLH repos on the Gitea server")

    push = sub.add_parser("push", help="Push local scripts to Gitea repo")
    push.add_argument("subsidiary", choices=list(SUBSIDIARIES))

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.token:
        print("Error: Gitea token required. Pass --token or set GITEA_TOKEN.")
        sys.exit(1)

    mgr = SubsidiaryRepoManager(args.gitea_url, args.token)

    if args.command == "create-all":
        for s in SUBSIDIARIES:
            url = mgr.create_repo(s)
            print(f"  {s}: {url}")

    elif args.command == "create":
        url = mgr.create_repo(args.subsidiary)
        print(f"Created: {url}")

    elif args.command == "delete":
        ok = mgr.delete_repo(args.subsidiary)
        print("Deleted." if ok else "Failed.")

    elif args.command == "status":
        repos = mgr.status()
        if not repos:
            print("No NLH script repos found.")
        for r in repos:
            print(f"  {r['name']}  ({r.get('html_url', '')})")

    elif args.command == "push":
        mgr.push_local_scripts(args.subsidiary)


if __name__ == "__main__":
    _cli()
