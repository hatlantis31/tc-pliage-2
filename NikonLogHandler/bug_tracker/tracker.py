"""
tracker.py
==========
Lightweight JSON-based issue tracker for NLH bugs, parser requests,
feature requests, and improvements.

Issues are stored in  bug_tracker/issues.json  and can be managed via
CLI or imported as a Python API.

Usage (CLI):
    python bug_tracker/tracker.py list
    python bug_tracker/tracker.py list --type bug --status open
    python bug_tracker/tracker.py new bug
    python bug_tracker/tracker.py new parser-request
    python bug_tracker/tracker.py show 42
    python bug_tracker/tracker.py close 42
    python bug_tracker/tracker.py comment 42 "Fixed in v4.1"
    python bug_tracker/tracker.py export --format csv

Usage (API):
    from bug_tracker.tracker import IssueTracker
    tracker = IssueTracker()
    issue = tracker.create(type="bug", title="Parser crashes on empty file", ...)
    tracker.close(issue.id)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

IssueType = Literal["bug", "parser-request", "feature", "improvement"]
IssueStatus = Literal["open", "in-progress", "resolved", "wont-fix", "duplicate"]

VALID_TYPES: tuple = ("bug", "parser-request", "feature", "improvement")
VALID_STATUSES: tuple = ("open", "in-progress", "resolved", "wont-fix", "duplicate")
VALID_PRIORITIES: tuple = ("critical", "high", "medium", "low")
VALID_SUBSIDIARIES: tuple = ("NPE", "NPI", "NPC", "All")


@dataclass
class Comment:
    author: str
    text: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Issue:
    id: int
    type: IssueType
    title: str
    description: str
    status: IssueStatus
    priority: str
    subsidiary: str
    reporter: str
    assignee: str
    created_at: str
    updated_at: str
    tags: list[str] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Issue":
        comments = [Comment(**c) for c in data.pop("comments", [])]
        issue = cls(**data)
        issue.comments = comments
        return issue

    def add_comment(self, text: str, author: str = "unknown") -> None:
        self.comments.append(Comment(author=author, text=text))
        self.updated_at = datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

ISSUES_FILE = Path(__file__).parent / "issues.json"


class IssueStore:
    def __init__(self, path: Path = ISSUES_FILE):
        self._path = path
        self._issues: dict[int, Issue] = {}
        self._next_id = 1
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                for item in data.get("issues", []):
                    issue = Issue.from_dict(item)
                    self._issues[issue.id] = issue
                self._next_id = data.get("next_id", 1)
            except Exception as exc:
                print(f"Warning: could not load issues: {exc}")

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "next_id": self._next_id,
            "issues": [i.to_dict() for i in self._issues.values()],
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, issue: Issue) -> None:
        self._issues[issue.id] = issue
        self._next_id = max(self._next_id, issue.id + 1)
        self.save()

    def get(self, issue_id: int) -> Optional[Issue]:
        return self._issues.get(issue_id)

    def all_issues(self) -> list[Issue]:
        return sorted(self._issues.values(), key=lambda i: i.id)

    def next_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid


# ---------------------------------------------------------------------------
# IssueTracker (public API)
# ---------------------------------------------------------------------------

class IssueTracker:
    def __init__(self, store_path: Path = ISSUES_FILE):
        self._store = IssueStore(store_path)

    def create(
        self,
        type: IssueType,
        title: str,
        description: str = "",
        priority: str = "medium",
        subsidiary: str = "All",
        reporter: str = "",
        assignee: str = "",
        tags: Optional[list[str]] = None,
    ) -> Issue:
        now = datetime.utcnow().isoformat()
        issue = Issue(
            id=self._store.next_id(),
            type=type,
            title=title,
            description=description,
            status="open",
            priority=priority,
            subsidiary=subsidiary,
            reporter=reporter,
            assignee=assignee,
            created_at=now,
            updated_at=now,
            tags=tags or [],
        )
        self._store.add(issue)
        return issue

    def get(self, issue_id: int) -> Optional[Issue]:
        return self._store.get(issue_id)

    def list(
        self,
        type: Optional[str] = None,
        status: Optional[str] = None,
        subsidiary: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> list[Issue]:
        issues = self._store.all_issues()
        if type:
            issues = [i for i in issues if i.type == type]
        if status:
            issues = [i for i in issues if i.status == status]
        if subsidiary:
            issues = [i for i in issues if i.subsidiary.upper() == subsidiary.upper()]
        if priority:
            issues = [i for i in issues if i.priority == priority]
        return issues

    def update_status(self, issue_id: int, status: IssueStatus) -> bool:
        issue = self._store.get(issue_id)
        if issue is None:
            return False
        issue.status = status
        issue.updated_at = datetime.utcnow().isoformat()
        self._store.save()
        return True

    def close(self, issue_id: int) -> bool:
        return self.update_status(issue_id, "resolved")

    def assign(self, issue_id: int, assignee: str) -> bool:
        issue = self._store.get(issue_id)
        if issue is None:
            return False
        issue.assignee = assignee
        issue.updated_at = datetime.utcnow().isoformat()
        self._store.save()
        return True

    def comment(self, issue_id: int, text: str, author: str = "unknown") -> bool:
        issue = self._store.get(issue_id)
        if issue is None:
            return False
        issue.add_comment(text, author)
        self._store.save()
        return True

    def export_csv(self, output_path: Optional[Path] = None) -> Path:
        if output_path is None:
            output_path = ISSUES_FILE.parent / "issues_export.csv"
        issues = self._store.all_issues()
        fieldnames = [
            "id", "type", "title", "status", "priority",
            "subsidiary", "reporter", "assignee", "created_at", "updated_at", "tags",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for issue in issues:
                row = {k: getattr(issue, k) for k in fieldnames}
                row["tags"] = ", ".join(issue.tags)
                writer.writerow(row)
        return output_path

    def stats(self) -> dict:
        issues = self._store.all_issues()
        return {
            "total": len(issues),
            "by_type": {t: sum(1 for i in issues if i.type == t) for t in VALID_TYPES},
            "by_status": {s: sum(1 for i in issues if i.status == s) for s in VALID_STATUSES},
            "by_priority": {p: sum(1 for i in issues if i.priority == p) for p in VALID_PRIORITIES},
        }


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_issue_list(issues: list[Issue]) -> None:
    if not issues:
        print("  (no issues found)")
        return
    fmt = "{:<5} {:<14} {:<12} {:<8} {:<6}  {}"
    print(fmt.format("ID", "TYPE", "STATUS", "PRI", "SUB", "TITLE"))
    print("-" * 80)
    for i in issues:
        print(fmt.format(
            f"#{i.id}", i.type, i.status, i.priority, i.subsidiary, i.title[:50]
        ))


def _print_issue_detail(issue: Issue) -> None:
    print(f"\n{'='*60}")
    print(f"  #{issue.id}  [{issue.type.upper()}]  {issue.title}")
    print(f"{'='*60}")
    print(f"  Status    : {issue.status}")
    print(f"  Priority  : {issue.priority}")
    print(f"  Subsidiary: {issue.subsidiary}")
    print(f"  Reporter  : {issue.reporter}")
    print(f"  Assignee  : {issue.assignee or '(unassigned)'}")
    print(f"  Created   : {issue.created_at[:10]}")
    print(f"  Updated   : {issue.updated_at[:10]}")
    if issue.tags:
        print(f"  Tags      : {', '.join(issue.tags)}")
    if issue.description:
        print(f"\n  Description:\n  {issue.description}")
    if issue.comments:
        print(f"\n  Comments ({len(issue.comments)}):")
        for c in issue.comments:
            print(f"    [{c.timestamp[:10]}] {c.author}: {c.text}")
    print()


def _prompt(label: str, choices: Optional[tuple] = None, default: str = "") -> str:
    if choices:
        label = f"{label} [{'/'.join(choices)}]"
    if default:
        label = f"{label} (default: {default})"
    label += ": "
    while True:
        val = input(label).strip() or default
        if choices and val not in choices:
            print(f"  Please choose one of: {', '.join(choices)}")
            continue
        return val


def _interactive_new(issue_type: str) -> dict:
    print(f"\nCreating new {issue_type}...")
    data = {
        "type": issue_type,
        "title": input("Title: ").strip(),
        "description": input("Description (one line): ").strip(),
        "priority": _prompt("Priority", VALID_PRIORITIES, "medium"),
        "subsidiary": _prompt("Subsidiary", VALID_SUBSIDIARIES, "All"),
        "reporter": input("Your name/email: ").strip(),
        "assignee": input("Assignee (leave blank if unknown): ").strip(),
        "tags": [t.strip() for t in input("Tags (comma-separated): ").split(",") if t.strip()],
    }
    return data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(description="NLH Issue Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    ls = sub.add_parser("list", help="List issues")
    ls.add_argument("--type", choices=VALID_TYPES)
    ls.add_argument("--status", choices=VALID_STATUSES)
    ls.add_argument("--sub", "--subsidiary", dest="subsidiary")
    ls.add_argument("--priority", choices=VALID_PRIORITIES)

    # new
    new = sub.add_parser("new", help="Create a new issue interactively")
    new.add_argument("type", choices=VALID_TYPES)

    # show
    show = sub.add_parser("show", help="Show issue details")
    show.add_argument("id", type=int)

    # close
    cl = sub.add_parser("close", help="Mark issue as resolved")
    cl.add_argument("id", type=int)

    # status
    st = sub.add_parser("status", help="Change issue status")
    st.add_argument("id", type=int)
    st.add_argument("status", choices=VALID_STATUSES)

    # comment
    cm = sub.add_parser("comment", help="Add a comment to an issue")
    cm.add_argument("id", type=int)
    cm.add_argument("text")
    cm.add_argument("--author", default=os.environ.get("USER", "unknown"))

    # assign
    asn = sub.add_parser("assign", help="Assign an issue")
    asn.add_argument("id", type=int)
    asn.add_argument("assignee")

    # stats
    sub.add_parser("stats", help="Show issue statistics")

    # export
    exp = sub.add_parser("export", help="Export issues to CSV")
    exp.add_argument("--output", type=Path)
    exp.add_argument("--format", choices=["csv"], default="csv")

    args = parser.parse_args()
    tracker = IssueTracker()

    if args.command == "list":
        issues = tracker.list(
            type=args.type, status=args.status,
            subsidiary=args.subsidiary, priority=args.priority,
        )
        _print_issue_list(issues)

    elif args.command == "new":
        data = _interactive_new(args.type)
        issue = tracker.create(**data)
        print(f"\nCreated issue #{issue.id}: {issue.title}")

    elif args.command == "show":
        issue = tracker.get(args.id)
        if issue:
            _print_issue_detail(issue)
        else:
            print(f"Issue #{args.id} not found.")

    elif args.command == "close":
        ok = tracker.close(args.id)
        print(f"Issue #{args.id} {'closed.' if ok else 'not found.'}")

    elif args.command == "status":
        ok = tracker.update_status(args.id, args.status)
        print(f"Issue #{args.id} status {'updated.' if ok else 'not found.'}")

    elif args.command == "comment":
        ok = tracker.comment(args.id, args.text, args.author)
        print(f"Comment {'added.' if ok else 'issue not found.'}")

    elif args.command == "assign":
        ok = tracker.assign(args.id, args.assignee)
        print(f"Issue #{args.id} {'assigned to ' + args.assignee if ok else 'not found.'}")

    elif args.command == "stats":
        s = tracker.stats()
        print(f"\nTotal issues: {s['total']}")
        print("\nBy type:"); [print(f"  {k}: {v}") for k, v in s["by_type"].items()]
        print("\nBy status:"); [print(f"  {k}: {v}") for k, v in s["by_status"].items()]
        print("\nBy priority:"); [print(f"  {k}: {v}") for k, v in s["by_priority"].items()]

    elif args.command == "export":
        out = tracker.export_csv(args.output)
        print(f"Exported to: {out}")


if __name__ == "__main__":
    _cli()
