"""
test_handler.py
===============
Dev-kit test harness for NLH parser scripts.

Validates that a handler script:
  1. Has a correctly named file (lowercase, ends with _log_handler)
  2. Contains exactly one LogHandlerBaseClass subclass
  3. Has valid LogHandlerParameters
  4. Has a working parser() method
  5. Has all methods referenced in analysis_options

Usage:
    python dev_kit/test_handler.py subsidiaries/NPE/scripts/my_log_handler.py
    python dev_kit/test_handler.py subsidiaries/NPE/scripts/my_log_handler.py --log path/to/test.log
    python dev_kit/test_handler.py --all-scripts NPE
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import re
import sys
import types
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module(filepath: Path, module_name: str) -> types.ModuleType:
    """Load a .py file as a Python module."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _find_framework() -> Path:
    """Locate the framework directory from this file's location."""
    root = Path(__file__).resolve().parent.parent
    fw = root / "framework"
    if fw.exists():
        sys.path.insert(0, str(fw))
    return fw


# ---------------------------------------------------------------------------
# HandlerTester
# ---------------------------------------------------------------------------

class HandlerTester:
    """
    Validates and smoke-tests a single NLH parser script.

    Parameters
    ----------
    script_path : str | Path
        Path to the .py handler script.
    """

    def __init__(self, script_path: str | Path):
        self.path = Path(script_path).resolve()
        self.name = self.path.stem       # filename without .py
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self._handler_cls = None

        _find_framework()

    # ── Public API ────────────────────────────────────────────────────────────

    def validate(self) -> bool:
        """
        Run all structural validation checks.
        Returns True if all pass, False if any errors found.
        """
        self.errors.clear()
        self.warnings.clear()

        self._check_filename()
        if not self._load_module():
            return False
        self._check_class_exists()
        self._check_parameters()
        self._check_methods()
        return len(self.errors) == 0

    def run(self, log_file: Optional[str | Path] = None) -> bool:
        """
        Validate + optionally run parser() on a real log file.

        Parameters
        ----------
        log_file : str | Path, optional
            Path to a sample log file for the smoke test.

        Returns
        -------
        bool
            True if all checks pass.
        """
        ok = self.validate()

        if log_file and self._handler_cls:
            ok = self._smoke_test_parser(Path(log_file)) and ok

        self._print_report()
        return ok

    # ── Checks ───────────────────────────────────────────────────────────────

    def _check_filename(self) -> None:
        name = self.name
        if not name.islower():
            self.errors.append(f"Filename must be all lowercase: '{name}'")
        if not name.endswith("_log_handler"):
            self.errors.append(f"Filename must end with '_log_handler': '{name}'")

    def _load_module(self) -> bool:
        try:
            self._module = _load_module(self.path, f"nlh_test.{self.name}")
            return True
        except Exception as exc:
            self.errors.append(f"Import error: {exc}")
            return False

    def _check_class_exists(self) -> None:
        try:
            from main_app_files.core_script_files.log_handler_class import LogHandlerBaseClass
        except ImportError as exc:
            self.errors.append(f"Could not import LogHandlerBaseClass: {exc}")
            return

        found = []
        for attr_name, obj in vars(self._module).items():
            if (
                isinstance(obj, type)
                and issubclass(obj, LogHandlerBaseClass)
                and obj is not LogHandlerBaseClass
            ):
                found.append(obj)

        if not found:
            self.errors.append("No LogHandlerBaseClass subclass found in the module.")
        elif len(found) > 1:
            self.warnings.append(f"Multiple handler classes found: {[c.__name__ for c in found]}")
            self._handler_cls = found[0]
        else:
            self._handler_cls = found[0]

    def _check_parameters(self) -> None:
        if self._handler_cls is None:
            return

        try:
            params = self._handler_cls.log_handler_information()
        except Exception as exc:
            self.errors.append(f"log_handler_information() failed: {exc}")
            return

        # Name → filename consistency
        sanitised = re.sub(r"\W+", "_", params.log_handler_name.lower())
        expected = f"{sanitised}_log_handler"
        if expected != self.name:
            self.errors.append(
                f"Handler name '{params.log_handler_name}' maps to '{expected}.py' "
                f"but file is named '{self.name}.py'"
            )

        # Version format
        if not re.match(r"^\d+\.\d+\.\d+$", str(params.version)):
            self.errors.append(
                f"Version '{params.version}' must be in 'x.y.z' format"
            )

        # log_pattern compiles
        try:
            re.compile(params.log_pattern_str())
        except re.error as exc:
            self.errors.append(f"log_pattern is not a valid regex: {exc}")

    def _check_methods(self) -> None:
        if self._handler_cls is None:
            return

        # parser() required
        if not hasattr(self._handler_cls, "parser"):
            self.errors.append("Missing required @classmethod: parser()")

        # analysis_options methods must exist
        try:
            params = self._handler_cls.log_handler_information()
            opts = params.analysis_options or {}
        except Exception:
            return

        for label, method_name in opts.items():
            if method_name == "data_table":
                continue  # built-in
            if not hasattr(self._handler_cls, method_name):
                self.errors.append(
                    f"analysis_options references '{method_name}' "
                    f"but that method does not exist on the class"
                )

    def _smoke_test_parser(self, log_file: Path) -> bool:
        if not log_file.exists():
            self.warnings.append(f"Log file not found for smoke test: {log_file}")
            return True

        try:
            from pandas import DataFrame
            result = self._handler_cls.parser(str(log_file))
            if result is None:
                self.errors.append("parser() returned None — must return a DataFrame")
                return False
            if not isinstance(result, DataFrame):
                self.errors.append(
                    f"parser() returned {type(result).__name__} — must return a DataFrame"
                )
                return False
            if result.empty:
                self.warnings.append("parser() returned an empty DataFrame")
            else:
                print(f"  Parsed {len(result)} rows, {len(result.columns)} columns")
            return True
        except Exception as exc:
            self.errors.append(f"parser() raised an exception: {exc}")
            return False

    # ── Report ────────────────────────────────────────────────────────────────

    def _print_report(self) -> None:
        print(f"\n{'='*60}")
        print(f"Handler: {self.name}")
        print(f"{'='*60}")

        if self.errors:
            print(f"  ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(f"    ✗ {e}")
        else:
            print("  ✓ All structural checks passed")

        if self.warnings:
            print(f"  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"    ⚠ {w}")

        status = "PASS" if not self.errors else "FAIL"
        print(f"\n  Result: {status}")
        print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="NLH Handler Tester – validate and smoke-test parser scripts"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("script", nargs="?", type=Path,
                       help="Path to handler .py file")
    group.add_argument("--all-scripts", metavar="SUBSIDIARY",
                       help="Test all scripts in subsidiaries/<SUB>/scripts/")

    parser.add_argument("--log", type=Path,
                        help="Sample log file for smoke-testing parser()")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    root = Path(__file__).resolve().parent.parent
    all_passed = True

    if args.script:
        tester = HandlerTester(args.script)
        ok = tester.run(args.log)
        all_passed = ok

    elif args.all_scripts:
        scripts_dir = root / "subsidiaries" / args.all_scripts.upper() / "scripts"
        if not scripts_dir.exists():
            print(f"Directory not found: {scripts_dir}")
            sys.exit(1)
        scripts = [f for f in sorted(scripts_dir.glob("*.py")) if not f.name.startswith("_")]
        if not scripts:
            print(f"No scripts found in {scripts_dir}")
            sys.exit(0)
        for script in scripts:
            tester = HandlerTester(script)
            ok = tester.run(args.log)
            if not ok:
                all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    _cli()
