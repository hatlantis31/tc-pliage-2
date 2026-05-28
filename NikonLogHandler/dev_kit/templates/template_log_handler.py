"""
NLH Parser Template  –  copy this file to your subsidiary's scripts/ folder.

Rename the file to:  <sanitised_handler_name>_log_handler.py
   where <sanitised_handler_name> is the handler's display name lowercased
   with all non-word characters replaced by underscores.

   Example: handler name "X6 CT SL Trace" → file "x6_ct_sl_trace_log_handler.py"

See dev_kit/HOW_TO_ADD_A_PARSER.md for the full step-by-step guide.
"""

from pandas import DataFrame, read_table, concat

from main_app_files.core_script_files.log_handler_class import (
    LogHandlerBaseClass,
    LogHandlerParameters,
)
from main_app_files.core_script_files import custom_graphs


class TemplateLogHandler(LogHandlerBaseClass):
    """
    Replace 'TemplateLogHandler' with your class name, e.g. X6CtSlTraceLogHandler.
    """

    # =========================================================================
    # EDIT THIS SECTION – fill in all fields
    # =========================================================================
    handler_parameters = LogHandlerParameters(
        log_handler_name="Template Handler",       # Display name shown in UI
        version="1.0.0",                           # Format: "major.minor.patch"
        log_pattern=r"Template.*\.log",            # Regex to match log filenames
        description="Short description of what this parser does.",
        supported_machine_types=["X6"],            # e.g. ["X6", "X8"]
        supported_logs=["Template_20240101.log"],  # Example log filenames
        logs_locations=[r"C:\Nikon\Logs"],         # Where logs live on the tool
        log_handler_group="GRP",                   # Sidebar group label
        # analysis_options maps button labels to method names on this class.
        # Labels must be ≤ 32 chars and contain no underscores.
        analysis_options={
            "Plot Data": "plot_graph",
        },
        save_method="csv",                         # "csv" | "excel" | "mesr"
        # show_data_table="yes",                   # "yes" (default) or "no"
    )
    # =========================================================================

    # ── REQUIRED METHOD ───────────────────────────────────────────────────────

    @classmethod
    def parser(cls, file_location: str, **kwargs) -> DataFrame:
        """
        Parse a single log file.  Called once per selected file.

        Parameters
        ----------
        file_location : str
            Absolute path to the log file on disk.

        Returns
        -------
        DataFrame
            Parsed data.  Must never return None — return DataFrame() on failure.
        """
        # TODO: replace this with your actual parsing logic
        df = read_table(
            file_location,
            sep="\t",          # adjust separator
            skiprows=0,        # skip header rows if needed
            encoding="utf-8",
        )
        # Clean column names
        df.columns = [c.strip() for c in df.columns]
        return df

    # ── OPTIONAL METHODS ──────────────────────────────────────────────────────

    @classmethod
    def join_tables(cls, data_tables: dict, **kwargs) -> dict[str, DataFrame]:
        """
        Merge DataFrames from multiple files into one (optional).

        Parameters
        ----------
        data_tables : dict
            {file_path: DataFrame} for each parsed file.

        Returns
        -------
        dict[str, DataFrame]
            {"joined_data": merged_DataFrame}
        """
        frames = list(data_tables.values())
        if not frames:
            return {"joined_data": DataFrame()}

        joined = concat(frames, ignore_index=True)
        # TODO: sort, deduplicate, etc. as needed
        return {"joined_data": joined}

    @classmethod
    def plot_graph(cls, gui_container, file_name: str, data: DataFrame) -> None:
        """
        Render a graph in the NLH GUI (optional).

        Parameters
        ----------
        gui_container : CTkFrame
            Parent GUI frame provided by NLH.
        file_name : str
            Display name for the graph title.
        data : DataFrame
            Data to plot (the joined or single-file DataFrame).
        """
        # TODO: customise axis labels and columns
        graph = custom_graphs.CustomLineGraph(
            gui_container,
            data_table=data,
            x_axis="",          # column name for X axis
            x_label="Time",
            y_left_label="Value",
            graph_title=file_name,
            y_left_axis=[""],   # list of column names for Y axis
        )
        graph.pack(fill="both", expand=True)

    # ── CONSTRUCTOR (leave as-is) ─────────────────────────────────────────────

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
