"""
Basic tool function in order to make a tool
"""
import logging
import customtkinter
from dataclasses import dataclass

from main_app_files.function_files.exception_handler_and_reporting import NlhException


class ToolWindow(customtkinter.CTkToplevel):
    def __init__(self, label, window_size: tuple, resizable: tuple, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WIDTH = window_size[0]
        HEIGHT = window_size[1]
        self.resizable(resizable[0], resizable[1])
        self.title(label)
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.minsize(WIDTH, HEIGHT)

        # Set the window to be on top initially and then it is removed
        self.attributes('-topmost', True)

    def remove_on_top(self):
        """
        Remove the topmost attribute
        """
        self.attributes('-topmost', False)
        self.update()


@dataclass(frozen=True)
class ToolInfo:
    """
    Immutable metadata descriptor for a Nikon tool window.

    This dataclass is used to declare all static information about a tool
    in one place. It is consumed by the tool base class and the UI layer
    to configure the window title, size, language strings, and SharePoint
    integration.

    Parameters
    ----------
    tool_display_name : str
        Human-friendly name of the tool shown in the window title bar and
        any header labels (e.g. ``'BMM Camera Degradation Tool'``).

    version : str
        Tool version string in ``'x.y.z'`` (major.minor.patch) format
        (e.g. ``'1.0.0'``). Validated by :meth:`_validate_version` at
        construction time — raises :exc:`TypeError` if not a string and
        :exc:`ValueError` if the format is incorrect.

    tools_description : str
        Short paragraph describing what the tool does. Displayed in the
        tool's information or about section in the UI.

    supported_machine : str
        Comma-separated string of machine types this tool supports
        (e.g. ``'32x, 62x'``). Shown in the tool information panel.

    widgets_text_dict : dict
        Nested dictionary of UI label strings keyed first by language code
        and then by widget identifier.  Use :meth:`widgets_text` to
        retrieve the correct language slice at runtime.

        Example structure::

            {
                'English': {
                    'btn_run':  'Run Analysis',
                    'lbl_path': 'Log Path',
                },
                'Japanese': {
                    'btn_run':  '分析を実行',
                    'lbl_path': 'ログパス',
                },
            }

    tool_window_size : tuple[int, int], optional
        ``(width, height)`` of the tool window in pixels.
        Both elements must be integers. Defaults to ``(400, 300)``.
        Raises :exc:`TypeError` if the value is not a tuple of integers.

    resizable : tuple[bool, bool], optional
        ``(horizontal, vertical)`` flags controlling whether the tool
        window can be resized by the user. Defaults to ``(False, False)``
        (fixed size in both directions).

    need_sharepoint_handler : bool, optional
        Set to ``True`` if the tool requires a SharePoint connection to
        upload or download files. When ``True`` the base class will
        initialise the SharePoint handler before the tool window opens.
        Defaults to ``False``.

    Raises
    ------
    TypeError
        If ``tool_window_size`` is not a tuple of integers, or if
        ``version`` is not a string.
    ValueError
        If ``version`` does not follow the ``'x.y'`` format with
        three non-negative integer parts.

    Example
    -------
    ::

        info = ToolInfo(
            tool_display_name     = 'BMM Camera Degradation Tool',
            version               = '1.2',
            tools_description     = 'Analyses BMM camera degradation logs.',
            supported_machine     = '32x, 62x',
            widgets_text_dict     = {
                'English': {'btn_run': 'Run Analysis'},
            },
            tool_window_size      = (800, 600),
            resizable             = (False, False),
            need_sharepoint_handler = False,
        )
    """
    tool_display_name: str
    version: str
    tools_description: str
    supported_machine: str
    widgets_text_dict: dict
    tool_window_size: tuple = (400, 300)
    resizable: tuple = (False, False)
    need_sharepoint_handler: bool = False

    def __post_init__(self):
        if not isinstance(self.tool_window_size, tuple) or \
                not all(isinstance(x, int) for x in self.tool_window_size):
            raise TypeError(
                f'tool_window_size needs to be a tuple of int parameters. '
                f'Instead got {self.tool_window_size}'
            )

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
                f"[ToolInfo] 'version' must be a string in 'x.y' format "
                f"(e.g. '1.0'). Got type {type(version).__name__!r}: {version!r}"
            )

        parts = version.split('.')

        if len(parts) != 2:
            raise ValueError(
                f"[ToolInfo] 'version' must follow the 'x.y' format "
                f"with exactly 2 parts separated by a dot (major.minor). "
                f"Got {len(parts)} part(s): {version!r}  —  "
                f"expected format example: '1.0'"
            )

        labels = ('major', 'minor')

        for index, part in enumerate(parts):
            label = labels[index]
            if not part.isdigit():
                raise ValueError(
                    f"[ToolInfo] 'version' {label} part (position {index}) "
                    f"must be a non-negative integer with no leading signs or spaces. "
                    f"Got part {part!r} in version {version!r}  —  "
                    f"expected format example: '1.0'"
                )

    def widgets_text(self, language: str = 'English') -> dict:
        """
        Return the widgets_text dict based on language.
        """
        return self.widgets_text_dict[language]


class BaseTool:
    """
    The base class for all tools that are used to analyze log files. All tools should
    inherit from this class and implement the run method to execute their functionality.
    """

    def __init__(self, tool_info: ToolInfo):
        """
        Initialize a new instance of a tool with its basic information.

        Args:
            tool_info (ToolInfo): A ToolInfo object containing the tool's metadata.
        """
        self.tool_info = tool_info
        self.tool_window = None
        self.sharepoint_handler = None

    # noinspection PyTypeChecker
    def _start_tool(self, sharepoint_handler=None, **kwargs):
        """
        Wrap the run function. This is meant just to create the top-level window.

        Args:
            sharepoint_handler: The SharePoint handler object from the main application
            **kwargs: Additional parameters for the tool
        """
        # Store the SharePoint handler reference
        self.sharepoint_handler = sharepoint_handler

        self.tool_window = ToolWindow(
            label=self.tool_info.tool_display_name,
            window_size=self.tool_info.tool_window_size,
            resizable=self.tool_info.resizable,
        )

        # Schedule the removal of topmost attribute after a short delay
        self.tool_window.after(200, self.tool_window.remove_on_top)

        self.run(tool_window=self.tool_window, sharepoint_handler=sharepoint_handler, **kwargs)

    def run(self, tool_window: ToolWindow, sharepoint_handler=None, **kwargs):
        """
        The main method that executes the tool's functionality. This method should be
        implemented by all subclasses that inherit from BaseTool.

        Args:
            tool_window:        The top-level window that the tool will be in.
            sharepoint_handler: The SharePoint handler object (None if not needed or
                                not authenticated).
            **kwargs:           Arbitrary keyword arguments that can be used to pass
                                additional parameters required by the tool's execution logic.
        """
        raise NotImplementedError("The run method must be implemented by the subclass.")
