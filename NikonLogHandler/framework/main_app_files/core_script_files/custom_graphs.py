"""
Model has plotting option to use
"""
import logging

import mplcursors
import numpy as np
from matplotlib.dates import date2num

from typing import Literal
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib.backend_bases import MouseButton
from matplotlib.colors import Normalize
from matplotlib.dates import DateFormatter, num2date
from matplotlib.patches import Circle
from numpy import arange
from pandas import DataFrame
from pandas.api.types import is_numeric_dtype, is_datetime64_dtype
from tksheet import Sheet
from customtkinter import CTkFrame, CTkToplevel, CTkTabview
from matplotlib import use as matplotlib_use, pyplot as plt, ticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from main_app_files.core_script_files import _plot_utils
from main_app_files.function_files.exception_handler_and_reporting import global_exception_handler

matplotlib_use('TkAgg')

# Literal type for Custom Graph dict keys limits
axis_properties_name = Literal['color', 'display name']
line_limits_properties_name = Literal['coordinates', 'color', 'display name', 'line width']


def heatmap(data, ax=None, cmap='viridis', linewidths=0, annot=False,
            xticklabels='auto', yticklabels='auto', vmin=None, vmax=None,
            cbar=True, cbar_kws=None):
    """
    Drop-in replacement for seaborn.heatmap using only matplotlib
    """
    if ax is None:
        ax = plt.gca()

    # Create heatmap
    im = ax.imshow(data,
                   aspect='auto',
                   cmap=cmap,
                   vmin=vmin,
                   vmax=vmax)

    # Handle tick labels
    if xticklabels == 'auto':
        ax.set_xticks(np.arange(data.shape[1]))
        if isinstance(data, DataFrame):
            ax.set_xticklabels(data.columns)
    elif xticklabels:
        ax.set_xticks(np.arange(len(xticklabels)))
        ax.set_xticklabels(xticklabels)

    if yticklabels == 'auto':
        ax.set_yticks(np.arange(data.shape[0]))
        if isinstance(data, DataFrame):
            ax.set_yticklabels(data.index)
    elif yticklabels:
        ax.set_yticks(np.arange(len(yticklabels)))
        ax.set_yticklabels(yticklabels)

    # Add colorbar
    if cbar:
        cbar_kws = cbar_kws or {}
        if 'ticks' in cbar_kws:
            plt.colorbar(im, ax=ax, **cbar_kws)
        else:
            plt.colorbar(im, ax=ax)

    # Add grid
    if linewidths:
        ax.grid(True, which='major', color='black', linewidth=linewidths)

    return im


class CustomTable(CTkFrame):
    """
    CustomTable class to present a DataFrame in a table format using a custom TKinter frame.
    Automatically resizes cells to fit text for smaller datasets and allows manual resizing.

    :param parent: The parent widget.
    :param data_table: DataFrame to be displayed in the table.
    """

    def __init__(self, master, data_table: DataFrame, **kwargs):
        super().__init__(master, **kwargs)
        self.sheet = None
        self.data_table = data_table  # Store the DataFrame
        self.pack(fill="both", expand=True)  # Make the frame fill its container
        self.after_idle(self.init_sheet)  # Delay sheet initialization until idle

    def init_sheet(self):
        """Initialize the sheet widget with data after the main loop starts."""
        # Create the sheet widget and pack it into the frame
        self.sheet = Sheet(self, data=self.data_table.values.tolist())
        self.sheet.pack(fill="both", expand=True)

        # Set the headers of the sheet based on DataFrame columns
        self.sheet.headers(self.data_table.columns.tolist())

        # Enable various user interactions with the sheet
        self.sheet.enable_bindings((
            "copy", "rc_select", "arrowkeys", "double_click_column_resize",
            "right_click_popup_menu", "column_width_resize", "column_select",
            "row_select", "drag_select", "single_select", "select_all"
        ))

        # Conditionally resize cells to fit text for smaller datasets
        if len(self.data_table) < 1000 and len(self.data_table.columns) < 20:
            self.sheet.set_all_cell_sizes_to_text(redraw=True)


class CustomTablesPloter(CTkTabview):
    def __init__(self, *args, data_table: DataFrame | dict[str, DataFrame], **kwargs):
        # Pass styling directly to super().__init__() instead of calling configure() separately
        super().__init__(
            *args,
            fg_color='light grey',
            bg_color='light grey',
            segmented_button_selected_color='Black',
            segmented_button_unselected_color='grey',
            segmented_button_fg_color='light grey',
            corner_radius=4,
            **kwargs
        )

        if not isinstance(data_table, dict):
            self.add("Data")
            self.tableframe = CTkFrame(master=self.tab("Data"))
            self.tableframe.grid(row=0, column=0, sticky="nsew")
            self.tab("Data").grid_rowconfigure(0, weight=1)
            self.tab("Data").grid_columnconfigure(0, weight=1)
            self.table = CustomTable(master=self.tableframe, data_table=data_table)
        else:
            self.table = {}
            for sheet in data_table.keys():
                self.add(sheet)
            for sheet in data_table.keys():
                self.table[sheet] = {}
                self.tab(sheet).grid_rowconfigure(0, weight=1)
                self.tab(sheet).grid_columnconfigure(0, weight=1)
                self.table[sheet]['Tableframe'] = CTkFrame(master=self.tab(sheet))
                self.table[sheet]['Tableframe'].grid(row=0, column=0, sticky="nsew")
                self.table[sheet]['Table'] = CustomTable(
                    master=self.table[sheet]['Tableframe'],
                    data_table=data_table[sheet]
                )


class CustomLineGraph(CTkFrame):
    """
    A customizable line graph component that can display data with one or two Y axes.

    Features:
    - Single or dual Y-axis plotting
    - Support for datetime X-axis with customizable date format
    - Trend line fitting with polynomial regression
    - Interactive hover tooltips
    - Clickable graphs that open in new windows
    - Customizable line colors, markers, and legends
    - Support for horizontal and vertical limit lines

    Parameters:
        graph_title (str): Title of the graph
        data_table (DataFrame): Pandas DataFrame containing the data to plot
        x_axis (str): Column name for X-axis data
        y_left_axis (dict|list): Columns to plot on left Y-axis
            - As list: ['column1', 'column2', ...]
            - As dict: {'column1': {'color': 'red', 'display name': 'Column 1'}, ...}
        y_right_axis (dict|list, optional): Columns to plot on right Y-axis (same format as y_left_axis)

        Display options:
        dpi (int): Resolution of the graph (default: 80)
        marker_size (int): Size of data point markers (default: 2)
        line_width (int): Width of plotted lines (default: 1)
        grid_on (bool): Whether to show grid lines (default: True)
        date_format (str): Format string for datetime x-axis (default: '%Y-%m-%d %H:%M')
            Examples: '%Y-%m-%d' (date only), '%m/%d %H:%M' (short format), '%b %d' (month day)

        Interactive options:
        click_graph_new_window (bool): Enable right-click to open in new window (default: True)
        nav_buttons (bool): Show navigation toolbar (default: True)

        Axis options:
        x_label (str, optional): Label for X-axis
        y_left_label (str, optional): Label for left Y-axis
        y_right_label (str, optional): Label for right Y-axis
        x_scale (str): Scale type for X-axis ('linear', 'log', etc.) (default: 'linear')
        y_left_scale (str): Scale type for left Y-axis (default: 'linear')
        y_right_scale (str): Scale type for right Y-axis (default: 'linear')

        Axis limits and ticks:
        x_axis_max_min (tuple): (min, max) limits for X-axis
        y_left_axis_max_min (tuple): (min, max) limits for left Y-axis
        y_right_axis_max_min (tuple): (min, max) limits for right Y-axis
        x_ticks (list): Custom tick positions for X-axis
        y_left_ticks (list): Custom tick positions for left Y-axis
        y_right_ticks (list): Custom tick positions for right Y-axis

        Legend options:
        y_left_axis_show_legend (bool): Show legend for left Y-axis (default: True)
        y_right_axis_show_legend (bool): Show legend for right Y-axis (default: True)
        y_left_axis_legend_loc (str): Position of left Y-axis legend (default: 'best')
        y_right_axis_legend_loc (str): Position of right Y-axis legend (default: 'best')

        Limit lines:
        x_line_limits (list): Vertical lines with format [{'coordinates': x, 'display name': 'name', 'color': 'color', 'line-width': width, 'internal_label': bool}, ...]
        y_left_line_limits (list): Horizontal lines on left Y-axis (same format as x_line_limits)
        y_right_line_limits (list): Horizontal lines on right Y-axis (same format as x_line_limits)

        Trend line options:
        line_fit (dict): Polynomial fitting options with format {'column': degree, ...}
        line_fit_show_r2 (bool): Show R² value in legend (default: False)
        trend_line_extend (dict): Extension of trend lines with format {'column': amount, ...}
    """

    def __init__(self, *args,
                 graph_title, data_table, x_axis, y_left_axis,
                 y_right_axis=None, x_label=None, y_left_label=None, y_right_label=None,
                 # Display options
                 dpi=80, marker_size=2, line_width=1, grid_on=True,
                 date_format='%Y-%m-%d %H:%M',  # NEW PARAMETER
                 # Interactive options
                 click_graph_new_window=True, nav_buttons=True,
                 # Axis options
                 x_scale='linear', y_left_scale='linear', y_right_scale='linear',
                 # Axis limits
                 x_axis_max_min=None, y_left_axis_max_min=None, y_right_axis_max_min=None,
                 # Tick options
                 x_ticks=None, y_left_ticks=None, y_right_ticks=None,
                 # Legend options
                 y_left_axis_show_legend=True, y_right_axis_show_legend=True,
                 y_left_axis_legend_loc='best', y_right_axis_legend_loc='best',
                 # Limit lines
                 x_line_limits=None, y_left_line_limits=None, y_right_line_limits=None,
                 # Trend line options
                 line_fit=None, line_fit_show_r2=False, trend_line_extend=None,
                 **kwargs):
        """Initialize the CustomLineGraph with the specified parameters."""
        super().__init__(*args, **kwargs)

        # Store all parameters as instance variables
        self.graph_title = graph_title
        self.data_table = data_table
        self.x_axis = x_axis
        self.y_left_axis = y_left_axis
        self.y_right_axis = y_right_axis

        # Display options
        self.dpi = dpi
        self.marker_size = marker_size
        self.line_width = line_width
        self.grid_on = grid_on
        self.date_format = date_format  # NEW INSTANCE VARIABLE

        # Labels
        self.x_label = x_label
        self.y_left_label = y_left_label
        self.y_right_label = y_right_label

        # Interactive options
        self.click_graph_new_window = click_graph_new_window

        # Axis options
        self.x_scale = x_scale
        self.y_left_scale = y_left_scale
        self.y_right_scale = y_right_scale

        # Axis limits
        self.x_axis_max_min = x_axis_max_min
        self.y_left_axis_max_min = y_left_axis_max_min
        self.y_right_axis_max_min = y_right_axis_max_min

        # Tick options
        self.x_ticks = x_ticks
        self.y_left_ticks = y_left_ticks
        self.y_right_ticks = y_right_ticks

        # Legend options
        self.y_left_axis_show_legend = y_left_axis_show_legend
        self.y_right_axis_show_legend = y_right_axis_show_legend
        self.y_left_axis_legend_loc = y_left_axis_legend_loc
        self.y_right_axis_legend_loc = y_right_axis_legend_loc

        # Limit lines
        self.x_line_limits = x_line_limits
        self.y_left_line_limits = y_left_line_limits
        self.y_right_line_limits = y_right_line_limits

        # Trend line options
        self.line_fit = line_fit or {}
        self.line_fit_show_r2 = line_fit_show_r2
        self.trend_line_extend = trend_line_extend

        # Initialize state variables
        self.left_axis_legend = []
        self.right_axis_legend = []
        self.left_axis = None
        self.right_axis = None
        self.window_open = False

        # Create the graph
        self.graph = self.figure_maker(nav_buttons=nav_buttons, click_graph_new_window=click_graph_new_window)

    def figure_maker(self, nav_buttons=True, gui_container=None, click_graph_new_window=False):
        """
        Create and configure a matplotlib figure with optional navigation buttons.

        Parameters:
            nav_buttons (bool): Whether to add navigation toolbar buttons
            gui_container (CTkFrame|CTkToplevel): Container widget for the figure
            click_graph_new_window (bool): Enable right-click to open in new window

        Returns:
            FigureCanvasTkAgg: Canvas object containing the figure
        """
        # Determine X-axis type (date or number)
        x_axis_type = "date" if is_datetime64_dtype(self.data_table[self.x_axis]) else "number"

        # Create figure and canvas
        figure = Figure(dpi=self.dpi)
        figure.set_layout_engine('tight')
        container = gui_container or self
        figure_canvas = FigureCanvasTkAgg(figure, master=container)

        # Add navigation toolbar if requested
        if nav_buttons:
            NavigationToolbar2Tk(figure_canvas, container)

        # Create main subplot
        self.left_axis = figure.add_subplot()

        # Format date axis if needed - MODIFIED TO USE CUSTOM FORMAT
        if x_axis_type == 'date' and nav_buttons:
            # Use the custom date format for navigation mode
            nav_format = self.date_format + ':%S' if '%S' not in self.date_format else self.date_format
            self.left_axis.xaxis.set_major_formatter(DateFormatter(nav_format))
            figure.autofmt_xdate()

        # Plot data on left Y-axis
        self._plot_left_axis_data(x_axis_type)

        # Configure left axis properties
        self._set_left_axis_properties()

        # Configure X-axis properties
        self._set_x_axis_properties()

        # Adjust date labels to prevent overlap
        if x_axis_type == 'date':
            self._format_date_axis()

        # Create right Y-axis if needed
        if self.y_right_axis:
            self._create_right_axis(x_axis_type)

        # Configure grid
        if self.grid_on:
            self.left_axis.grid(True)

        # Pack the figure in the container
        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        # Bind right-click handler if enabled
        if click_graph_new_window:
            figure.canvas.mpl_connect("button_press_event", self.right_click_callback)

        # Apply custom date format for all date axes - MODIFIED
        if x_axis_type == 'date':
            self.left_axis.xaxis.set_major_formatter(DateFormatter(self.date_format))

        # Pack FIRST, then draw
        figure_canvas.get_tk_widget().pack(fill="both", expand=1)
        figure_canvas.draw()  # ← draw AFTER pack so widget has real size

        return figure_canvas

    def _plot_left_axis_data(self, x_axis_type):
        """
        Plot data on the left Y-axis.

        Parameters:
            x_axis_type (str): Type of X-axis ('date' or 'number')
        """
        # Validate y_left_axis
        self._validate_axis_parameter(self.y_left_axis, "y_left_axis")

        # Convert list to dict if necessary
        if not isinstance(self.y_left_axis, dict):
            self.y_left_axis = {item: {} for item in self.y_left_axis}

        # Plot each series
        for column, properties in self.y_left_axis.items():
            # Validate column data
            self._validate_column(column)

            # Filter out NaN values
            data_to_plot = self.data_table[[self.x_axis, column]].dropna().sort_values(by=self.x_axis)

            # Get line properties
            color = properties.get('color')
            display_name = properties.get('display name', column)

            # Plot the line
            line, = self.left_axis.plot(
                data_to_plot[self.x_axis],
                data_to_plot[column],
                marker='.',
                color=color,
                markersize=self.marker_size,
                linewidth=self.line_width,
                label=display_name
            )

            # Add to legend if enabled
            if self.y_left_axis_show_legend:
                self.left_axis_legend.append(display_name)

            # Add hover labels
            if line:
                self._add_hover_labels(line, x_axis_type)

            # Add trend line if requested
            if column in self.line_fit:
                self._add_fit_line(data_to_plot, column, properties, self.left_axis, self.left_axis_legend)

    @staticmethod
    def _validate_axis_parameter(axis_param, param_name):
        """
        Validate that an axis parameter is a list or dict.

        Parameters:
            axis_param: The parameter to validate
            param_name (str): Name of the parameter for error messages

        Raises:
            TypeError: If parameter is not a list or dict
        """
        if not isinstance(axis_param, (list, dict)):
            raise TypeError(f'"{param_name}" must be a list or dict, got {type(axis_param)}')

    def _validate_column(self, column):
        """
        Validate that a column exists and contains numeric data.

        Parameters:
            column (str): Name of the column to validate

        Raises:
            TypeError: If column data is not numeric
        """
        if not is_numeric_dtype(self.data_table[column]):
            raise TypeError(f'Column "{column}" must contain numeric data')

    def _add_hover_labels(self, line, x_axis_type):
        """
        Add interactive hover labels to plot lines.

        Parameters:
            line: The plotted line object
            x_axis_type (str): Type of X-axis ('date' or 'number')
        """
        if x_axis_type == 'date':
            mplcursors.cursor(line).connect("add", lambda sel: sel.annotation.set_text(
                f'{sel.artist.get_label()}\n'
                f'X: {num2date(sel.target[0]).strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'Y: {sel.target[1]:.2f}'
            ))
        else:
            mplcursors.cursor(line).connect("add", lambda sel: sel.annotation.set_text(
                f'{sel.artist.get_label()}\n'
                f'X: {sel.target[0]:.2f}\n'
                f'Y: {sel.target[1]:.2f}'
            ))

    def _add_fit_line(self, data_table, column, properties, axis, legend_list):
        """
        Add a polynomial trend line fit to the data.

        Parameters:
            data_table (DataFrame): Data to fit
            column (str): Column name to fit
            properties (dict): Line properties
            axis: The axis to plot on
            legend_list (list): Legend entries to update
        """
        # Get X and Y values
        x_values = data_table[self.x_axis].values
        y_values = data_table[column].values

        # Convert datetime to numerical values if needed
        if is_datetime64_dtype(x_values):
            x_numeric = date2num(x_values)
        else:
            x_numeric = x_values

        # Filter out NaN values
        valid_data = ~np.isnan(x_numeric) & ~np.isnan(y_values)
        x_numeric = x_numeric[valid_data]
        y_values = y_values[valid_data]

        # Skip if no valid data
        if len(x_numeric) == 0 or len(y_values) == 0:
            return

        # Get polynomial degree
        degree = self.line_fit[column]

        try:
            # Fit polynomial
            coeffs = np.polyfit(x_numeric, y_values, degree)
            poly = np.poly1d(coeffs)

            # Determine trend line range
            x_min = x_numeric.min()

            if self.trend_line_extend is None:
                x_max = x_numeric.max()
            else:
                # Handle extension for datetime or numeric
                if is_datetime64_dtype(x_values):
                    x_max = date2num(self.trend_line_extend)
                else:
                    x_max = self.trend_line_extend

            # Generate trend line points
            x_fit = np.linspace(x_min, x_max, 100)
            y_fit = poly(x_fit)

            # Get line style properties
            fit_color = properties.get('color', 'black')
            # Use fit_line_display_name if provided, otherwise use original display_name
            display_name = properties.get('fit_line_display_name',
                                          properties.get('display name', column))

            # Convert back to datetime for plotting if needed
            if is_datetime64_dtype(x_values):
                x_fit = num2date(x_fit)

            # Plot the trend line
            axis.plot(x_fit, y_fit, '--', color=fit_color, label=f'{display_name} (Fit)')

            # Calculate and add R² if requested
            if self.line_fit_show_r2:
                r_squared = 1 - (sum((y_values - poly(x_numeric)) ** 2) /
                                 ((len(y_values) - 1) * np.var(y_values, ddof=1)))
                legend_list.append(f'{display_name} (Fit) R²={r_squared:.3f}')
            else:
                legend_list.append(f'{display_name} (Fit)')

        except Exception as e:
            # Handle fitting errors
            global_exception_handler(type(e), e, e.__traceback__,
                                     error_message="Error in polynomial fitting",
                                     show_popup=False)

    def _set_left_axis_properties(self):
        """Configure properties for the left Y-axis."""
        # Add legend if enabled
        if self.y_left_axis_show_legend:
            if self.y_left_axis_legend_loc == "Outside":
                self.left_axis.legend(self.left_axis_legend, loc='center',
                                      bbox_to_anchor=(1.02, 0.5), borderaxespad=0.)
            else:
                self.left_axis.legend(self.left_axis_legend, loc=self.y_left_axis_legend_loc)

        # Set axis labels and title
        self.left_axis.set_title(self.graph_title)
        self.left_axis.set_ylabel(self.y_left_label)
        self.left_axis.set_xlabel(self.x_label)

        # Set axis scale
        self.left_axis.set_yscale(self.y_left_scale)

        # Set custom ticks if provided
        if self.y_left_ticks is not None:
            self.left_axis.set_yticks(self.y_left_ticks)

        # Add horizontal limit lines
        _plot_utils.add_line_annotations(
            axis=self.left_axis,
            line_limits=self.y_left_line_limits,
            orientation='horizontal',
            side='left'
        )

        # Set axis limits if provided
        if self.y_left_axis_max_min:
            self.left_axis.set_ylim(self.y_left_axis_max_min)

    def _set_x_axis_properties(self):
        """Configure properties for the X-axis."""
        if is_numeric_dtype(self.data_table[self.x_axis]) or is_datetime64_dtype(self.data_table[self.x_axis]):
            # Create a copy of x_line_limits for bottom annotations
            bottom_annotations = []
            if self.x_line_limits:
                # For each line, create a copy but remove the display name if it's an internal label
                for line in self.x_line_limits:
                    line_copy = line.copy()
                    if line.get('internal_label', False):
                        line_copy['display name'] = ''  # Remove the label text but keep the line
                    bottom_annotations.append(line_copy)

            # Add vertical limit lines with modified labels
            _plot_utils.add_line_annotations(
                axis=self.left_axis,
                line_limits=bottom_annotations if bottom_annotations else self.x_line_limits,
                orientation='vertical',
                side='bottom'
            )

            # Set axis scale
            self.left_axis.set_xscale(self.x_scale)

            # Add internal labels for vertical lines
            self._add_internal_x_line_labels()

            # Set axis limits if provided
            if self.x_axis_max_min:
                self.left_axis.set_xlim(self.x_axis_max_min)

            # Set custom ticks if provided
            if self.x_ticks:
                self.left_axis.xaxis.set_major_locator(ticker.MultipleLocator(self.x_ticks))

    def _format_date_axis(self):
        """Format X-axis labels for better display of dates."""
        plt.setp(
            self.left_axis.xaxis.get_majorticklabels(),
            rotation=45,
            ha='right',
            rotation_mode='anchor'
        )
        plt.tight_layout()

    def _add_internal_x_line_labels(self):
        """Add internal labels for vertical limit lines."""
        if not self.x_line_limits:
            return

        for line in self.x_line_limits:
            # Skip if coordinates not provided
            coordinates = line.get('coordinates')
            if coordinates is None:
                continue

            # Skip if not an internal label
            if not line.get('internal_label', False):
                continue

            # Get properties
            display_name = line.get('display name', '')
            color = line.get('color', 'red')

            # Calculate text position (30% up from bottom)
            ymin, ymax = self.left_axis.get_ylim()
            text_y = ymin + (ymax - ymin) * 0.3

            # Add rotated text
            self.left_axis.text(
                coordinates, text_y, display_name,
                rotation=90,
                color='red',
                verticalalignment='bottom',
                horizontalalignment='right'
            )

    def _create_right_axis(self, x_axis_type):
        """
        Create and configure the right Y-axis.

        Parameters:
            x_axis_type (str): Type of X-axis ('date' or 'number')
        """
        # Validate y_right_axis
        self._validate_axis_parameter(self.y_right_axis, "y_right_axis")

        # Create twin axis
        self.right_axis = self.left_axis.twinx()

        # Convert list to dict if necessary
        if not isinstance(self.y_right_axis, dict):
            self.y_right_axis = {item: {} for item in self.y_right_axis}

        # Plot each series
        for column, properties in self.y_right_axis.items():
            # Validate column data
            self._validate_column(column)

            # Filter out NaN values
            data_to_plot = self.data_table[[self.x_axis, column]].dropna().sort_values(by=self.x_axis)

            # Get line properties
            color = properties.get('color')
            display_name = properties.get('display name', column)

            # Plot the line
            line, = self.right_axis.plot(
                data_to_plot[self.x_axis],
                data_to_plot[column],
                marker='.',
                color=color,
                markersize=self.marker_size,
                linewidth=self.line_width,
                label=display_name
            )

            # Add to legend if enabled
            if self.y_right_axis_show_legend:
                self.right_axis_legend.append(display_name)

            # Add hover labels
            if line:
                self._add_hover_labels(line, x_axis_type)

            # Add trend line if requested
            if column in self.line_fit:
                self._add_fit_line(data_to_plot, column, properties, self.right_axis, self.right_axis_legend)

        # Set axis properties
        self._configure_right_axis()

    def _configure_right_axis(self):
        """Configure properties for the right Y-axis."""
        # Set axis label
        self.right_axis.set_ylabel(self.y_right_label)

        # Set axis scale
        try:
            self.right_axis.set_yscale(self.y_right_scale)
        except ValueError as e:
            logging.warning(f"Warning: Could not set y_right_scale: {e}")

        # Set custom ticks if provided
        if self.y_right_ticks is not None:
            try:
                self.right_axis.set_yticks(self.y_right_ticks)
            except ValueError as e:
                logging.warning(f"Warning: Could not set y_right_ticks: {e}")

        # Add legend if enabled
        if self.y_right_axis_show_legend:
            self._add_right_axis_legend()

        # Add horizontal limit lines
        _plot_utils.add_line_annotations(
            axis=self.right_axis,
            line_limits=self.y_right_line_limits,
            orientation='horizontal',
            side='right'
        )

        # Set axis limits if provided
        if self.y_right_axis_max_min:
            self.right_axis.set_ylim(self.y_right_axis_max_min)

        # Format tick labels
        self._format_right_axis_ticks()

    def _add_right_axis_legend(self):
        """Add legend to the right Y-axis."""
        if self.y_right_axis_legend_loc == "Outside":
            self.right_axis.legend(
                self.right_axis_legend,
                loc='center',
                bbox_to_anchor=(1.15, 0.5),
                borderaxespad=0.
            )
        else:
            self.right_axis.legend(
                self.right_axis_legend,
                loc=self.y_right_axis_legend_loc
            )

    def _format_right_axis_ticks(self):
        """Format tick labels on the right Y-axis for better readability."""
        # Adjust tick label size
        self.right_axis.tick_params(axis='y', labelsize=10)

        # Use scientific notation for large numbers
        if self.y_right_scale == 'linear':
            formatter = ticker.ScalarFormatter(useMathText=True)
            formatter.set_scientific(True)
            formatter.set_powerlimits((-2, 3))
            self.right_axis.yaxis.set_major_formatter(formatter)

        # Adjust layout to prevent overlap
        self.right_axis.figure.tight_layout()

    def right_click_callback(self, event):
        """
        Handle right-click events on the plot.

        Parameters:
            event: Mouse event object
        """
        if event.button == MouseButton.RIGHT:
            self.open_graph_in_window(event)

    def open_graph_in_window(self, event=None):
        """Open the graph in a new resizable window."""
        # Do nothing if window is already open
        if self.window_open:
            return

        # Set flag to indicate window is open
        self.window_open = True

        # Create new window
        window = CTkToplevel(self)
        window.title(self.graph_title)
        window.geometry("400x250")

        # Set callback for window close
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))

        # Create graph in new window
        self.graph = self.figure_maker(
            nav_buttons=True,
            gui_container=window,
            click_graph_new_window=False
        )

    def on_window_close(self, window):
        """
        Handle window close events.

        Parameters:
            window: Window being closed
        """
        self.window_open = False
        window.destroy()

class CustomBarGraph(CTkFrame):
    """
    CustomBarGraph class will crate line graph (can be scatter if line_width set 0)\n
    :param data_table = type(DataFrame) date to plot\n
    :param graph_size = type(tuple) default (400, 250), graph size in pixels\n
    :param graph_title = type(str)\n
    :param dpi = type(int) default 60, define the point size in the graph\n
    :param click_graph_new_window = type(bool) default True\n
    :param nav_buttons = type(bool) default True, define if to show graph nav buttons\n
    :param y1_axis_legend_loc = type(str) default "best"\n
    :param y2_axis_legend_loc = type(str) default "best"\n
    :param x_axis = type(str) name of the x-left_axis header in the dataframe \n
    :param y1_axis = type(list) names of the y1-left_axis header key in the dataframe, and color value \n
    :param color = type(list)  color value \n
    :param x_axis_max_min = type(tuple) default None, tuple with left_axis (min,max)\n
    :param y_ticks = type(list) default None, list with (min,max,step)\n
    :param y1_label = type(str)\n
    :param y2_label = type(str)\n
    :param x_label = type(str)
    """

    def __init__(self, *args,
                 data_table: DataFrame,
                 graph_size: tuple = (400, 250),
                 graph_title: str is not None,
                 dpi: int = 60,
                 click_graph_new_window: bool = True,
                 nav_buttons: bool = True,
                 y1_axis_legend_loc: str = "best",
                 x_axis: str,
                 y1_axis: list,
                 color: list,
                 width_bar: float = 0.35,
                 y1_label: str = None,
                 x_label: str = None,
                 y_ticks: list = None,
                 stacked: bool = False,
                 y_axis_max_min: list = None,
                 **kwargs, ):
        super().__init__(*args, **kwargs)
        self.click_graph_new_window = click_graph_new_window
        self.y1_axis_legend_loc = y1_axis_legend_loc
        self.y1_label = y1_label
        self.graph_title = graph_title
        self.y1_axis = y1_axis
        self.x_axis = x_axis
        self.x_label = x_label
        self.data_table = data_table
        self.dpi = dpi
        self.color = color
        self.y_axis_max_min = y_axis_max_min
        self.y_ticks = y_ticks
        self.width_bar = width_bar
        self.width = graph_size[0] / self.dpi
        self.height = graph_size[1] / self.dpi
        self.axis_legend = []
        self.stacked = stacked
        self.window_open = False
        # ========================================
        # ============ create a graph ============
        # ========================================

        self.figure_canvas = self.figure_maker(nav_buttons, click_graph_new_window=self.click_graph_new_window)

    def figure_maker(self, nav_buttons, master_obj=None, click_graph_new_window=False):
        """
        Creates and configures a matplotlib figure with optional navigation buttons and click event handling.

        Parameters:
        nav_buttons (bool): If True, navigation toolbar buttons will be added to the figure.
        master_obj (optional): The container widget where the figure will be placed.
            If None, the figure will be placed in the current context.
        click_graph_new_window (bool): If True, clicking on the graph will trigger a callback function for handling
            the event, such as opening a new window. Defaults to False.

        Returns:
        FigureCanvasTkAgg: The canvas object containing the created figure, which can be packed into a Tkinter widget.
        """
        # ============ create a figure ============
        figure = Figure(figsize=(self.width, self.height), dpi=self.dpi, tight_layout=True)
        if master_obj:
            figure_canvas = FigureCanvasTkAgg(figure, master=master_obj)
        else:
            figure_canvas = FigureCanvasTkAgg(figure, master=self)

        # ============ create the toolbar ============
        if nav_buttons:
            if master_obj:
                NavigationToolbar2Tk(self.figure_canvas, master_obj)
            else:
                NavigationToolbar2Tk(self.figure_canvas, self)

        # ============ create axes ============
        axis = figure.add_subplot()

        # ============ create the bar graph ============
        axis = self.data_table.plot.bar(x=self.x_axis, y=self.y1_axis, stacked=self.stacked, ax=axis, title=self.graph_title)
        axis.grid()
        axis.set_ylabel(self.y1_label)

        # ============ set x left_axis min max values ============
        if self.y_axis_max_min:
            axis.set_ylim(self.y_axis_max_min)

        # # ============ set color ============
        # if self.color is not []:
        #     left_axis.set_color(self.color)

        # ============ set x tick values ============
        if self.y_ticks:
            ticks = arange(self.y_ticks[0], self.y_ticks[1], self.y_ticks[2])
            axis.set_yticks(ticks)

        # ============ place figure in window ============
        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        if click_graph_new_window:
            # ============ bind function on graph click ============
            figure_canvas.mpl_connect('button_press_event', self.right_click_callback)

        return figure_canvas

    def right_click_callback(self, event=None):
        """
        Callback function to handle the right-click event on the plot.

        Parameters:
            event (matplotlib.backend_bases.MouseEvent): The event object that contains information about the event.
        """
        if event.button == MouseButton.RIGHT:
            self.open_graph_in_window(event)

    def open_graph_in_window(self, event=None):
        """
            crate a resizable window with graph that have nav buttons
        """
        if self.window_open:
            return  # Do nothing if the window is already open

        self.window_open = True  # Set the flag to indicate the window is open
        # ============ define window size for new graph on click ============
        window = CTkToplevel(self)
        window.title(self.graph_title)
        window.geometry(f"{400}x{250}")

        # Reset the flag when the window is closed
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))

        # ========================================
        # ============ create a graph ============
        # ========================================
        self.figure_canvas = self.figure_maker(nav_buttons=True, master_obj=window, click_graph_new_window=False)

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.

        This function is called when the user closes the window. It resets the
        `window_open` flag to `False` to allow a new window to be opened in the
        future, and then destroys the window.

        Parameters:
        window (CTkToplevel): The window instance that is being closed.
        """
        self.window_open = False  # Reset the flag
        window.destroy()  # Close the window


class CustomBoxPlot(CTkFrame):
    """
    CustomBoxPlot class will create
    :param data_table = type(DataFrame) date to plot
    :param graph_size = type(tuple)
    :param graph_title = type(str)
    :param dpi = type(int)
    :param click_graph_new_window = type(bool)
    :param nav_buttons = type(bool)
    :param x_axis = type(str)
    :param y_axis = type(str)
    """

    def __init__(self, parent, *args, data_table: DataFrame, graph_size: tuple = (400, 250),
                 graph_title: str = None, dpi: int = 60, click_graph_new_window: bool = True,
                 nav_buttons: bool = True, x_axis: str = None, y_axis: str = None, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.data_table = data_table
        self.graph_size = graph_size
        self.graph_title = graph_title
        self.dpi = dpi
        self.click_graph_new_window = click_graph_new_window
        self.nav_buttons = nav_buttons
        self.x_axis = x_axis
        self.y_axis = y_axis

        self.width = graph_size[0] / self.dpi
        self.height = graph_size[1] / self.dpi
        self.window_open = False
        self.figure_canvas = self.figure_maker()

    def figure_maker(self):
        """
        Creates and configures a matplotlib figure with a box plot, optional navigation buttons, and click event handling.

        Returns:
        FigureCanvasTkAgg: The canvas object containing the created figure, which can be packed into a Tkinter widget.
        """
        # Create a figure
        figure = Figure(figsize=(self.width, self.height), dpi=self.dpi, tight_layout=True)
        figure_canvas = FigureCanvasTkAgg(figure, master=self)

        # Create the toolbar
        if self.nav_buttons:
            NavigationToolbar2Tk(figure_canvas, self)

        # Create axes
        axis = figure.add_subplot()

        # Create the box plot
        y_axis_columns = [col for col in self.data_table.columns if col == self.y_axis]
        x_axis_values = self.data_table[self.x_axis].unique()
        data_values = []
        for x_value in x_axis_values:
            data_values.append(self.data_table[self.data_table[self.x_axis] == x_value][self.y_axis].values)

        axis.boxplot(data_values, labels=x_axis_values, vert=True)
        axis.set_title(self.graph_title)
        axis.set_xlabel(self.x_axis)
        axis.set_ylabel(self.y_axis)

        # Place figure in window
        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        if self.click_graph_new_window:
            figure_canvas.mpl_connect('button_press_event', self.right_click_callback)

        return figure_canvas

    def right_click_callback(self, event=None):
        """
        Callback function to handle the right-click event on the plot.

        Parameters:
            event (matplotlib.backend_bases.MouseEvent): The event object that contains information about the event.
        """
        if event.button == MouseButton.RIGHT:
            self.open_graph_in_window(event)

    def open_graph_in_window(self, event=None):
        """
        Create a resizable window with graph and nav buttons
        """
        if self.window_open:
            return  # Do nothing if the window is already open

        self.window_open = True  # Set the flag to indicate the window is open
        # Create a resizable window with graph and nav buttons
        window = CTkToplevel(self)
        window.geometry(f"{400}x{250}")

        # Reset the flag when the window is closed
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))

        self.figure_canvas = self.figure_maker()

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.

        This function is called when the user closes the window. It resets the
        `window_open` flag to `False` to allow a new window to be opened in the
        future, and then destroys the window.

        Parameters:
        window (CTkToplevel): The window instance that is being closed.
        """
        self.window_open = False  # Reset the flag
        window.destroy()  # Close the window


class CustomHeatmap(CTkFrame):
    """
    CustomHeatmap class will create heatmap graph (can be scatter if line_width set 0)\n
    :param data_table = type(DataFrame) date to plot\n
    :param graph_size = type(tuple) default (400, 250), graph size in pixels\n
    :param graph_title = type(str)\n
    :param click_graph_new_window = type(bool) default True\n
    :param nav_buttons = type(bool) default True, define if to show graph nav buttons\n
    :param line_width = type(int) default 0, line width of the heatmap\n
    :param y_label = type(str) label of the y-axis\n
    :param x_label = type(str) label of the x-axis\n
    :param xtickslables = type(list) default None, list of x-axis labels\n
    :param ytickslables = type(list) default None, list of y-axis labels\n
    :param max_min = type(list) default None, list with (min,max)\n
    :param cmap = default jet, color map\n
    :param annot = type(bool) default True, show values on heatmap\n
    :linewidths = type(int) default 0, line width of the heatmap\n
    """

    def __init__(self, *args,
                 data_table: DataFrame,
                 graph_size: tuple = (400, 250),
                 graph_title: str is not None,
                 dpi: int = 60,
                 annot: bool = False,
                 click_graph_new_window: bool = True,
                 nav_buttons: bool = True,
                 line_width: int = 0,
                 xticklabels="auto",
                 yticklabels="auto",
                 y_label: str = None,
                 x_label: str = None,
                 max_min: list = [None, None],
                 cmap='jet',
                 **kwargs, ):

        super().__init__(*args, **kwargs)
        self.click_graph_new_window = click_graph_new_window
        self.graph_title = graph_title
        self.grid_size = graph_size
        self.data_table = data_table
        self.dpi = dpi
        self.data_table = data_table
        self.axis_legend = []
        self.annot = annot
        self.line_width = line_width
        self.xticklabels = xticklabels
        self.yticklabels = yticklabels
        self.width = graph_size[0] / self.dpi
        self.height = graph_size[1] / self.dpi
        self.max_min = max_min
        self.x_label = x_label
        self.y_label = y_label
        self.cmap = cmap
        self.window_open = False
        # ========================================
        # ============ create a graph ============
        # ========================================

        self.figure_canvas = self.figure_maker(nav_buttons, click_graph_new_window=self.click_graph_new_window)

    def figure_maker(self, nav_buttons: bool = True, gui_container: CTkFrame | CTkToplevel = None, click_graph_new_window: bool = False):
        """
        :param nav_buttons: type(bool = True) define if to show graph nav buttons
        :param gui_container: an isinstance of CTkFrame or CTkToplevel type obj this will be the master for the gui windows that will be crated
        :param click_graph_new_window:
        :return:
        """
        # ============ create a figure ============
        figure = Figure(dpi=self.dpi, layout='tight')
        if gui_container:
            figure_canvas = FigureCanvasTkAgg(figure, master=gui_container)
        else:
            figure_canvas = FigureCanvasTkAgg(figure, master=self)
        figure_canvas.draw()

        # ============ create the toolbar/nav_buttons object ============
        if nav_buttons:
            if gui_container:
                NavigationToolbar2Tk(figure_canvas, gui_container)
            else:
                NavigationToolbar2Tk(figure_canvas, self)

        # ============ create axes ============
        axis = figure.add_subplot()

        # ============error handling, check the data type of the class ============
        if not isinstance(self.data_table, DataFrame):
            raise TypeError(f"the data_table must be type(DataFrame) not {type(self.data_table)}")
        if not isinstance(self.max_min, list):
            raise TypeError(f"the max_min must be type(list) not {type(self.max_min)}")
        if not isinstance(self.xticklabels, list) and self.xticklabels != "auto":
            raise TypeError(f"the xticklabels must be type(list) not {type(self.xticklabels)}")
        if not isinstance(self.yticklabels, list) and self.yticklabels != "auto":
            raise TypeError(f"the yticklabels must be type(list) not {type(self.yticklabels)}")
        if not isinstance(self.x_label, str) and self.x_label is not None:
            raise TypeError(f"the x_label must be type(str) not {type(self.x_label)}")
        if not isinstance(self.y_label, str) and self.y_label is not None:
            raise TypeError(f"the y_label must be type(str) not {type(self.y_label)}")
        if not isinstance(self.cmap, str):
            raise TypeError(f"the cmap must be type(str) not {type(self.cmap)}")
        if not isinstance(self.annot, bool):
            raise TypeError(f"the annot must be type(bool) not {type(self.annot)}")
        if not isinstance(self.line_width, int):
            raise TypeError(f"the line_width must be type(int) not {type(self.line_width)}")
        if not isinstance(self.graph_title, str):
            raise TypeError(f"the graph_title must be type(str) not {type(self.graph_title)}")
        if not isinstance(self.click_graph_new_window, bool):
            raise TypeError(f"the click_graph_new_window must be type(bool) not {type(self.click_graph_new_window)}")

        # ============ calculate min and max of the data ============
        if self.max_min[0] is None:
            min_val = self.data_table.min().min()
            max_val = self.data_table.max().max()
        else:
            min_val = self.max_min[0]
            max_val = self.max_min[1]

        # ============ create the bar graph ============
        heatmap(self.data_table,
                ax=axis,
                cmap=self.cmap,
                linewidths=self.line_width,
                annot=self.annot,
                xticklabels=self.xticklabels,
                yticklabels=self.yticklabels,
                vmin=min_val,
                vmax=max_val,
                cbar_kws={'ticks': range(int(round(min_val)), int(round(max_val + 1)), int(round((max_val - min_val) // 10)))})
        axis.grid()
        # ============ set graph label ============
        if self.x_label:
            axis.set_xlabel(self.x_label, fontsize=15)
        else:
            raise ValueError("x_label is not defined")
        if self.y_label:
            axis.set_ylabel(self.y_label, fontsize=15)
        else:
            raise ValueError("y_label is not defined")
        if self.graph_title:
            axis.set_title(self.graph_title, fontsize=35)
        else:
            raise ValueError("graph_title is not defined")

        # ============ place figure in window ============
        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        if click_graph_new_window:
            # ============ bind function on graph click ============
            figure_canvas.mpl_connect('button_press_event', self.right_click_callback)

        return figure_canvas

    def right_click_callback(self, event=None):
        """
        Callback function to handle the right-click event on the plot.

        Parameters:
            event (matplotlib.backend_bases.MouseEvent): The event object that contains information about the event.
        """
        if event.button == MouseButton.RIGHT:
            self.open_graph_in_window(event)

    def open_graph_in_window(self, event=None):
        """
            crate a resizable window with graph that have nav buttons
        """
        if self.window_open:
            return  # Do nothing if the window is already open

        self.window_open = True  # Set the flag to indicate the window is open
        # ============ define window size for new graph on click ============
        window = CTkToplevel(self, title=self.graph_title)
        window.geometry(f"{400}x{250}")
        # Reset the flag when the window is closed
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))
        # ========================================
        # ============ create a graph ============
        # ========================================

        self.figure_canvas = self.figure_maker(nav_buttons=True, gui_container=window, click_graph_new_window=False)

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.

        This function is called when the user closes the window. It resets the
        `window_open` flag to `False` to allow a new window to be opened in the
        future, and then destroys the window.

        Parameters:
        window (CTkToplevel): The window instance that is being closed.
        """
        self.window_open = False  # Reset the flag
        window.destroy()  # Close the window


class CustomLineGraphGrouping(CTkFrame):
    """
    CustomLineGraph class will crate line graph (can be scatter if line_width set 0),
    this class inherit from the CTkframe, so you can use also frame properties
    :param graph_title: type(str) title of the graph to be shown
    :param dpi: type(int = 80) define the point size in the graph
    :param marker_size: type(int = 1) set marker size
    :param line_width: type(int = 1) set line size
    :param click_graph_new_window: type(bool = True) default True
    :param nav_buttons: type(bool = True) default True, define if to show graph nav buttons
    :param grid_on: type(bool = True) select if to show graph grid
    :param click_graph_new_window: type(bool = True) default True
    :param nav_buttons: type(bool = True) define if to show graph nav buttons
    :param data_table: type(DataFrame) the date to plot it needs to be a DataFrame
    :param x_axis: type(str) name of the x_axis header in the dataframe
    to set specific color and display name to each line use dict {'colum_1_name': {'color': 'color_1','display name': 'name_1'},'colum_2_name': {'color': 'color_2','display name': 'name_2'},...}
    :param y_axis: type(tuple)
    to set specific color and display name to each line use dict {'colum_1_name': {'color': 'color_1','display name': 'name_1'},'colum_2_name': {'color': 'color_2','display name': 'name_2'},...}
    :param x_label: type(str = None) Name to display on X Axis
    :param y_label: type(str = None) Name to display on Right Y Axis
    :param x_line_limits: type(list[dict] = None) list of dict with line limits ['coordinates': x_coordinates, 'display name': 'line name', line-width: width},'color': color...]
    :param y_line_limits: type(list[dict] = None) list of dict with line limits ['coordinates': y_coordinates, 'display name': 'line name', line-width: width},...]
    :param x_axis_max_min: type(tuple = None) tuple with axis (min,max)
    :param y_axis_max_min: type(tuple = None) tuple with axis (min,max)
    :param show_legend: type(bool = True) chose if the show y right lines legend
    :param legend_loc: type(str= 'best') set location of the y right lines legend
    """

    def __init__(self, *args,
                 graph_title: str,
                 dpi: int = 80,
                 marker_size: int = 1,
                 line_width: int = 1,
                 click_graph_new_window: bool = True,
                 nav_buttons: bool = True,
                 grid_on: bool = True,
                 data_table: DataFrame,
                 x_axis: str,
                 x_label: str = None,
                 y_axis: tuple,
                 y_label: str = None,
                 x_line_limits: list[dict[line_limits_properties_name: str | int | float]] = None,
                 y_line_limits: list[dict[line_limits_properties_name: str | int | float]] = None,
                 x_axis_max_min: tuple[int | float] = None,
                 y_axis_max_min: tuple[int | float] = None,
                 show_legend: bool = False,
                 legend_loc: str = 'best',
                 **kwargs, ):
        super().__init__(*args, **kwargs)
        # Set parameters as self parameters, so you will be able to pass to a function
        self.graph_title = graph_title
        self.dpi = dpi
        self.line_width = line_width
        self.marker_size = marker_size
        self.click_graph_new_window = click_graph_new_window
        self.grid_on = grid_on
        self.data_table = data_table
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.x_label = x_label
        self.y_label = y_label
        self.x_line_limits = x_line_limits
        self.y_line_limits = y_line_limits
        self.x_axis_max_min = x_axis_max_min
        self.y_axis_max_min = y_axis_max_min
        self.show_legend = show_legend
        self.legend_loc = legend_loc
        # ini parameter
        self.axis_legend = []
        self.axis = None
        self.window_open = False
        # ========================================
        # ============ create a graph ============
        # ========================================

        self.graph = self.figure_maker(nav_buttons, click_graph_new_window=self.click_graph_new_window)

    def figure_maker(self, nav_buttons: bool = True, gui_container: CTkFrame | CTkToplevel = None, click_graph_new_window: bool = False):
        """
        :param nav_buttons: type(bool = True) define if to show graph nav buttons
        :param gui_container: an isinstance of CTkFrame or CTkToplevel type obj this will be the master for the gui windows that will be crated
        :param click_graph_new_window:
        :return:
        """
        # ============ create a figure ============
        figure = Figure(dpi=self.dpi, layout='tight')

        # ============ create the y right axis ============
        if type(self.y_axis) is not tuple:
            raise TypeError(f'"y_axis" is {type(self.y_axis)} expect tuple or list')
        else:
            self.axis = figure.subplots()
            for key, grp in self.data_table.groupby([self.y_axis[0]]):
                if self.show_legend:
                    self.axis = grp.plot(ax=self.axis, x=self.x_axis, y=self.y_axis[1], label=key[0], markersize=5)
                else:
                    self.axis = grp.plot(ax=self.axis, x=self.x_axis, y=self.y_axis[1], label=key[0], markersize=5, legend=False)

        # ============ Set Axis title names ============
        if self.graph_title:
            self.axis.set_title(self.graph_title)

        # ============ Set Axis Labels names ============
        if self.y_label:
            self.axis.set_ylabel(self.y_label)

        if self.y_label:
            self.axis.set_xlabel(self.x_label)

        # ============ set x axis min max values ============
        if self.x_axis_max_min:
            self.axis.set_xlim(self.x_axis_max_min)

        # ============ set y axis min max values ============
        if self.y_axis_max_min:
            self.axis.set_ylim(self.y_axis_max_min)

        # ============ create the x axis limit line  ============
        if self.x_line_limits:
            for x in self.x_line_limits:
                line_width = x['line width'] if 'line width' in x.keys() else 3
                if 'coordinates' not in x.keys(): raise ValueError('Missing coordinates from line limit')
                if 'color' in x.keys():  # check to see if properties has 'color'
                    self.axis.axvline(x=x['coordinates'], color=x['color'], linestyle='--')
                else:
                    self.axis.axvline(x=x['coordinates'], linestyle='--')

        # ============ create the y right axis limit line  ============
        if self.y_line_limits:
            for y in self.y_line_limits:
                line_width = y['line width'] if 'line width' in y.keys() else 3
                if 'coordinates' not in y.keys(): raise ValueError('Missing coordinates from line limit')
                if 'color' in y.keys():  # check to see if properties has 'color'
                    self.axis.axhline(y=y['coordinates'], color=y['color'], linestyle='--')
                else:
                    self.axis.axhline(y=y['coordinates'], linestyle='--')
                self.axis.annotate(y['display name'], xy=(0, y['coordinates']), xycoords='data', xytext=(1.5, 1.5), textcoords='offset points')
        # ============ Graph grid on/off ============
        if self.grid_on:
            self.axis.grid(True)

        # ============ place figure in window ============
        if gui_container:
            figure_canvas = FigureCanvasTkAgg(figure, master=gui_container)
        else:
            figure_canvas = FigureCanvasTkAgg(figure, master=self)
        figure_canvas.draw()
        # ============ create the toolbar/nav_buttons object ============
        if nav_buttons:
            if gui_container:
                NavigationToolbar2Tk(figure_canvas, gui_container)
            else:
                NavigationToolbar2Tk(figure_canvas, self)

        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        # ============ bind function on graph click ============
        if click_graph_new_window:
            figure_canvas.mpl_connect('button_press_event', self.open_graph_in_window)
        return figure_canvas

    def open_graph_in_window(self, event=None):
        """
            crate a resizable window with graph that have nav buttons
        """
        if self.window_open:
            return  # Do nothing if the window is already open
        self.window_open = True  # Set the flag to indicate the window is open
        # ============ define window size for new graph on click ============
        window = CTkToplevel(self)
        window.title(self.graph_title)
        window.geometry(f"{400}x{250}")
        # Reset the flag when the window is closed
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))
        # ========================================
        # ============ create a graph ============
        # ========================================
        self.graph = self.figure_maker(nav_buttons=True, gui_container=window, click_graph_new_window=False)

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.

        This function is called when the user closes the window. It resets the
        `window_open` flag to `False` to allow a new window to be opened in the
        future, and then destroys the window.

        Parameters:
        window (CTkToplevel): The window instance that is being closed.
        """
        self.window_open = False  # Reset the flag
        window.destroy()  # Close the window


class CustomHeatMapFromTable(CTkFrame):
    """
    A class that extends CTkFrame to create a custom heatmap from a given pandas DataFrame.

    Attributes:
        data_table (DataFrame): The source data for the heatmap.
        graph_title (str): The title of the graph.
        dpi (int): The resolution of the figure in dots-per-inch.
        annot (bool): Flag to annotate each cell with the numeric value.
        click_graph_new_window (bool): Flag to enable opening the graph in a new window on click.
        y_label (str): The label for the y-axis.
        x_label (str): The label for the x-axis.
        heat_map_y (str): The column name to be used as rows in the heatmap.
        heat_map_x (str): The column name to be used as columns in the heatmap.
        value_col (str): The column name whose values will fill the heatmap.
        pint_circle (bool): Flag to enable drawing a circle around the heatmap.
        circle_color (str): The color of the circle around the heatmap.
        show_values (bool): Flag to show values on the heatmap.
    """

    def __init__(self, *args,
                 data_table: DataFrame,
                 graph_size: tuple = (3, 3),
                 graph_title: str = None,
                 dpi: int = 60,
                 annot: bool = False,
                 click_graph_new_window: bool = True,
                 nav_buttons: bool = False,
                 y_label: str = None,
                 x_label: str = None,
                 heat_map_y: str,
                 heat_map_x: str,
                 value_col: str,
                 scale_max_min: tuple = None,
                 pint_circle: bool = False,
                 circle_color: str = 'black',
                 show_values=False,
                 show_values_in_popup: bool = False,
                 value_decimal_places: int = 0,
                 **kwargs):
        """
        Initializes the CustomHeatMapFromTable with the provided parameters and creates the heatmap.

        :param *args: Variable length argument list for CTkFrame.
        :param **kwargs: Arbitrary keyword arguments for CTkFrame.
        """
        super().__init__(*args, **kwargs)
        self.click_graph_new_window = click_graph_new_window
        self.graph_title = graph_title
        self.grid_size = graph_size
        # Pivot the data_table to create a matrix suitable for a heatmap
        self.data_table = data_table.pivot(index=heat_map_y, columns=heat_map_x, values=value_col)
        self.dpi = dpi
        self.annot = annot
        self.max_min = scale_max_min
        self.x_label = x_label
        self.y_label = y_label
        self.heat_map_y = heat_map_y
        self.heat_map_x = heat_map_x
        self.value_col = value_col
        self.pint_circle = pint_circle
        self.circle_color = circle_color
        self.show_values = show_values
        self.show_values_in_popup = show_values_in_popup
        self.value_decimal_places = value_decimal_places
        self.axis = None
        self.cax = None
        self.cbar = None
        self.figure = None
        self.window_open = False
        # Create a graph based on the initialized attributes
        self.figure_canvas = self.figure_maker(nav_buttons, click_graph_new_window=self.click_graph_new_window, show_values=self.show_values)

    def figure_maker(self, nav_buttons: bool = True, gui_container: CTkFrame | CTkToplevel = None, click_graph_new_window: bool = False, show_values: bool = False):
        """
        Creates and configures the figure, axes, and other graphical elements of the heatmap.

        :param nav_buttons: Flag to display navigation buttons.
        :param gui_container: The GUI container for the figure canvas.
        :param click_graph_new_window: Flag to enable graph interaction for opening in a new window.
        :param show_values: Flag to display values on the heatmap.
        :return: The figure canvas widget.
        """
        # Create a figure with the specified DPI and tight layout
        self.figure = Figure(dpi=self.dpi, layout='tight', figsize=self.grid_size)
        # Determine the master widget for the FigureCanvasTkAgg
        if gui_container:
            figure_canvas = FigureCanvasTkAgg(self.figure, master=gui_container)
        else:
            figure_canvas = FigureCanvasTkAgg(self.figure, master=self)
        figure_canvas.draw()

        # Add navigation toolbar if nav_buttons is True
        if nav_buttons:
            if gui_container:
                NavigationToolbar2Tk(figure_canvas, gui_container)
            else:
                NavigationToolbar2Tk(figure_canvas, self)

        # Create a subplot for the heatmap
        self.axis = self.figure.add_subplot()

        # Check if self.max_min is correctly structured as a list or tuple with exactly two elements
        if isinstance(self.max_min, (list, tuple)) and len(self.max_min) == 2:
            vmin, vmax = self.max_min
        else:
            vmin, vmax = None, None  # Fallback to automatic scaling if check fails

        # Generate the heatmap with scale limits applied
        self.cax = self.axis.matshow(self.data_table, cmap='coolwarm', interpolation='nearest', vmin=vmin, vmax=vmax)

        # Set axes labels and tick marks
        self.configure_axes(show_values=show_values)

        # Optionally draw a circle around the heatmap
        if self.pint_circle:
            self.draw_circle()

        # Normalize the colormap and add a colorbar
        self.add_colorbar()

        # Set the graph title
        if self.graph_title:
            self.axis.set_title(self.graph_title)

        # Configure the canvas widget and pack it into the GUI
        canvas_widget = figure_canvas.get_tk_widget()
        canvas_widget.pack(side='top', fill='both', expand=True)
        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        # Bind function on graph click if enabled
        if click_graph_new_window:
            figure_canvas.mpl_connect('button_press_event', self.right_click_callback)

        return figure_canvas

    def configure_axes(self, show_values):
        """
        Configures the axes of the heatmap, including setting tick labels and hiding spines.
        """
        # Adjust the margins and set tick labels based on the DataFrame's columns and index
        self.axis.margins(0.05)

        # Reduce the number of y-axis tick labels if there are more than 10
        if len(self.data_table.index) > 10:
            # Calculate the step size to skip some labels
            step = len(self.data_table.index) // 10
            # Set the tick positions and labels with the step size
            self.axis.set_yticks(range(0, len(self.data_table.index), step))
            self.axis.set_yticklabels(self.data_table.index[::step])
        else:
            self.axis.set_yticks(range(len(self.data_table.index)))
            self.axis.set_yticklabels(self.data_table.index)

        # Reduce the number of x-axis tick labels if there are more than 10
        if len(self.data_table.columns) > 10:
            # Calculate the step size to skip some labels
            step = len(self.data_table.columns) // 10
            # Set the tick positions and labels with the step size
            self.axis.set_xticks(range(0, len(self.data_table.columns), step))
            self.axis.set_xticklabels(self.data_table.columns[::step], rotation='vertical')
        else:
            self.axis.set_xticks(range(len(self.data_table.columns)))
            self.axis.set_xticklabels(self.data_table.columns)

        # Hide the tick marks and plot spines for a cleaner appearance
        self.axis.tick_params(axis='y', which='both', length=0)
        self.axis.tick_params(axis='x', which='both', length=0)
        for spine in self.axis.spines.values():
            spine.set_visible(False)

        # Optionally display values in each cell
        if show_values:
            if self.value_decimal_places > 0 and type(self.value_decimal_places) is int:
                decimal_format = f"{{val:.{self.value_decimal_places}f}}"  # Dynamic format string
                for (i, j), val in np.ndenumerate(self.data_table):
                    if not np.isnan(val):  # Only display if the value is not NaN
                        formatted_value = decimal_format.format(val=val)  # Format value with dynamic precision
                        self.axis.text(j, i, formatted_value, ha='center', va='center', color='black')

    def draw_circle(self):
        """
        Draws a circle around the heatmap for stylistic purposes.
        """
        radius = max(len(self.data_table.columns), len(self.data_table.index)) * 0.6
        circle = Circle((len(self.data_table.columns) / 2 - 0.5, len(self.data_table.index) / 2 - 0.5), radius,
                        color=self.circle_color, fill=False, linewidth=2, clip_on=False)
        self.axis.add_artist(circle)

    def add_colorbar(self):
        """
        Adds a colorbar to the heatmap, with custom ticks indicating the min and max values.
        """
        norm = Normalize(vmin=self.data_table.min().min(), vmax=self.data_table.max().max())
        self.cbar = self.figure.colorbar(self.cax, ax=self.axis, shrink=0.8, pad=0.1, ticks=[norm.vmin, norm.vmax])
        self.cbar.ax.set_yticklabels([f'{norm.vmin:.2f}', f'{norm.vmax:.2f}'])

    def right_click_callback(self, event=None):
        """
        Callback function to handle the right-click event on the plot.

        Parameters:
            event (matplotlib.backend_bases.MouseEvent): The event object that contains information about the event.
        """
        if event.button == MouseButton.RIGHT:
            self.open_graph_in_window(event)

    def open_graph_in_window(self, event=None):
        """
            crate a resizable window with graph that have nav buttons
        """
        if self.window_open:
            return  # Do nothing if the window is already open
        self.window_open = True  # Set the flag to indicate the window is open
        # ============ define window size for new graph on click ============
        window = CTkToplevel(self)
        window.title(self.graph_title)
        window.geometry(f"{600}x{600}")
        # Reset the flag when the window is closed
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))
        # ========================================
        # ============ create a graph ============
        # ========================================

        self.figure_canvas = self.figure_maker(nav_buttons=True, gui_container=window, click_graph_new_window=False, show_values=self.show_values_in_popup)

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.

        This function is called when the user closes the window. It resets the
        `window_open` flag to `False` to allow a new window to be opened in the
        future, and then destroys the window.

        Parameters:
        window (CTkToplevel): The window instance that is being closed.
        """
        self.window_open = False  # Reset the flag
        window.destroy()  # Close the window


class CustomPolarPlot(CTkFrame):
    """
    CustomPolarPlot class will create polar graph\n
    :param data_table: type(DataFrame) data to plot, expected columns ['theta', 'r']\n
    :param graph_size: type(tuple) default (400, 250), graph size in pixels\n
    :param graph_title: type(str)\n
    :param click_graph_new_window: type(bool) default True\n
    :param nav_buttons: type(bool) default True, define if to show graph nav buttons\n
    :param cmap: default 'jet', color map for the scatter plot\n
    :param dpi: type(int) default 60, dots per inch\n
    """

    def __init__(self, *args, data_table: DataFrame, graph_size: tuple = (400, 250), graph_title: str = None, dpi: int = 60,
                 nav_buttons: bool = True,
                 cmap='jet',
                 click_graph_new_window: bool = True,
                 r_min: float = None, r_max: float = None,
                 **kwargs):

        super().__init__(*args, **kwargs)
        self.data_table = data_table
        self.graph_size = graph_size
        self.graph_title = graph_title
        self.dpi = dpi
        self.click_graph_new_window = click_graph_new_window
        self.nav_buttons = nav_buttons
        self.cmap = cmap
        self.width, self.height = graph_size
        self.r_min = r_min
        self.r_max = r_max
        self.window_open = False
        self.figure_canvas = self.figure_maker(nav_buttons, click_graph_new_window=click_graph_new_window)

    def figure_maker(self, nav_buttons: bool = True, gui_container: CTkFrame | CTkToplevel = None,
                     click_graph_new_window: bool = False):
        """
        Creates and configures a matplotlib figure with a polar plot, optional navigation buttons, and click event handling.

        Parameters:
        nav_buttons (bool): If True, navigation toolbar buttons will be added to the figure. Defaults to True.
        gui_container (CTkFrame | CTkToplevel, optional): The container widget where the figure will be placed.
            If None, the figure will be placed in the current context. Defaults to None.
        click_graph_new_window (bool): If True, clicking on the graph will trigger a callback function for handling
            the event, such as opening a new window. Defaults to False.

        Returns:
        FigureCanvasTkAgg: The canvas object containing the created figure, which can be packed into a Tkinter widget.
        """
        # Create a figure
        figure = Figure(figsize=(self.width / self.dpi, self.height / self.dpi), dpi=self.dpi, layout='tight')

        if gui_container:
            figure_canvas = FigureCanvasTkAgg(figure, master=gui_container)
        else:
            figure_canvas = FigureCanvasTkAgg(figure, master=self)
        figure_canvas.draw()

        # Navigation toolbar
        if nav_buttons:
            if gui_container:
                NavigationToolbar2Tk(figure_canvas, gui_container)
            else:
                NavigationToolbar2Tk(figure_canvas, self)

        # Create polar axes
        ax = figure.add_subplot(111, polar=True)
        ax.plot(self.data_table['theta'], self.data_table['r'], color='blue')  # Simple line plot
        ax.scatter(self.data_table['theta'], self.data_table['r'], c=self.data_table['r'], cmap=self.cmap,
                   alpha=0.75)  # Scatter plot

        # Set r limits
        if self.r_min is not None and self.r_max is not None:
            ax.set_ylim([self.r_min, self.r_max])

        # Reduce the number of radial ticks (y-axis)
        num_radial_ticks = 5  # You can adjust this number
        r_ticks = np.linspace(ax.get_ylim()[0], ax.get_ylim()[1], num_radial_ticks)
        ax.set_yticks(r_ticks)

        # Reduce the number of angular ticks (x-axis)
        num_angular_ticks = 8  # You can adjust this number (e.g., 4, 6, 8, 12)
        theta_ticks = np.linspace(0, 2 * np.pi, num_angular_ticks, endpoint=False)
        ax.set_xticks(theta_ticks)

        # Optionally, format the tick labels
        ax.set_xticklabels([f'{int(np.degrees(x))}°' for x in theta_ticks])

        # Optionally set title
        if self.graph_title:
            ax.set_title(self.graph_title, va='bottom')

        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        if click_graph_new_window:
            figure_canvas.mpl_connect('button_press_event', self.open_graph_in_window)

        return figure_canvas

    def open_graph_in_window(self, event=None):
        """
        Opens a new window and creates a matplotlib figure within it.

        Parameters:
        event (optional): The event that triggers this function, such as a button press. Defaults to None.
        """
        if self.window_open:
            return  # Do nothing if the window is already open
        self.window_open = True  # Set the flag to indicate the window is open
        window = CTkToplevel(self)
        window.geometry(f"400x400")
        # Reset the flag when the window is closed
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))
        self.figure_maker(nav_buttons=True, gui_container=window, click_graph_new_window=False)

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.

        This function is called when the user closes the window. It resets the
        `window_open` flag to `False` to allow a new window to be opened in the
        future, and then destroys the window.

        Parameters:
        window (CTkToplevel): The window instance that is being closed.
        """
        self.window_open = False  # Reset the flag
        window.destroy()  # Close the window


class CustomHeatmapWithSideView(CTkFrame):
    """
    A custom heatmap widget with a side view graph.

    This class creates a frame containing a heatmap and a side view graph,
    along with various customization options.
    """

    def __init__(self, *args,
                 data_table: DataFrame,
                 graph_size: tuple = (800, 600),
                 graph_title: str = None,
                 dpi: int = 60,
                 annot: bool = False,
                 click_graph_new_window: bool = True,
                 nav_buttons: bool = False,
                 _buttons: bool = False,
                 line_width: int = 0,
                 xticklabels="auto",
                 yticklabels="auto",
                 y_label: str = None,
                 x_label: str = None,
                 max_min: list = None,
                 cmap='jet',
                 HeatPlotLoc: int = 0,
                 Ax_Az_Dec: int = 0,
                 Threshold: float = None,
                 **kwargs):

        super().__init__(*args, **kwargs)
        self.click_graph_new_window = click_graph_new_window
        self.graph_title = graph_title
        self.graph_size = graph_size
        self.data_table = data_table
        self.dpi = dpi
        self.annot = annot
        self.line_width = line_width
        self.xticklabels = xticklabels
        self.yticklabels = yticklabels
        self.width = graph_size[0] / self.dpi
        self.height = graph_size[1] / self.dpi
        self.max_min = max_min
        self.x_label = x_label
        self.y_label = y_label
        self.cmap = cmap
        self.window_open = False
        self.HeatPlotLoc = HeatPlotLoc
        self.Ax_Az_Dec = Ax_Az_Dec
        self.threshold = Threshold

        self.figure, self.ax_colorbar, self.ax_heatmap, self.ax_xz = None, None, None, None
        self.figure_canvas = self.figure_maker(nav_buttons, click_graph_new_window=self.click_graph_new_window)

    def calculate_optimal_ticks(self, ax, orientation='x'):
        """
        Calculate the optimal number of ticks based on figure size and orientation.
        """
        fig_width = self.figure.get_size_inches()[0] * self.figure.dpi
        fig_height = self.figure.get_size_inches()[1] * self.figure.dpi

        bbox = ax.get_window_extent()
        if orientation == 'x':
            axis_length = bbox.width
            min_spacing = 50  # Minimum pixels between ticks
        else:
            axis_length = bbox.height
            min_spacing = 30  # Minimum pixels between ticks

        max_ticks = max(2, int(axis_length / min_spacing))
        return max_ticks

    def set_axis_ticks(self, ax, orientation='x'):
        """
        Set the optimal number of ticks for an axis.
        """
        n_ticks = self.calculate_optimal_ticks(ax, orientation)

        if orientation == 'x':
            start, end = ax.get_xlim()
            ax.xaxis.set_major_locator(MaxNLocator(n_ticks))
        else:
            start, end = ax.get_ylim()
            ax.yaxis.set_major_locator(MaxNLocator(n_ticks))

    @staticmethod
    def format_ticks(value, pos):
        """
        Format the ticks to show up to 4 decimal places.
        """
        return f'{value:.1f}'

    def _apply_real_axis_ticks(self):
        """
        Replace seaborn's integer cell-position ticks with actual
        coordinate values from the DataFrame columns (X) and index (Y).
        """
        x_values = self.data_table.columns.astype(float)
        y_values = self.data_table.index.astype(float)

        n_cols = len(x_values)
        n_rows = len(y_values)

        # --- X axis for heatmap ---
        n_x_ticks = self.calculate_optimal_ticks(self.ax_heatmap, 'x')
        x_tick_indices = np.linspace(0, n_cols - 1, n_x_ticks, dtype=int)
        x_tick_positions = x_tick_indices + 0.5
        x_tick_labels = [f"{x_values[i]:.4f}" for i in x_tick_indices]

        self.ax_heatmap.set_xticks(x_tick_positions)
        self.ax_heatmap.set_xticklabels(x_tick_labels, rotation=45, ha='right', fontsize=8)

        # --- Y axis for heatmap ---
        n_y_ticks = self.calculate_optimal_ticks(self.ax_heatmap, 'y')
        y_tick_indices = np.linspace(0, n_rows - 1, n_y_ticks, dtype=int)
        y_tick_positions = y_tick_indices + 0.5
        y_tick_labels = [f"{y_values[i]:.4f}" for i in y_tick_indices]

        self.ax_heatmap.set_yticks(y_tick_positions)
        self.ax_heatmap.set_yticklabels(y_tick_labels, rotation=0, fontsize=8)

        # --- X axis for line plot, match exactly the heatmap X ticks ---
        if self.Ax_Az_Dec == 0 and self.ax_xz is not None:
            x_tick_real_values = x_values[x_tick_indices]  # real float values at same indices
            self.ax_xz.set_xticks(x_tick_real_values)  # set ticks at those real values
            self.ax_xz.set_xticklabels(x_tick_labels, rotation=45, ha='right', fontsize=8)
            self.ax_xz.set_xlim(x_values.min(), x_values.max())

    def figure_maker(self, nav_buttons: bool = False, gui_container: CTkFrame | CTkToplevel = None,
                     click_graph_new_window: bool = True):
        """
        Create and return a figure with heatmap and side view.
        """
        self.figure = Figure(figsize=(self.width, self.height), dpi=self.dpi)

        if gui_container:
            figure_canvas = FigureCanvasTkAgg(self.figure, master=gui_container)
        else:
            figure_canvas = FigureCanvasTkAgg(self.figure, master=self)
        figure_canvas.draw()

        if nav_buttons:
            if gui_container:
                NavigationToolbar2Tk(figure_canvas, gui_container)
            else:
                NavigationToolbar2Tk(figure_canvas, self)

        if self.Ax_Az_Dec == 0:
            if self.HeatPlotLoc == 0:
                gs = self.figure.add_gridspec(3, 1, height_ratios=[0.05, 0.475, 0.475])
                self.ax_colorbar = self.figure.add_subplot(gs[0])
                self.ax_heatmap = self.figure.add_subplot(gs[1])
                self.ax_xz = self.figure.add_subplot(gs[2])
            else:
                gs = self.figure.add_gridspec(3, 1, height_ratios=[0.05, 0.475, 0.475])
                self.ax_colorbar = self.figure.add_subplot(gs[0])
                self.ax_xz = self.figure.add_subplot(gs[1])
                self.ax_heatmap = self.figure.add_subplot(gs[2])

            x_values = self.data_table.columns.astype(float)
            x_min, x_max = x_values.min(), x_values.max()

            for y in range(self.data_table.shape[0]):
                self.ax_xz.plot(x_values, self.data_table.iloc[y], alpha=0.5)

            if self.threshold is not None:
                self.ax_xz.axhline(y=self.threshold, color='r', linestyle='--',
                                   label=f'Threshold: {self.threshold}')
                self.ax_xz.legend()

            self.ax_xz.set_xlabel(self.x_label, fontsize=12)
            self.ax_xz.set_ylabel('Z', fontsize=12)
            self.ax_xz.set_xlim(x_min, x_max)
        else:
            gs = self.figure.add_gridspec(2, 1, height_ratios=[0.05, 0.95])
            self.ax_colorbar = self.figure.add_subplot(gs[0])
            self.ax_heatmap = self.figure.add_subplot(gs[1])

        if self.max_min is None:
            min_val = self.data_table.min().min()
            max_val = self.data_table.max().max()
        else:
            min_val, max_val = self.max_min

        heatmap(self.data_table,
                ax=self.ax_heatmap,
                cmap=self.cmap,
                linewidths=self.line_width,
                annot=self.annot,
                xticklabels=False,  # ← CHANGED from self.xticklabels
                yticklabels=False,  # ← CHANGED from self.yticklabels
                vmin=min_val,
                vmax=max_val,
                cbar=False)

        self.ax_heatmap.invert_yaxis()
        self.ax_heatmap.set_xlabel(self.x_label, fontsize=12)
        self.ax_heatmap.set_ylabel(self.y_label, fontsize=12)

        norm = plt.Normalize(min_val, max_val)
        sm = plt.cm.ScalarMappable(cmap=self.cmap, norm=norm)
        sm.set_array([])
        cbar = self.figure.colorbar(sm, cax=self.ax_colorbar, orientation='horizontal', aspect=30)
        cbar.set_ticks(np.linspace(min_val, max_val, 11))
        self.ax_colorbar.xaxis.set_ticks_position('top')
        self.ax_colorbar.xaxis.set_label_position('top')

        if self.Ax_Az_Dec == 0:
            self.ax_xz.set_ylim(min_val, max_val)

        formatter = FuncFormatter(self.format_ticks)
        self.ax_heatmap.xaxis.set_major_formatter(formatter)
        self.ax_heatmap.yaxis.set_major_formatter(formatter)

        if self.Ax_Az_Dec == 0:
            self.ax_xz.xaxis.set_major_formatter(formatter)
            self.ax_xz.yaxis.set_major_formatter(formatter)

        # Set optimal ticks for line plot only
        self.figure.canvas.draw()
        if self.Ax_Az_Dec == 0:
            self.set_axis_ticks(self.ax_xz, 'x')
            self.set_axis_ticks(self.ax_xz, 'y')

        if self.graph_title:
            self.figure.suptitle(self.graph_title, fontsize=20, y=0.98, weight='bold')

        self.figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))

        # ← Apply real coordinate values to heatmap axes, called last
        self._apply_real_axis_ticks()
        self.figure.canvas.draw()

        figure_canvas.get_tk_widget().pack(fill="both", expand=1)

        if click_graph_new_window:
            figure_canvas.mpl_connect('button_press_event', self.right_click_callback)

        return figure_canvas

    def update_range(self, new_range: list = None):
        """
        Update the color range of the heatmap and side view.
        """
        if self.figure is None or self.ax_heatmap is None:
            return

        if new_range:
            self.max_min = new_range
        min_val, max_val = self.max_min

        self.ax_heatmap.collections[0].set_clim(self.max_min)

        self.ax_colorbar.clear()
        norm = plt.Normalize(min_val, max_val)
        sm = plt.cm.ScalarMappable(cmap=self.cmap, norm=norm)
        sm.set_array([])
        cbar = self.figure.colorbar(sm, cax=self.ax_colorbar, orientation='horizontal', aspect=30)
        cbar.set_ticks(np.linspace(min_val, max_val, 11))
        self.ax_colorbar.xaxis.set_ticks_position('top')
        self.ax_colorbar.xaxis.set_label_position('top')

        if self.Ax_Az_Dec == 0:
            self.ax_xz.set_ylim(min_val, max_val)
            if self.threshold is not None:
                for line in self.ax_xz.lines[:]:
                    if line.get_linestyle() == '--':
                        line.remove()
                self.ax_xz.axhline(y=self.threshold, color='r', linestyle='--',
                                   label=f'Threshold: {self.threshold}')
                self.ax_xz.legend()

        # Update ticks
        self.set_axis_ticks(self.ax_heatmap, 'x')
        self.set_axis_ticks(self.ax_heatmap, 'y')
        if self.Ax_Az_Dec == 0:
            self.set_axis_ticks(self.ax_xz, 'x')
            self.set_axis_ticks(self.ax_xz, 'y')

        self.figure_canvas.draw_idle()

    def right_click_callback(self, event=None):
        """
        Callback function for right-click events on the graph.
        """
        if event.button == MouseButton.RIGHT:
            self.open_graph_in_window(event)

    def open_graph_in_window(self, event=None):
        """
        Open the graph in a new resizable window with navigation buttons.
        """
        if self.window_open:
            return

        self.window_open = True
        window = CTkToplevel(self)
        window.title(self.graph_title)
        window.geometry(f"{800}x{600}")
        window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(window))
        self.figure_canvas = self.figure_maker(nav_buttons=False, gui_container=window, click_graph_new_window=False)

    def on_window_close(self, window):
        """
        Callback function to handle the window close event.
        """
        self.window_open = False
        window.destroy()