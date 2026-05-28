"""
This module provides custom GUI components built on top of the customtkinter library.

It includes the following classes:
- CustomListBox: A customized listbox widget with enhanced functionality.
- CustomButtonProgressBarFrame: A frame that can switch between a button and a progress bar.
- CustomMessageBox: A custom message box for displaying messages to the user.

These components are designed to be used in a larger application, providing more
flexible and feature-rich alternatives to standard tkinter widgets.
"""

import tkinter
import customtkinter
import calendar

from datetime import datetime
from typing import Callable

from customtkinter.windows.widgets.utility import pop_from_dict_by_set


class CustomListBox(customtkinter.CTkTextbox):
    def __init__(self, *args,
                 command: Callable = None,
                 select_mode="extended",
                 variable=None,
                 **kwargs):
        super().__init__(*args, border_width=0, corner_radius=5, **kwargs)
        self.current_value = None
        self.command = command
        self.variable: tkinter.Variable = variable

        # Define list box
        self._textbox = tkinter.Listbox(self,
                                        foreground=self._apply_appearance_mode(self._text_color),
                                        background=self._apply_appearance_mode(self._fg_color),
                                        width=0,
                                        height=0,
                                        font=self._apply_font_scaling(self._font),
                                        highlightthickness=0,
                                        relief="flat",
                                        activestyle='none',
                                        selectmode=select_mode,
                                        listvariable=self.variable,
                                        **pop_from_dict_by_set(kwargs, self._valid_tk_text_attributes))
        self._textbox.bind("<<ListboxSelect>>", self.command)
        self._textbox.configure(yscrollcommand=self._y_scrollbar.set)
        self._textbox.configure(xscrollcommand=self._x_scrollbar.set)
        self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)

    def _draw(self, no_color_updates=False):
        self._textbox.configure(foreground=self._apply_appearance_mode(self._text_color),
                                background=self._apply_appearance_mode(self._fg_color))
        super()._draw(no_color_updates)
        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._corner_radius),
                                                                              self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            if self._fg_color == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._bg_color),
                                        outline=self._apply_appearance_mode(self._bg_color))
                self._x_scrollbar.configure(fg_color=self._bg_color, button_color=self._scrollbar_button_color,
                                            button_hover_color=self._scrollbar_button_hover_color)
                self._y_scrollbar.configure(fg_color=self._bg_color, button_color=self._scrollbar_button_color,
                                            button_hover_color=self._scrollbar_button_hover_color)
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._fg_color),
                                        outline=self._apply_appearance_mode(self._fg_color))
                self._x_scrollbar.configure(fg_color=self._fg_color, button_color=self._scrollbar_button_color,
                                            button_hover_color=self._scrollbar_button_hover_color)
                self._y_scrollbar.configure(fg_color=self._fg_color, button_color=self._scrollbar_button_color,
                                            button_hover_color=self._scrollbar_button_hover_color)

            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        self._canvas.tag_lower("inner_parts")
        self._canvas.tag_lower("border_parts")

    def add_items_list(self, items: list[str]):
        """
        add a list of str to the list,
        will remove any items that are int the list_box
        :items: items list [str]
        """
        self._textbox.delete(0, "end")
        self._textbox.insert(0, *items)

    def insert(self, item: str):
        """
        add a single item to the  List
        :items: items str
        """
        return self._textbox.insert("end", item)

    def clear_list(self):
        return self._textbox.delete(0, "end")

    def disable(self):
        return self._textbox.configure(state="disabled")

    def enable(self):
        return self._textbox.configure(state="normal")

    def get_selected(self) -> list[str]:
        """
        :return: list of all selected items in the list
        """
        return [self._textbox.get(i) for i in self._textbox.curselection()]


class CustomButtonProgressBarFrame(customtkinter.CTkFrame):
    def __init__(self, master, button_command, button_text, **kwargs):
        super().__init__(master, **kwargs)

        # Configuring the grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.label = None
        self.progress_bar = None

        # Create the initial button
        self.button = customtkinter.CTkButton(self, text=button_text, command=button_command)
        self.button.grid(row=1, column=0, rowspan=2, pady=2, padx=2, sticky="nsew")

    def run(self, progressbar_label_text):
        """
        Remove button and start ProgressBar
        """
        self._clear_widgets()

        # Create the label and progress bar
        self.label = customtkinter.CTkLabel(self, text=progressbar_label_text)
        self.label.grid(row=0, column=0, pady=(1, 1), padx=2, sticky="nsew")
        self.progress_bar = customtkinter.CTkProgressBar(self)
        self.progress_bar.grid(row=1, column=0, pady=(0, 1), padx=2, sticky="nsew")
        self.progress_bar.start()

    def update_frame_after_command(self, button_text, button_command, color=None):
        """
        Update the frame when command completes
        """
        self._clear_widgets()

        # Create a button with the specified text and color
        if color:
            self.button = customtkinter.CTkButton(self, text=button_text, command=button_command, fg_color=color)
        else:
            self.button = customtkinter.CTkButton(self, text=button_text, command=button_command)
        self.button.grid(row=1, column=0, rowspan=2, pady=2, padx=2, sticky="nsew")

    def _clear_widgets(self):
        """
        Safely destroy existing widgets
        """
        if hasattr(self, 'button') and self.button is not None:
            try:
                self.button.destroy()
            except Exception:
                pass
        self.button = None

        if hasattr(self, 'label') and self.label is not None:
            try:
                self.label.destroy()
            except Exception:
                pass
        self.label = None

        if hasattr(self, 'progress_bar') and self.progress_bar is not None:
            try:
                self.progress_bar.stop()
                self.progress_bar.destroy()
            except Exception:
                pass
        self.progress_bar = None

    def disabled_button(self):
        """
        Disable the button
        """
        if hasattr(self, 'button') and self.button is not None:
            try:
                self.button.configure(state="disabled")
            except Exception:
                pass

    def enable_button(self):
        """
        Enable the button
        """
        if hasattr(self, 'button') and self.button is not None:
            try:
                self.button.configure(state="normal")
            except Exception:
                pass


class CustomMessageBox(customtkinter.CTkToplevel):
    """
    A custom message box that displays a message and an OK button.
    """

    def __init__(self, message):
        super().__init__()
        self.title('Nikon log handler')

        # 1. Make it stay on top
        self.attributes("-topmost", True)

        # 2. Prevent interaction with the main window while this is open (Modal)
        self.grab_set()

        # Create a label for the message
        self.message_label = customtkinter.CTkLabel(
            self,
            text=message,
            font=("Arial", 14),
            wraplength=350
        )
        self.message_label.pack(pady=20, padx=20)

        # 3. THIS IS THE KEY: command=self.destroy
        # When clicked, this destroys the window, which satisfies
        # the 'wait_window' call in the main thread.
        self.ok_button = customtkinter.CTkButton(
            self,
            text="OK",
            command=self.destroy
        )
        self.ok_button.pack(pady=10)

        # Set the appearance mode (light or dark)
        customtkinter.set_appearance_mode("dark")

    def show(self):
        """
        Display the message box.
        """
        self.mainloop()


class DateSelectionDialog(customtkinter.CTkToplevel):
    """Dialog for selecting start date for analysis using customtkinter"""

    def __init__(self, parent=None, min_date=None, max_date=None):
        """
        Initialize date selection dialog

        Args:
            parent: Parent window
            min_date: Minimum date available in data (datetime)
            max_date: Maximum date available in data (datetime)
        """
        super().__init__(parent)

        self.result = None
        self.min_date = min_date
        self.max_date = max_date
        self.user_responded = False

        # Configure dialog window
        self.title("Select Start Date")
        self.geometry("500x200")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Center the dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 125
        self.geometry(f"500x200+{x}+{y}")

        # Set appearance
        self.configure(fg_color=("gray95", "gray10"))

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Create widgets
        self._create_widgets()

        # Setup modal behavior
        self.after(10, self._setup_modal)

    def _setup_modal(self):
        """Setup modal behavior"""
        if self.winfo_exists() and self.master:
            self.transient(self.master)
            self.grab_set()
            self.focus_force()

    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = customtkinter.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=0)

        # Title label
        title_label = customtkinter.CTkLabel(main_frame, text="Select Start Date", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Info label for date range
        if self.min_date and self.max_date:
            date_range_text = f"Range: {self.min_date.strftime('%Y-%m-%d %H:%M')} to {self.max_date.strftime('%Y-%m-%d %H:%M')}"
            info_label = customtkinter.CTkLabel(main_frame, text=date_range_text, font=("Arial", 11))
            info_label.grid(row=1, column=0, pady=(0, 10))

        # Date selection frame
        date_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        date_frame.grid(row=2, column=0, pady=(0, 10))

        # Year dropdown
        year_label = customtkinter.CTkLabel(date_frame, text="Year:", font=("Arial", 12))
        year_label.grid(row=0, column=0, padx=(0, 5), sticky="e")

        years = [str(year) for year in range(self.min_date.year, self.max_date.year + 1)] if self.min_date and self.max_date else [str(datetime.now().year)]
        self.year_var = tkinter.StringVar(value=str(self.min_date.year) if self.min_date else str(datetime.now().year))
        self.year_combo = customtkinter.CTkComboBox(date_frame, variable=self.year_var, values=years, width=80, state="readonly", command=self._update_days)
        self.year_combo.grid(row=0, column=1, padx=(0, 10))

        # Month dropdown
        month_label = customtkinter.CTkLabel(date_frame, text="Month:", font=("Arial", 12))
        month_label.grid(row=0, column=2, padx=(0, 5), sticky="e")

        months = [str(m) for m in range(1, 13)]
        if self.min_date and self.max_date and self.min_date.year == self.max_date.year:
            months = [str(m) for m in range(self.min_date.month, self.max_date.month + 1)]
        self.month_var = tkinter.StringVar(value=str(self.min_date.month) if self.min_date else "1")
        self.month_combo = customtkinter.CTkComboBox(date_frame, variable=self.month_var, values=months, width=60, state="readonly", command=self._update_days)
        self.month_combo.grid(row=0, column=3, padx=(0, 10))

        # Day dropdown
        day_label = customtkinter.CTkLabel(date_frame, text="Day:", font=("Arial", 12))
        day_label.grid(row=0, column=4, padx=(0, 5), sticky="e")

        self.day_var = tkinter.StringVar(value=str(self.min_date.day) if self.min_date else "1")
        self.day_combo = customtkinter.CTkComboBox(date_frame, variable=self.day_var, width=60, state="readonly")
        self.day_combo.grid(row=0, column=5, padx=(0, 10))

        # Hour dropdown
        hour_label = customtkinter.CTkLabel(date_frame, text="Hour:", font=("Arial", 12))
        hour_label.grid(row=0, column=6, padx=(0, 5), sticky="e")

        hours = [str(h) for h in range(24)]
        self.hour_var = tkinter.StringVar(value=str(self.min_date.hour) if self.min_date else "0")
        self.hour_combo = customtkinter.CTkComboBox(date_frame, variable=self.hour_var, values=hours, width=60, state="readonly")
        self.hour_combo.grid(row=0, column=7)

        # Button frame
        button_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 3), weight=1)
        button_frame.grid_columnconfigure((1, 2), weight=0)

        # OK button
        ok_button = customtkinter.CTkButton(button_frame, text="OK", command=self._on_ok, width=100, font=("Arial", 12))
        ok_button.grid(row=0, column=1, padx=5)

        # Cancel button
        cancel_button = customtkinter.CTkButton(button_frame, text="Cancel", command=self._on_cancel, width=100, font=("Arial", 12), fg_color="gray", hover_color="darkgray")
        cancel_button.grid(row=0, column=2, padx=5)

        # Initialize days
        self._update_days()

    def _update_days(self, choice=None):
        """Update days based on selected year and month"""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            max_days = calendar.monthrange(year, month)[1]
            days = [str(day) for day in range(1, max_days + 1)]

            # Restrict days if in min_date or max_date month
            if self.min_date and self.max_date and year == self.min_date.year and month == self.min_date.month:
                days = [str(day) for day in range(self.min_date.day, max_days + 1)]
            if self.max_date and year == self.max_date.year and month == self.max_date.month:
                days = [str(day) for day in range(1, self.max_date.day + 1)]

            self.day_combo.configure(values=days)
            if int(self.day_var.get()) > max_days:
                self.day_var.set(str(max_days))

        except ValueError:
            pass

    def _on_ok(self):
        """Handle OK button click"""
        if self.user_responded:
            return
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            hour = int(self.hour_var.get())
            selected_date = datetime(year, month, day, hour, 0, 0)

            # Validate against min_date and max_date
            if self.min_date and selected_date < self.min_date.replace(microsecond=0):
                self.result = self.min_date.replace(microsecond=0)
            elif self.max_date and selected_date > self.max_date.replace(microsecond=0):
                self.result = self.max_date.replace(microsecond=0)
            else:
                self.result = selected_date
        except ValueError:
            self.result = None

        self.user_responded = True
        self._close_dialog()

    def _on_cancel(self):
        """Handle Cancel button click"""
        if self.user_responded:
            return
        self.result = None
        self.user_responded = True
        self._close_dialog()

    def _close_dialog(self):
        """Close the dialog safely"""
        if self.winfo_exists():
            try:
                self.grab_release()
            except:
                pass
            self.destroy()

    def get_result(self):
        """Get the selected date or None"""
        self.wait_window(self)
        return self.result
