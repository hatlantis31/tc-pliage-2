"""
_plot_utils.py

This module provides utility functions for plotting with matplotlib. It is intended for internal use within the project to facilitate common plotting tasks such as adding annotated lines to plots.

Functions:
- add_line_annotations: Adds annotated lines (horizontal or vertical) to a matplotlib axis.

Note: This module is named with a leading underscore to indicate that it is intended for internal use and is not part of the public API of the project.
"""


def add_line_annotations(axis, line_limits, orientation='horizontal', side='left'):
    """
    Adds line annotations to a matplotlib axis.

    Draws lines (horizontal or vertical) on the specified axis according to provided
    specifications and annotates them with display names. The annotations are positioned
    based on the specified side (left, right, bottom) relative to the lines.

    Parameters:
    - axis : matplotlib.axes.Axes
        The matplotlib axis object to draw lines and annotations on.
    - line_limits : list of dict
        A list of dictionaries, where each dictionary specifies the properties of a line
        and its annotation. Expected keys are 'coordinates', 'line width', 'color', and
        'display name'.
    - orientation : str, optional
        The orientation of the lines to draw ('horizontal' or 'vertical'). Default is 'horizontal'.
    - side : str, optional
        The side relative to the axis on which to place the text annotation ('left', 'right', 'bottom').
        Default is 'left'.

    Raises:
    - ValueError: If 'coordinates' key is missing from any item in line_limits.

    Returns:
    None
    """
    if not line_limits:
        # No lines to add, so exit the function early
        return

    for line in line_limits:
        line_width = line.get('line width', 3)  # Use a default line width of 3 if not specified
        if 'coordinates' not in line:
            raise ValueError("Missing 'coordinates' from line limit specification.")

        color = line.get('color', 'black')  # Default color is black if not specified
        display_name = line.get('display name', '')  # Default display name is empty string

        # Draw the line based on specified orientation
        if orientation == 'horizontal':
            axis.axhline(y=line['coordinates'], color=color, linestyle='--', linewidth=line_width)
        elif orientation == 'vertical':
            axis.axvline(x=line['coordinates'], color=color, linestyle='--', linewidth=line_width)

        # Annotate the line if a display name is provided
        if display_name:
            # Calculate relative position for annotation, adjusted based on orientation and side
            if orientation == 'horizontal':
                rel_pos = (line['coordinates'] - axis.get_ylim()[0]) / (axis.get_ylim()[1] - axis.get_ylim()[0])
                x_pos = -0.05 if side == 'left' else 1.05  # Determine x position based on side
                axis.text(x_pos, rel_pos, display_name, verticalalignment='bottom',
                          horizontalalignment='left' if side == 'left' else 'right',
                          transform=axis.transAxes, fontsize=10, color=color, clip_on=False)
            elif orientation == 'vertical':
                rel_pos = (line['coordinates'] - axis.get_xlim()[0]) / (axis.get_xlim()[1] - axis.get_xlim()[0])
                axis.text(rel_pos, -0.05, display_name, verticalalignment='top',
                          horizontalalignment='center', transform=axis.transAxes,
                          fontsize=10, color=color, clip_on=False)