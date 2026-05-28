"""
log_handler_class.py
====================
Core base classes for NLH log handler plugins.

Defines:
  - LogHandlerBaseClass      – inherit this to build a new handler
  - LogHandlerParameters     – metadata container for a handler
  - LogHandlerInformation    – read-only information object returned to callers
  - LogHandlerMessageBroker  – thread-safe queue for GUI ↔ handler communication
  - LogHandlerBaseClassError – specific exception for base-class errors
"""

import logging
import os
from datetime import datetime
from queue import Queue
from typing import Literal

from dataclasses import dataclass
from customtkinter import CTkFrame
from pandas import DataFrame, ExcelWriter, read_csv, read_excel

from main_app_files.core_script_files.custom_graphs import CustomTablesPloter
from main_app_files.function_files.exception_handler_and_reporting import (
    NlhException,
    global_exception_handler,
)

# ---------------------------------------------------------------------------
# Module-level constants  (referenced by external code – do not rename)
# ---------------------------------------------------------------------------
parsed_file_inductor: str = "Parsed"
literal_available_save_methods = Literal["csv", "excel", "mesr"]
available_save_methods: list[str] = ["csv", "excel", "mesr"]


# ---------------------------------------------------------------------------
# LogHandlerParameters
# ---------------------------------------------------------------------------
class LogHandlerParameters:
    """
    Immutable metadata container for a log handler plugin.

    Parameters
    ----------
    log_handler_name : str
        Display name shown to users.
    version : str
        Handler version in 'x.y.z' format where x, y, z are integers >= 0 (e.g. '1.0.0').
    log_pattern : str
        Regex pattern used to identify matching log files.
    description : str
        Short description of what this handler does.
    supported_machine_types : list[str]
        Machine types this handler supports.
    supported_logs : list[str]
        Example log filenames this handler can parse.
    logs_locations : list[str]
        Where these logs are typically found on the machine.
    analysis_options : dict[str, str] | None
        Maps button labels (≤ 32 chars, no underscores) to method names.
        A "Data Table" entry is added automatically unless show_data_table='no'.
    save_method : str
        One of 'csv', 'excel', or 'mesr'.  Defaults to 'csv'.
    show_data_table : str
        'yes' (default) or 'no'.  When 'no', analysis_options must be provided.
    log_handler_group : str
        Group/category name for this handler.
    """

    def __init__(
            self,
            log_handler_name: str,
            version: str,
            log_pattern: str,
            description: str,
            supported_machine_types: list[str],
            supported_logs: list[str],
            logs_locations: list[str],
            analysis_options: dict[str, str] | None = None,
            save_method: literal_available_save_methods = "csv",
            show_data_table: str = "yes",
            log_handler_group: str = None,
    ):
        # ── Required field validation ──────────────────────────────────────
        self._require_value(log_handler_name, "log_handler_name")
        self._require_value(log_handler_group, "log_handler_group")
        self._require_value(log_pattern, "log_pattern")
        self._require_value(description, "description")
        self._require_value(supported_machine_types, "supported_machine_types")
        self._require_value(supported_logs, "supported_logs")
        self._require_value(logs_locations, "logs_locations")

        # ── version validation ─────────────────────────────────────────────
        self._validate_version(version)

        # ── show_data_table validation ─────────────────────────────────────────────
        if show_data_table not in ("yes", "no"):
            raise ValueError("LogHandlerParameters.show_data_table can only be 'yes' or 'no'")

        # ── analysis_options validation ────────────────────────────────────
        if analysis_options is not None:
            if not isinstance(analysis_options, dict):
                raise TypeError(
                    f"analysis_options must be dict or None, got {type(analysis_options)}"
                )
            for key, value in analysis_options.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError(
                        f"analysis_options entries must be [str: str], "
                        f"got [{type(key)}: {type(value)}]"
                    )
                if len(key) > 32:
                    raise ValueError(
                        f"Analysis option display name must be ≤ 32 characters, "
                        f"got {len(key)} for '{key}'"
                    )
                if "_" in key:
                    raise ValueError(
                        f"Analysis option display names cannot contain '_', got '{key}'"
                    )

        # ── Build plotting_options_dict ────────────────────────────────────
        if show_data_table == "no":
            if not analysis_options:
                raise ValueError(
                    "analysis_options cannot be empty when show_data_table='no'"
                )
            plotting_options = dict(analysis_options)
        else:
            plotting_options = dict(analysis_options) if analysis_options else {}
            plotting_options["Data Table"] = "_show_data_table"

        # ── Store attributes ───────────────────────────────────────────────
        self._class_name = None
        self._log_handler_name = log_handler_name
        self._version = version
        self._log_pattern = log_pattern
        self._description = description
        self._supported_machine_types = supported_machine_types
        self._supported_logs = supported_logs
        self._logs_locations = logs_locations
        self._log_handler_group = log_handler_group
        self._plotting_options_dict = plotting_options
        self._save_method = save_method

    # ── Internal helper ────────────────────────────────────────────────────
    @staticmethod
    def _require_value(value, field_name: str):
        if not value:
            raise ValueError(f"LogHandlerParameters.{field_name} cannot be empty")

    @staticmethod
    def _validate_version(version: str) -> None:
        """
        Validate that version follows the x.y format where x, y are
        integers >= 0 (major, minor).

        Valid:   '1.0',  '0.1',  '12.3'
        Invalid: '1.0.0',  '1.a',  1,  '1.0.0.0',  '-1.0'

        Raises
        ------
        TypeError
            If version is not a string.
        ValueError
            If version does not match x.y exactly, or any part is not a
            non-negative integer.
        """
        if not isinstance(version, str):
            raise TypeError(
                f"LogHandlerParameters.version must be a string in 'x.y' format "
                f"(e.g. '1.0'). Got type {type(version).__name__!r}: {version!r}"
            )

        parts = version.split('.')

        if len(parts) != 2:
            raise ValueError(
                f"LogHandlerParameters.version must follow the 'x.y' format with "
                f"exactly 2 parts separated by a dot (major.minor). "
                f"Got {len(parts)} part(s): {version!r}  —  "
                f"expected format example: '1.0'"
            )

        labels = ('major', 'minor')

        for index, part in enumerate(parts):
            label = labels[index]
            if not part.isdigit():
                raise ValueError(
                    f"LogHandlerParameters.version {label} part (position {index}) "
                    f"must be a non-negative integer with no leading signs or spaces. "
                    f"Got part {part!r} in version {version!r}  —  "
                    f"expected format example: '1.0'"
                )

    # ── Properties ─────────────────────────────────────────────────────────
    @property
    def class_name(self) -> str | None:
        """
        The handler's class name, set by discovery after plugin loading.
        None until discovery registers it.
        """
        return self._class_name

    @class_name.setter
    def class_name(self, new_name: str):
        """Set the handler's class name during plugin discovery."""
        self._class_name = new_name

    @property
    def log_handler_name(self) -> str:
        """Display name of the handler shown to users."""
        return self._log_handler_name

    @property
    def version(self) -> str:
        """Handler version string in 'x.y.z' format (e.g. '1.0.0')."""
        return self._version

    @property
    def log_pattern(self) -> str:
        """Regex pattern used to identify matching log files."""
        return self._log_pattern

    @property
    def description(self) -> str:
        """Short description of what this handler analyses."""
        return self._description

    @property
    def logs_locations(self) -> list[str]:
        """File system paths where the supported logs are typically found."""
        return self._logs_locations

    @property
    def supported_machine_types(self) -> list[str]:
        """Machine types this handler supports (e.g. ['32x', '62x'])."""
        return self._supported_machine_types

    @property
    def supported_logs(self) -> list[str]:
        """Example log filenames this handler can parse."""
        return self._supported_logs

    @property
    def plotting_options_dict(self) -> dict[str, str]:
        """
        Mapping of analysis button labels to their method names.
        Always includes a 'Data Table' entry unless show_data_table='no'
        was passed at construction.
        """
        return self._plotting_options_dict

    @property
    def plotting_options_str(self) -> str:
        """
        Numbered string listing all analysis options, one per line.

        Example
        -------
        '1. Graph Line Sensor\\n2. Data Table\\n'
        """
        lines = (
            f"{i + 1}. {name}\n"
            for i, name in enumerate(self._plotting_options_dict)
        )
        return "".join(lines)

    @property
    def save_method(self) -> str:
        """Output format used when saving results — one of 'csv', 'excel', or 'mesr'."""
        return self._save_method

    @property
    def log_handler_group(self) -> str:
        """Group or category this handler belongs to, used for filtering in the UI."""
        return self._log_handler_group


# ---------------------------------------------------------------------------
# LogHandlerInformation
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LogHandlerInformation:
    """
    Read-only snapshot of handler metadata returned by
    ``LogHandlerBaseClass.log_handler_information()``.

    This is produced at runtime by the base class and consumed by discovery
    and the UI. It is frozen so it can be safely passed between threads and
    stored in dictionaries without risk of mutation.

    Parameters
    ----------
    log_handler_name : str
        Display name of the handler shown to users in the UI
        (e.g. 'X8 BMM Camera Degradation').
    version : str
        Handler version string in 'x.y.z' format (e.g. '1.0.0').
    log_handler_class : str
        The handler's class name as registered by discovery
        (e.g. 'X8BmmCameraDegradationLogHandler').
    log_handler_group : str
        Group or category this handler belongs to, used for filtering
        in the UI (e.g. 'BSA/BMU').
    analysis_option_list : list
        List of analysis option display names available for this handler
        (e.g. ['Graph Line Sensor', 'Data Table']).
    log_handler_information_dict : dict
        Pre-formatted dictionary of all handler metadata ready to be
        loaded into a DataFrame for the information table in the UI.
    log_analysis_option_str : str
        Pre-formatted string listing all analysis options, one per line,
        ready for display in the UI.
    log_handler_description_str : str
        Full description of what this handler analyses, shown in the
        description text box in the UI.
    log_supported_machine_types_list : list
        List of machine type strings this handler supports
        (e.g. ['32x', '62x']).
    log_supported_logs_list : list
        List of example log filenames this handler can parse
        (e.g. ['DiagBFP0_...csv']).
    logs_locations_list : list
        List of file system paths where the supported logs are typically
        found on the machine (e.g. ['EXDP/unitlog/...']).
    log_parsed_file_inductor_str : str
        Regex pattern string used to identify matching log files
        (e.g. '^DiagBFP').
    log_handler_save_method_str : str
        Output format used when saving results — one of 'csv', 'excel',
        or 'mesr'.
    """
    log_handler_name: str
    version: str
    log_handler_class: str
    log_handler_group: str
    analysis_option_list: list
    log_handler_information_dict: dict
    log_analysis_option_str: str
    log_handler_description_str: str
    log_supported_machine_types_list: list
    log_supported_logs_list: list
    logs_locations_list: list
    log_parsed_file_inductor_str: str
    log_handler_save_method_str: str


# ---------------------------------------------------------------------------
# LogHandlerBaseClassError
# ---------------------------------------------------------------------------
class LogHandlerBaseClassError(Exception):
    """Raised for errors specific to LogHandlerBaseClass logic."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# LogHandlerMessageBroker
# ---------------------------------------------------------------------------
class LogHandlerMessageBroker:
    """
    Thread-safe one-way message queue between a handler worker thread and the GUI.

    Usage::

        broker = LogHandlerMessageBroker()
        broker.send_message({'type': 'display_message', 'message': 'Hello'})
        reply = broker.receive_message()
    """

    def __init__(self):
        self._queue = Queue()

    # Keep the original public attribute name so existing callers work.
    @property
    def queue(self) -> Queue:
        """
        The underlying :class:`queue.Queue` instance used for message passing.

        This property exposes the internal queue for callers that need direct
        access (e.g. passing it to a worker thread or polling it externally).
        Prefer :meth:`send_message` and :meth:`receive_message` for normal
        put/get operations so that logging and empty-queue safety are handled
        consistently.

        Returns
        -------
        queue.Queue
            The shared ``Queue`` object backing this broker.

        Example
        -------
        Pass the queue directly to a worker thread that puts results onto it::

            worker = AnalysisWorker(broker.queue)
            worker.start()
        """
        return self._queue

    def send_message(self, message: dict):
        """Put *message* onto the queue."""
        logging.info("LogHandlerMessageBroker – sending: %s", message)
        self._queue.put(message)

    def receive_message(self) -> dict | None:
        """Return the next message, or ``None`` if the queue is empty."""
        return self._queue.get() if not self._queue.empty() else None


# ---------------------------------------------------------------------------
# LogHandlerBaseClass
# ---------------------------------------------------------------------------
class LogHandlerBaseClass:
    """
    Base class for all NLH log-handler plugins.

    Subclass checklist
    ------------------
    **Required** (must override):

    1. ``handler_parameters`` – class-level ``LogHandlerParameters`` instance.
    2. ``parser(file_location, **kwargs)`` – parse one raw log file and return:
       - ``DataFrame``              when ``save_method`` is ``'csv'`` or ``'mesr'``
       - ``dict[str, DataFrame]``   when ``save_method`` is ``'excel'``

    **Optional** (override only if needed):

    3. ``join_tables(data_tables, **kwargs)`` – merge parsed tables before saving.
    4. One or more plotting methods (e.g. ``my_graph(gui_container, file_name, data)``).
       Register them in ``handler_parameters.analysis_options``.

    Example
    -------
    ::

        class MyHandler(LogHandlerBaseClass):
            handler_parameters = LogHandlerParameters(
                log_handler_name="My Handler",
                log_handler_group="My Group",
                description="Parses my_log.log",
                log_pattern=r"my_log.*\\.log",
                supported_machine_types=["TypeA"],
                supported_logs=["my_log.log"],
                logs_locations=["D:/logs/"],
                save_method="csv",
            )

            @classmethod
            def parser(cls, file_location, **kwargs):
                ...
                return my_dataframe
    """

    # ── Class-level sentinel – subclasses must replace this ────────────────
    handler_parameters: "LogHandlerParameters"

    # =========================================================================
    # Class methods – public API used before instantiation
    # =========================================================================

    @classmethod
    def log_handler_information(cls) -> LogHandlerInformation:
        """
        Build and return a frozen LogHandlerInformation snapshot from this
        handler's handler_parameters.
        """
        cls._validate_handler_parameters()

        nl = "\n"
        params = cls.handler_parameters
        analysis_option_list = list(params.plotting_options_dict.keys()) \
            if isinstance(params.plotting_options_dict, dict) else None

        info_table = {
            "LOG HANDLER NAME": params.log_handler_name,
            "VERSION": params.version,
            "DESCRIPTION": params.description,
            "SUPPORTED MACHINE TYPES": "".join(
                f"• {x}{nl}" for x in params.supported_machine_types
            ),
            "SUPPORTED LOGS": "".join(
                f"• {x}{nl}" for x in params.supported_logs
            ),
            "LOGS LOCATIONS": "".join(
                f"• {x}{nl}" for x in params.logs_locations
            ),
            "ANALYSIS OPTION": (
                "".join(f"• {x}{nl}" for x in analysis_option_list)
                if analysis_option_list
                else "No option available"
            ),
        }

        return LogHandlerInformation(
            log_handler_name=params.log_handler_name,
            version=params.version,
            log_handler_class=cls.__name__,
            log_handler_group=params.log_handler_group,
            analysis_option_list=analysis_option_list,
            log_handler_information_dict=info_table,
            log_analysis_option_str=params.plotting_options_str,
            log_handler_description_str=params.description,
            log_supported_machine_types_list=params.supported_machine_types,
            log_supported_logs_list=params.supported_logs,
            logs_locations_list=params.logs_locations,
            log_parsed_file_inductor_str=parsed_file_inductor,
            log_handler_save_method_str=params.save_method,
        )

    @classmethod
    def log_pattern_str(cls) -> str:
        """Return the log-file regex pattern for this handler."""
        cls._validate_handler_parameters()
        return cls.handler_parameters.log_pattern

    # =========================================================================
    # Class methods – override in subclasses
    # =========================================================================

    @classmethod
    def parser(
            cls, file_location: str, **kwargs
    ) -> "dict[str, DataFrame] | DataFrame":
        """
        Parse a single raw log file.

        Parameters
        ----------
        file_location : str
            Full path to the log file.
        **kwargs
            Injected helpers: ``user_input``, ``display_message``,
            ``select_file``, ``get_date``.

        Returns
        -------
        DataFrame
            When ``save_method`` is ``'csv'`` or ``'mesr'``.
        dict[str, DataFrame]
            When ``save_method`` is ``'excel'`` (keys = sheet names).
        """
        raise NotImplementedError(
            "parser() must be implemented in every LogHandlerBaseClass subclass."
        )

    @classmethod
    def join_tables(
            cls,
            data_tables: "dict[str, DataFrame] | dict[str, dict[str, DataFrame]]",
            **kwargs,
    ) -> "dict[str, DataFrame] | dict[str, dict[str, DataFrame]]":
        """
        Optionally merge parsed tables before saving.

        The default implementation returns *data_tables* unchanged.
        Override this when you need to combine results from multiple files.
        """
        return data_tables

    @classmethod
    def plot_graph(
            cls,
            gui_container: CTkFrame,
            file_name: str,
            data: "DataFrame | dict[str, DataFrame]",
    ):
        """
        Template for a plotting / analysis option.

        Rename this method and register it in ``handler_parameters.analysis_options``.
        The GUI will call it with a fresh ``CTkFrame`` container.

        Parameters
        ----------
        gui_container : CTkFrame
            The frame to draw into.  Configure rows/columns as needed.
        file_name : str
            Name of the source file (for titles / labels).
        data : DataFrame | dict[str, DataFrame]
            The parsed data to visualise.
        """
        raise NotImplementedError(
            "plot_graph() must be implemented or replaced with a named plotting method."
        )

    # =========================================================================
    # Class methods – internal helpers (not part of the plugin API)
    # =========================================================================

    @classmethod
    def _validate_handler_parameters(cls):
        """Raise ``TypeError`` if ``handler_parameters`` is not a ``LogHandlerParameters``."""
        if not isinstance(cls.handler_parameters, LogHandlerParameters):
            raise TypeError(
                f"Expected 'handler_parameters' to be LogHandlerParameters, "
                f"got {type(cls.handler_parameters)}"
            )

    @classmethod
    def _get_validated_parameters(cls) -> LogHandlerParameters:
        """Return ``handler_parameters`` after validation, with ``class_name`` set."""
        cls._validate_handler_parameters()
        cls.handler_parameters.class_name = cls.__name__
        return cls.handler_parameters

    @classmethod
    def _show_data_table(cls, gui_container: CTkFrame, file_name: str, data: DataFrame):
        """Render *data* as a scrollable table inside *gui_container*."""
        gui_container.grid_rowconfigure(0, weight=1)
        gui_container.grid_columnconfigure(0, weight=1)
        table = CustomTablesPloter(gui_container, data_table=data)
        table.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

    # =========================================================================
    # Instance initialisation
    # =========================================================================

    def __init__(
            self,
            message_broker: "LogHandlerMessageBroker",
            folder_Path: str,
            file_list: list[str],
            save_folder: str = None,
            input_event=None,
    ):
        # ── Validate inputs ────────────────────────────────────────────────
        if not folder_Path:
            raise ValueError("folder_Path cannot be empty")
        if not file_list:
            raise ValueError("file_list cannot be empty")
        if "" in file_list:
            raise ValueError("file_list cannot contain empty strings")

        params = self._get_validated_parameters()
        if params.save_method not in available_save_methods:
            raise ValueError(
                f"save_method must be one of {available_save_methods}, "
                f"got '{params.save_method}'"
            )

        # ── Store state ────────────────────────────────────────────────────
        self.message_broker = message_broker
        self.input_event = input_event

        self._input_cache = {}  # Caches user_input() results
        self._displayed_messages_cache = set()  # Tracks shown display_message() calls

        self.__folder_path = folder_Path
        self.__save_folder = save_folder if save_folder else folder_Path
        self.__file_list = file_list
        self.__save_method = params.save_method
        self.__analysis_options_dict = params.plotting_options_dict
        self.__parsed_file_dict = {}

    # =========================================================================
    # Public instance methods
    # =========================================================================

    def log_files_parsing_and_saving(self):
        """
        Orchestrate the full parse → join → save pipeline.

        Steps
        -----
        1. Parse every file in ``file_list`` using ``parser()``.
        2. Merge results with ``join_tables()`` (no-op by default).
        3. Save each result according to ``save_method``.

        Returns
        -------
        tuple[LogHandlerBaseClass, dict, str | None]
            ``(self, parsed_file_dict, errors_message)``
            *errors_message* is ``None`` when everything succeeded.
        """
        data_tables: dict = {}
        parsed_file_dict: dict = {}
        errors_message: str | None = None

        # ── Step 1: Parse ─────────────────────────────────────────────────
        logging.info("===Files Parsing=== START")
        for file in self.__file_list:
            logging.info("=Parsing %s= START", file)
            try:
                data_table = self.parser(
                    os.path.join(self.__folder_path, file),
                    user_input=self.user_input,
                    display_message=self.display_message,
                    select_file=self.select_file,
                    get_date=self.get_date,
                )
                self._validate_parsed_output(data_table)
                data_tables[file] = data_table

            except NlhException as exc:
                errors_message = self._accumulate_error(
                    errors_message,
                    header="Parsing Logs Error:\n",
                    line=f"{file} - {str(exc).replace(chr(10), ' ')}\n",
                )
                global_exception_handler(
                    type(exc), exc, exc.__traceback__,
                    error_message=f"{file} failed parsing: {exc}",
                    show_popup=False,
                )
            except Exception as exc:
                errors_message = self._accumulate_error(
                    errors_message,
                    header="Parsing Log Error:\n",
                    line=f"{file} - unexpected error while parsing\n",
                )
                global_exception_handler(
                    type(exc), exc, exc.__traceback__,
                    error_message=f"{file} failed parsing: {exc}",
                    show_popup=False,
                )
            logging.info("=Parsing %s= END", file)
        logging.info("===File Parsing=== END")

        if not data_tables:
            return self, parsed_file_dict, f"NLH Failed to parse all log files:\n{errors_message}"

        # ── Step 2: Join ──────────────────────────────────────────────────
        logging.info("===Joining Parsed Logs=== START")
        try:
            data_tables = self.join_tables(
                data_tables,
                user_input=self.user_input,
                display_message=self.display_message,
                select_file=self.select_file,
                get_date=self.get_date,
            )
            if not isinstance(data_tables, dict):
                raise TypeError(
                    f"join_tables must return dict, got {type(data_tables)}"
                )
        except (NlhException, Exception) as exc:
            join_error = (
                f"NLH Failed to join result files:\n{exc}\n"
                if not errors_message
                else f"NLH Failed to join result files:\n{exc}\n"
                     f"In addition the following error occurred:\n{errors_message}"
            )
            global_exception_handler(
                type(exc), exc, exc.__traceback__,
                error_message=f"Failed to join result files: {exc}",
                show_popup=False,
            )
            logging.info("===Joining Parsed Logs=== END")
            return self, parsed_file_dict, join_error
        logging.info("===Joining Parsed Logs=== END")

        # ── Step 3: Save ──────────────────────────────────────────────────
        logging.info("===Save Parsed Logs=== START")
        for parsed_log_name, table in data_tables.items():
            logging.info("=Saving %s as %s= START", parsed_log_name, self.__save_method)
            try:
                parsed_file_dict[parsed_log_name] = self.__save_data(parsed_log_name, table)
            except NlhException as exc:
                errors_message = self._accumulate_error(
                    errors_message,
                    header="Saving Result file Error:\n",
                    line=f"{parsed_log_name} - {str(exc).replace(chr(10), ' ')}\n",
                )
                global_exception_handler(
                    type(exc), exc, exc.__traceback__,
                    error_message=f"{parsed_log_name} failed saving: {exc}",
                    show_popup=False,
                )
            except Exception as exc:
                errors_message = self._accumulate_error(
                    errors_message,
                    header="Saving Result file Error:\n",
                    line=f"{parsed_log_name} - unexpected error while saving result file\n",
                )
                global_exception_handler(
                    type(exc), exc, exc.__traceback__,
                    error_message=f"{parsed_log_name} failed saving: {exc}",
                    show_popup=False,
                )
            logging.info("=Saving %s= END", parsed_log_name)
        logging.info("===Save Parsed Logs=== END")

        if parsed_file_dict:
            return self, parsed_file_dict, errors_message
        return self, parsed_file_dict, f"NLH Failed to save all log files:\n{errors_message}"

    def load_data_table(self, parsed_file_full_path: str) -> "DataFrame | dict[str, DataFrame]":
        """
        Load a previously saved result file back into memory.

        Parameters
        ----------
        parsed_file_full_path : str
            Full path to the saved result file.

        Returns
        -------
        DataFrame
            For 'csv' and 'mesr' save methods.
        dict[str, DataFrame]
            For 'excel' save method (keys = sheet names).
        """
        logging.info("=== Loading Data - %s === START", parsed_file_full_path)

        loaders = {
            "csv": lambda p: read_csv(p),
            "mesr": lambda p: read_csv(p, sep=";"),
            "excel": lambda p: read_excel(p, sheet_name=None),
        }
        loader = loaders.get(self.__save_method)
        if loader is None:
            raise ValueError(f"Unknown save method: '{self.__save_method}'")

        result = loader(parsed_file_full_path)
        logging.info("=== Loading Data - %s === END", parsed_file_full_path)
        return result

    def run_analysis_option(
            self,
            frame: CTkFrame,
            parsed_log_name: str,
            plot_option: str,
            datatable: DataFrame,
    ):
        """
        Invoke a registered plotting / analysis method by its display name.

        Parameters
        ----------
        frame : CTkFrame
            Container frame for the resulting GUI widget.
        parsed_log_name : str
            Name of the result file (used for titles).
        plot_option : str
            Key from ``handler_parameters.analysis_options``.
        datatable : DataFrame
            Data to pass to the plotting method.
        """
        logging.info("=== Plotting '%s' === START", plot_option)
        method_name = self.__analysis_options_dict[plot_option]
        getattr(self, method_name)(
            gui_container=frame,
            file_name=parsed_log_name,
            data=datatable,
        )
        logging.info("=== Plotting '%s' for '%s' === END", plot_option, parsed_log_name)

    # ── GUI interaction helpers ────────────────────────────────────────────

    def display_message(self, message: str, only_once: bool = False):
        """
        Send *message* to the GUI for display and wait for the user to dismiss it.

        Parameters
        ----------
        message : str
            Text to show.
        only_once : bool
            When ``True``, skip if this exact message has already been shown.
        """
        if only_once and message in self._displayed_messages_cache:
            logging.info("Skipping already-shown message: '%s'", message)
            return

        self.__send_and_wait({"type": "display_message", "message": message})

        if only_once:
            self._displayed_messages_cache.add(message)

    def select_file(self, title: str, file_types: list, file_extension: str) -> str | None:
        """
        Open a GUI file-selection dialog and return the chosen path.

        Parameters
        ----------
        title : str
            Dialog window title.
        file_types : list
            File-type filters for the dialog.
        file_extension : str
            Default extension to filter by.

        Returns
        -------
        str | None
            Selected file path, or ``None`` if cancelled.
        """
        response = self.__send_and_wait({
            "type": "select_file",
            "title": title,
            "file_types": file_types,
            "file_extension": file_extension,
        })
        return response.get("result") if response else None

    def user_input(self, prompt: str, only_once: bool = False) -> str | None:
        """
        Request a text input from the user via the GUI.

        Parameters
        ----------
        prompt : str
            Instruction shown to the user.
        only_once : bool
            When ``True``, return a cached answer if *prompt* was asked before.

        Returns
        -------
        str | None
            The user's answer, or ``None`` if cancelled.
        """
        if only_once and prompt in self._input_cache:
            return self._input_cache[prompt]

        response = self.__send_and_wait({"type": "user_input", "prompt": prompt})
        result = response.get("result") if response else None

        if only_once and result is not None:
            self._input_cache[prompt] = result

        return result

    def get_date(
            self,
            min_date: datetime | None = None,
            max_date: datetime | None = None,
            only_once: bool = False,
    ) -> datetime | None:
        """
        Open a GUI date-picker and return the selected date.

        Parameters
        ----------
        min_date : datetime | None
            Earliest selectable date.
        max_date : datetime | None
            Latest selectable date.
        only_once : bool
            When ``True``, return a cached result for the same min/max pair.

        Returns
        -------
        datetime | None
            The selected date, or ``None`` if cancelled.
        """
        cache_key = f"get_date_min:{min_date}_max:{max_date}"

        if only_once and cache_key in self._input_cache:
            logging.info("Using cached date for key: %s", cache_key)
            return self._input_cache[cache_key]

        response = self.__send_and_wait({
            "type": "get_date",
            "min_date": min_date.isoformat() if min_date else None,
            "max_date": max_date.isoformat() if max_date else None,
        })

        result = response.get("result") if response else None
        if result and isinstance(result, str):
            result = datetime.fromisoformat(result)

        if only_once and result is not None:
            self._input_cache[cache_key] = result

        return result

    def clear_input_cache(self, prompt: str = None):
        """
        Clear cached inputs and/or displayed-message history.

        Parameters
        ----------
        prompt : str | None
            Clear only this specific entry.  Pass ``None`` to clear everything.
        """
        if prompt:
            self._input_cache.pop(prompt, None)
            self._displayed_messages_cache.discard(prompt)
        else:
            self._input_cache.clear()
            self._displayed_messages_cache.clear()

    # =========================================================================
    # Private helpers
    # =========================================================================

    def __send_and_wait(self, message: dict) -> dict | None:
        """
        Put *message* on the broker queue and block until the GUI replies.

        Returns
        -------
        dict | None
            The reply dict, or ``None`` if the queue was empty.
        """
        self.message_broker.send_message(message)
        self.input_event.wait()
        self.input_event.clear()
        return self.message_broker.receive_message()

    def __save_data(self, file_name: str, table: "DataFrame | dict[str, DataFrame]") -> str:
        """
        Persist *table* to disk and return the full path of the saved file.

        Parameters
        ----------
        file_name : str
            Base name (with original extension) of the source log.
        table : DataFrame | dict[str, DataFrame]
            Data to save.

        Returns
        -------
        str
            Full path of the saved result file.

        Raises
        ------
        NlhException
            When the target file is locked by another process.
        Exception
            For any other unexpected I/O error.
        """
        extension_map = {"excel": ".xlsx", "mesr": ".MESR", "csv": ".csv"}
        file_extension = extension_map.get(self.__save_method, ".csv")

        base_name, _ = os.path.splitext(file_name)
        handler_class = self.log_handler_information().log_handler_class
        result_name = f"{base_name}_{parsed_file_inductor}_{handler_class}{file_extension}"
        result_path = os.path.join(self.__save_folder, result_name)

        try:
            if self.__save_method == "csv":
                table.to_csv(result_path, index=False)
                logging.info("Saved CSV: %s", result_path)

            elif self.__save_method == "mesr":
                table.to_csv(result_path, index=False, header=False, sep="\t")
                logging.info("Saved MESR: %s", result_path)

            elif self.__save_method == "excel":
                with ExcelWriter(result_path) as writer:
                    for sheet_name, sheet_data in table.items():
                        sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                        logging.info("Saved sheet '%s' to Excel", sheet_name)
                logging.info("Saved Excel: %s", result_path)

            else:
                raise ValueError(f"Unsupported save method: '{self.__save_method}'")

            return result_path

        except PermissionError as exc:
            raise NlhException(
                f"Cannot save '{result_name}' – the file is open in another program."
            ) from exc
        except Exception as exc:
            raise Exception(
                f"Unexpected error while saving '{result_name}'."
            ) from exc

    def _validate_parsed_output(self, data_table):
        """
        Confirm that ``parser()`` returned the correct type for the active save method.

        Raises ``TypeError`` with a descriptive message on mismatch.
        """
        class_name = self._get_validated_parameters().class_name

        if self.__save_method in ("csv", "mesr"):
            if not isinstance(data_table, DataFrame):
                raise TypeError(
                    f"{class_name}.parser() returned {type(data_table)}, "
                    f"expected pandas.DataFrame for save_method='{self.__save_method}'"
                )
        elif self.__save_method == "excel":
            if not isinstance(data_table, dict):
                raise TypeError(
                    f"{class_name}.parser() returned {type(data_table)}, "
                    f"expected dict[str, DataFrame] for save_method='excel'"
                )
            for sheet, data in data_table.items():
                if not isinstance(sheet, str) or not isinstance(data, DataFrame):
                    raise TypeError(
                        f"Excel sheets must be [str, DataFrame], "
                        f"got [{type(sheet)}, {type(data)}]"
                    )

    @staticmethod
    def _accumulate_error(
            current: str | None,
            header: str,
            line: str,
    ) -> str:
        """
        Append *line* to *current*, prepending *header* the first time.

        This replaces the repetitive ``if not errors_message`` blocks
        throughout ``log_files_parsing_and_saving``.
        """
        if current is None:
            return header + line
        return current + line
