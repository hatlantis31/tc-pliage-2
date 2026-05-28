"""
discovery.py

Scans analysis_files/handler_files/ and analysis_files/tools_files/ for
plugin scripts and populates two registries:

    discovery.log_handlers_dict   {pattern_str: [HandlerInfo, ...]}
    discovery.tools_list          [BaseTool instance, ...]

Usage:
    from main_app_files.core_script_files.discovery import discovery
    discovery.discover()

    # then read:
    discovery.log_handlers_dict
    discovery.tools_list
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sys
from typing import Any

from main_app_files.core_script_files.log_handler_class import LogHandlerBaseClass
from main_app_files.core_script_files.nikon_tool_class import BaseTool


class PluginDiscovery:
    """
    Discovers and registers handler and tool plugins from external script dirs.

    Registries are empty until discover() is called explicitly.
    """

    def __init__(self) -> None:
        self.log_handlers_dict: dict[str, list[Any]] = {}
        self.tools_list: list[Any] = []
        self.load_errors: list[tuple[str, Exception]] = []
        self.handler_classes_dict: dict[str, type] = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def discover(self) -> None:
        """
        Scan handler_files/ and tools_files/ and populate both registries.

        Clears any previous results before scanning so each call is a fresh
        discovery run. Call this once at startup (or again for hot-reload).
        """
        self.log_handlers_dict.clear()
        self.tools_list.clear()
        self.load_errors.clear()
        self.handler_classes_dict.clear()

        handler_dir, tools_dir = self._resolve_script_dirs()

        self._load_handlers(handler_dir)
        self._load_tools(tools_dir)

    # ── Path resolution ─────────────────────────────────────────────────────

    def _resolve_script_dirs(self) -> tuple[str, str]:
        """
        Return (handler_dir, tools_dir) for the current runtime mode.

        Dev layout:
            Nikon_Log_Handler/
                analysis_files/
                    handler_files/
                    tools_files/
                main_app_files/
                    core_script_files/
                        discovery.py   <-- this file

        Frozen layout (PyInstaller):
            dist/NikonLogHandler/
                NikonLogHandler.exe
                handler_files/
                tools_files/
        """
        if getattr(sys, 'frozen', False):
            # Packaged: handler/tool dirs sit next to the executable
            base = os.path.dirname(sys.executable)
        else:
            # Dev: walk up from this file to the repo root, then into analysis_files/
            # __file__ = .../main_app_files/core_script_files/discovery.py
            # two levels up = repo root  (Nikon_Log_Handler/)
            repo_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', '..')
            )
            base = os.path.join(repo_root, 'analysis_files')

        handler_dir = os.path.join(base, 'handler_files')
        tools_dir = os.path.join(base, 'tools_files')
        return handler_dir, tools_dir

    # ── Generic file loader ──────────────────────────────────────────────────

    @staticmethod
    def _load_py_file(filepath: str, module_name: str):
        """
        Load a .py file as a module and return it.

        The module is registered in sys.modules under module_name so that
        any relative imports inside the script can resolve correctly.
        Raises on any import-time error so callers can log it.
        """
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    # ── Handler discovery ────────────────────────────────────────────────────

    def _load_handlers(self, handler_dir: str) -> None:
        """
        Scan handler_dir for *_log_handler.py files.
        Each valid file is loaded and passed to _register_handler().
        All failures — import errors AND validation errors — are recorded
        in load_errors so the UI can report them.
        """
        if not os.path.isdir(handler_dir):
            logging.warning(f"Handler directory not found: {handler_dir}")
            return

        for filename in sorted(os.listdir(handler_dir)):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue

            name = filename[:-3]  # strip .py  e.g. "my_machine_log_handler"
            filepath = os.path.join(handler_dir, filename)
            module_name = f'nlh_handler.{name}'

            try:
                module = self._load_py_file(filepath, module_name)
                self._register_handler(module, name)
            except Exception as exc:
                self.load_errors.append((filename, exc))
                logging.error(
                    f"Failed to load handler '{filename}': {exc}",
                    exc_info=True,
                )

    def _register_handler(self, module, name: str) -> None:
        """
        Validate a loaded handler module and add its info to log_handlers_dict.

        Validation rules:
          - the module must contain exactly one LogHandlerBaseClass subclass
          - filename must be all lowercase
          - filename must end with _log_handler
          - the handler's display name must match the filename

        Raises ValueError for any validation failure so _load_handlers can
        catch it and record it in load_errors.
        """
        # ── Find the handler class ───────────────────────────────────────────
        handler_cls = None
        for attr_name, obj in vars(module).items():
            if (
                    isinstance(obj, type)
                    and issubclass(obj, LogHandlerBaseClass)
                    and obj is not LogHandlerBaseClass
            ):
                handler_cls = obj
                break

        if handler_cls is None:
            raise ValueError(  # ← raise, not warn+return
                f"No LogHandlerBaseClass subclass found in '{name}'. "
                f"Ensure the module defines a class that inherits from "
                f"LogHandlerBaseClass (and is not LogHandlerBaseClass itself)."
            )

        # ── Filename rules ───────────────────────────────────────────────────
        if not name.islower():
            raise ValueError(
                f'Handler file name "{name}" must be all lowercase.'
            )
        if not name.endswith('_log_handler'):
            raise ValueError(
                f'Handler file name "{name}" must end with "_log_handler".'
            )

        # ── Name-match check ─────────────────────────────────────────────────
        log_pattern = handler_cls.log_pattern_str()
        handler_info = handler_cls.log_handler_information()

        sanitised = re.sub(r'\W+', '_', handler_info.log_handler_name.lower())
        expected_name = f'{sanitised}_log_handler'
        if expected_name != name:
            raise ValueError(
                f'Log handler name "{handler_info.log_handler_name}" '
                f'does not match file name "{name}". '
                f'Expected file to be named "{expected_name}.py".'
            )

        # ── Register ─────────────────────────────────────────────────────────
        self.log_handlers_dict.setdefault(log_pattern, []).append(handler_info)
        self.handler_classes_dict[handler_info.log_handler_name] = handler_cls
        logging.info(
            f"Registered handler: {handler_info.log_handler_name} "
            f"(pattern: {log_pattern})"
        )

    # ── Tool discovery ───────────────────────────────────────────────────────

    def _load_tools(self, tools_dir: str) -> None:
        """
        Scan tools_dir for .py files.
        Each valid file is loaded and passed to _register_tools().
        All failures — import errors AND validation errors — are recorded
        in load_errors so the UI can report them.
        """
        if not os.path.isdir(tools_dir):
            logging.warning(f"Tools directory not found: {tools_dir}")
            return

        for filename in sorted(os.listdir(tools_dir)):
            if not filename.endswith('.py') or filename.startswith('_'):
                continue

            name = filename[:-3]
            filepath = os.path.join(tools_dir, filename)
            module_name = f'nlh_tool.{name}'

            try:
                module = self._load_py_file(filepath, module_name)
                self._register_tools(module, name)  # ← pass name for error messages
            except Exception as exc:
                self.load_errors.append((filename, exc))
                logging.error(
                    f"Failed to load tool '{filename}': {exc}",
                    exc_info=True,
                )

    def _register_tools(self, module, name: str) -> None:
        """
        Find all BaseTool subclasses in the module and append instances to tools_list.

        Raises ValueError if no BaseTool subclass is found so _load_tools can
        catch it and record it in load_errors — same pattern as _register_handler.
        """
        found_any = False

        for attr_name, obj in vars(module).items():
            if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseTool)
                    and obj is not BaseTool
            ):
                instance = obj()
                self.tools_list.append(instance)
                logging.info(
                    f"Registered tool: {instance.tool_info.tool_display_name}"
                )
                found_any = True

        if not found_any:
            raise ValueError(  # ← raise, not silent skip
                f"No BaseTool subclass found in '{name}'. "
                f"Ensure the module defines a class that inherits from "
                f"BaseTool (and is not BaseTool itself)."
            )


# ── Module-level singleton ───────────────────────────────────────────────────
# Registries are EMPTY until discover() is called explicitly.
discovery = PluginDiscovery()
