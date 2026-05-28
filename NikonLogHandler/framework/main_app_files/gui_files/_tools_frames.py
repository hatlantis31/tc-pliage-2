"""
This module contains the ToolsFrame class which is a part of the GUI responsible for
displaying and handling the functionality of tools.
"""

import threading
from functools import partial

from PIL import Image
from tktooltip import ToolTip

import customtkinter
from main_app_files.core_script_files.discovery import discovery
from main_app_files.core_script_files.log_handler_class import LogHandlerMessageBroker


def run_tool(tool, sharepoint_handler=None, **kwargs):
    """
    Execute the specified tool.

    tool: The tool to be executed.
    sharepoint_handler: The SharePoint handler object from main application.
    kwargs: Additional parameters for the tool.
    """
    tool._start_tool(sharepoint_handler=sharepoint_handler, **kwargs)


class ToolsFrame(customtkinter.CTkFrame):
    """
    A frame in the main application window that contains buttons for each tool.
    """

    def __init__(self, master, app_logo: Image.Image, widgets_text: dict, set_description: callable, **kwargs):
        """
        Initialize the frame.

        master: The parent widget.
        app_logo: The application logo.
        widgets_text: A dictionary containing text for each widget.
        set_description: A callable that sets a description for each tool.
        """

        super().__init__(master, **kwargs)

        self.__widgets_text = widgets_text
        self.set_description = set_description
        self.sharepoint_handler = None  # Will be set by the main window

        # Event for thread synchronization
        self.input_event = threading.Event()

        # Message broker for communication between threads
        self.message_broker = LogHandlerMessageBroker()

        # Dictionary of log handlers
        self.log_handlers_dict = discovery.log_handlers_dict

        self.__selected_log_type = 'Nikon Log Handler'
        self.__app_logo = app_logo
        self.__run_stats = None
        self.__available_tools = {}
        self.tools_buttons = {}
        self.tools_tooltip = {}
        self.tools_list = discovery.tools_list

        # Initialize the GUI components
        self.__initialize_gui()

    def set_sharepoint_handler(self, sharepoint_handler):
        """
        Set the SharePoint handler and update tool states.

        Args:
            sharepoint_handler: The SharePoint handler object
        """
        self.sharepoint_handler = sharepoint_handler
        self.update_sharepoint_dependent_tools()

    def __initialize_gui(self):
        """
        Initialize the GUI components.
        """
        row = 0

        # Generate buttons for each tool
        for tool in self.tools_list:
            tool_display_name = tool.tool_info.tool_display_name
            needs_sharepoint = tool.tool_info.need_sharepoint_handler

            # Create button with conditional command based on SharePoint requirement
            if needs_sharepoint:
                # Tool needs SharePoint - use lambda to pass sharepoint_handler
                button_command = partial(self._run_tool_with_sharepoint_check, tool)
            else:
                # Tool doesn't need SharePoint - use original command
                button_command = partial(run_tool, tool)

            self.tools_buttons[tool_display_name] = customtkinter.CTkButton(
                self,
                text=tool_display_name,
                command=button_command
            )
            self.tools_buttons[tool_display_name].grid(row=row, column=0, padx=0, pady=(0, 5), sticky='ew')

            # Tooltip with tool description
            tools_description = tool.tool_info.tools_description
            self.tools_tooltip[tool_display_name] = ToolTip(
                self.tools_buttons[tool_display_name],
                msg=tools_description,
                refresh=2,
                delay=1
            )

            # Update the column and row for next button
            row += 1

        # Initial update of SharePoint-dependent tools (they should be disabled initially)
        self.update_sharepoint_dependent_tools()

    def _run_tool_with_sharepoint_check(self, tool):
        """
        Run a tool that requires SharePoint handler with authentication check.

        Args:
            tool: The tool to run
        """
        # Check if SharePoint handler is available and authenticated
        if not self.sharepoint_handler or not self.sharepoint_handler.is_authenticated:
            import tkinter.messagebox
            tkinter.messagebox.showerror(
                "SharePoint Required",
                f"This tool requires SharePoint access.\nPlease login to SharePoint first."
            )
            return

        # Run the tool with SharePoint handler
        run_tool(tool, sharepoint_handler=self.sharepoint_handler)

    def update_sharepoint_dependent_tools(self):
        """
        Update the state of tools that depend on SharePoint authentication.
        Call this method when SharePoint authentication status changes.
        """
        is_authenticated = self.sharepoint_handler and self.sharepoint_handler.is_authenticated

        for tool in self.tools_list:
            if tool.tool_info.need_sharepoint_handler:
                tool_display_name = tool.tool_info.tool_display_name
                button = self.tools_buttons.get(tool_display_name)
                tooltip = self.tools_tooltip.get(tool_display_name)

                if button and tooltip:
                    if is_authenticated:
                        button.configure(state="normal", text=tool_display_name)
                        tooltip.msg = tool.tool_info.tools_description
                    else:
                        button.configure(state="disabled", text=tool_display_name)
                        tooltip.msg = "Tool disabled please login to SharePoint"

    def reload_tools(self):
        """
        Re-read discovery registries and repopulate tool buttons.
        Called after discovery.discover() completes or on reload.
        """
        # Update the tools list from discovery
        self.tools_list = discovery.tools_list

        # Destroy existing buttons and tooltips cleanly
        for display_name, button in self.tools_buttons.items():
            button.destroy()
        for display_name, tooltip in self.tools_tooltip.items():
            tooltip.destroy()  # ToolTip supports destroy()

        self.tools_buttons.clear()
        self.tools_tooltip.clear()

        # Rebuild the GUI with the new tools list
        self.__initialize_gui()
