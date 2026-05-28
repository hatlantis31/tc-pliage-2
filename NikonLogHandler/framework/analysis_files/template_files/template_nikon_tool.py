"""
Tool Template

This is a template for creating a tool in the analysis_files module.
Use this template as a starting point to define the necessary information
and functionality for your tool.

Author: [Your Name]
Date: [Date]

Usage:
1. Fill in the required information in the ToolInfo instance.
2. Implement the functionality in the run method.
"""

from main_app_files.core_script_files.nikon_tool_class import BaseTool, ToolInfo, ToolWindow


class ToolTemplate(BaseTool):
    """
    [Tool Name]

    [Tool Description]
    """

    def __init__(self):
        """
        Initializes the [Tool Name] with tool information and any other necessary data.
        """
        tool_info = ToolInfo(tool_display_name="Tool Name",
                             version="x.y",
                             tools_description="Tool Description",
                             supported_machine="All",
                             widgets_text_dict={
                                 'English': {}
                             }
                             )
        super().__init__(tool_info=tool_info)

    def run(self, tool_window: ToolWindow, **kwargs):
        """
        The main method that executes the tool's functionality. This method should be
        implemented by all subclasses that inherit from BaseTool.

        Args:
            tool_window: this Top level window that the tool will be in
            **kwargs: Arbitrary keyword arguments that can be used to pass additional
                      parameters required by the tool's execution logic.
        """
        # Implement the functionality here
        # use thread_runner function to run non GUI logic, so it will not freze the GUI
        raise NotImplementedError("The run method must be implemented by the subclass.")