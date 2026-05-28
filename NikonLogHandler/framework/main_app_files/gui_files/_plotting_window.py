"""
This script provides a GUI application for handling and plotting log data using customtkinter.
"""

import logging
import os
import customtkinter
import subprocess
import win32clipboard

from PIL import Image, ImageGrab
from tkinter import PhotoImage
from main_app_files.core_script_files.discovery import discovery
from main_app_files.gui_files._custom_gui_widgets import CustomListBox
from main_app_files.function_files._threading_handler import thread_runner
from main_app_files.function_files.exception_handler_and_reporting import global_exception_handler, NlhException
from tktooltip import ToolTip
from io import BytesIO


class PlotTab(customtkinter.CTkTabview):
    """
    PlotTab class inherits from customtkinter.CTkTabview and is used to create
    a tabbed view where each tab contains a plot frame.
    """

    def __init__(self, master, selected_log: str, plotting_error_msgs: str, log_handler_obj, datatable: object, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color='transparent', bg_color='transparent')
        self.plot_frames = {}

        for plot_option in log_handler_obj.log_handler_information().analysis_option_list:
            self.add(plot_option)

        for plot_option in log_handler_obj.log_handler_information().analysis_option_list:
            self.plot_frames[plot_option] = {}

            # FIX 1: Configure the tab itself to expand its content
            self.tab(plot_option).grid_rowconfigure(0, weight=1)
            self.tab(plot_option).grid_columnconfigure(0, weight=1)

            self.plot_frames[plot_option]['Plot-frame'] = customtkinter.CTkFrame(
                master=self.tab(plot_option)
            )

            # FIX 1: Make the Plot-frame fill the tab
            self.plot_frames[plot_option]['Plot-frame'].grid(
                row=0, column=0, sticky="nsew", padx=1, pady=1
            )

            # FIX 1: Make the Plot-frame's own grid expand internally
            self.plot_frames[plot_option]['Plot-frame'].grid_rowconfigure(0, weight=1)
            self.plot_frames[plot_option]['Plot-frame'].grid_columnconfigure(0, weight=1)

            try:
                log_handler_obj.run_analysis_option(
                    frame=self.plot_frames[plot_option]['Plot-frame'],
                    plot_option=plot_option,
                    parsed_log_name=selected_log,
                    datatable=datatable
                )
            except Exception as e:
                global_exception_handler(type(e), e, e.__traceback__, show_popup=False)
                self.error_label = customtkinter.CTkLabel(
                    master=self.plot_frames[plot_option]['Plot-frame'],
                    text=plotting_error_msgs,
                    text_color='red',
                    font=('', 15, 'bold'),
                    width=250
                )
                self.error_label.grid(row=0, column=0, sticky='ew')

    def _set_grid_tab_by_name(self, name: str):
        self._tab_dict[name].grid(
            row=3, column=0, sticky="nsew",
            padx=self._apply_widget_scaling(max(self._corner_radius, self._border_width)),
            pady=self._apply_widget_scaling(max(self._corner_radius, self._border_width))
        )
        # FIX 1: Ensure the override also keeps weights set
        self._tab_dict[name].grid_rowconfigure(0, weight=1)
        self._tab_dict[name].grid_columnconfigure(0, weight=1)


class PlottingWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, log_handler_name: str = None, app_logo: Image, jmp_logo: Image,
                 excel_logo: Image, copy_graph: Image, log_handler_obj: object = None,
                 parsed_file_dict: dict = None, widgets_text: dict, **kwargs):
        super().__init__(*args, **kwargs)
        WIDTH = 1100
        HEIGHT = int(WIDTH * 0.5)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ===================================
        # =========   Parameters    =========
        # ===================================
        self.selected_log_file = None
        self.title("Analysis Result Window")
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.minsize(WIDTH, HEIGHT)
        self.__widgets_text = widgets_text
        self.image_folder = os.path.abspath(os.curdir) + '\image_files\\'
        app_icon = PhotoImage(file=self.image_folder + 'app_images\\nikon_icon.png')
        self.iconphoto(False, app_icon)

        # Use discovery singleton instead of analysis_files
        if log_handler_obj:
            self.log_handlers_dict = discovery.log_handlers_dict

        self.button_loading_animation_list = []
        self.loading_animation_list = []
        self.tab_view = None
        self.__parsed_file_dict = {}
        self.__log_handlers_list = []
        self.__file_list = []
        self.__selected_log_type = None
        self.__selected_log_handler_object = None

        # ===================================
        # ============    GUI    ============
        # ===================================

        self.columnconfigure(0, weight=0, minsize=int(self.winfo_reqwidth() * (3 / 12)))
        self.columnconfigure(1, weight=1, minsize=int(self.winfo_reqwidth() * (9 / 12)))
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.menu_frame = customtkinter.CTkFrame(master=self)
        self.menu_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=5, padx=5)

        self.menu_frame.rowconfigure(0, weight=0)
        self.menu_frame.columnconfigure((0, 1, 2, 4), weight=0)
        self.menu_frame.columnconfigure(3, weight=1)

        self.__jmp_logo = customtkinter.CTkImage(jmp_logo, size=(30, 30))
        self.__lunch_jmp_button = customtkinter.CTkButton(
            master=self.menu_frame,
            command=self.open_log_in_jmp,
            image=self.__jmp_logo,
            fg_color='transparent',
            width=30,
            border_spacing=0,
            text=''
        )
        self.__lunch_jmp_button.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.__lunch_jmp_button_Tooltip = ToolTip(
            self.__lunch_jmp_button,
            msg=self.__widgets_text['open_jmp_tooltip'],
            refresh=2,
            delay=1
        )

        self.__excel_logo = customtkinter.CTkImage(excel_logo, size=(30, 30))
        self.__lunch_excel_button = customtkinter.CTkButton(
            master=self.menu_frame,
            image=self.__excel_logo,
            command=self.open_log_in_excel,
            fg_color='transparent',
            border_spacing=0,
            width=30,
            text=''
        )
        self.__lunch_excel_button.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.__lunch_excel_button_Tooltip = ToolTip(
            self.__lunch_excel_button,
            msg=self.__widgets_text['open_excel_tooltip'],
            refresh=2,
            delay=1
        )

        self.__copy_graph = customtkinter.CTkImage(copy_graph, size=(25, 25))
        self.__take_image_button = customtkinter.CTkButton(
            master=self.menu_frame,
            image=self.__copy_graph,
            command=lambda: self.capture_to_clipboard(frame=self.tab_view_frame),
            fg_color='gray',
            border_spacing=0,
            width=10,
            text=''
        )
        self.__take_image_button.grid(row=0, column=4, sticky='nsew', padx=5, pady=5)
        self.__take_image_button_Tooltip = ToolTip(
            self.__take_image_button,
            msg=self.__widgets_text['copy_graph_to_clipboard'],
            refresh=2,
            delay=1
        )

        self.file_list_and_dropdown_frame = customtkinter.CTkFrame(master=self)
        self.file_list_and_dropdown_frame.grid(row=1, column=0, rowspan=2, sticky='nsew', padx=5, pady=(0, 5))

        self.file_list_and_dropdown_frame.columnconfigure(0, weight=0)
        self.file_list_and_dropdown_frame.rowconfigure(0, weight=0)
        self.file_list_and_dropdown_frame.rowconfigure(1, weight=0)
        self.file_list_and_dropdown_frame.rowconfigure(2, weight=1)

        self.log_type_dropdown = customtkinter.CTkOptionMenu(
            master=self.file_list_and_dropdown_frame,
            values=[],
            variable=customtkinter.StringVar(value=self.__widgets_text['select_log_type']),
            command=self.log_type_selection
        )
        self.log_type_dropdown.grid(row=0, column=0, sticky='ew', padx=(10, 5), pady=(10, 0))

        self.file_select_label = customtkinter.CTkLabel(
            master=self.file_list_and_dropdown_frame,
            text='File List:',
            font=('', 15, 'bold', 'underline'),
            width=250
        )
        self.file_select_label.grid(row=1, column=0, sticky='ew', padx=5, pady=(10, 0))

        self.log_file_list_box = CustomListBox(
            self.file_list_and_dropdown_frame,
            select_mode='single',
            command=self.plot_selected_logs_file,
            text_color=('black', 'white')
        )
        self.log_file_list_box.grid(row=2, column=0, sticky='nsew', padx=5, pady=(0, 5))

        self.tab_view_frame = customtkinter.CTkFrame(master=self)
        self.tab_view_frame.grid(row=1, column=1, padx=(0, 5), pady=(0, 5), sticky='nsew')

        self.tab_view_frame.columnconfigure(0, weight=1)
        self.tab_view_frame.rowconfigure(0, weight=1)

        self.teb_view_place_holder_message(self.__widgets_text['No_Data'])

        if log_handler_obj and log_handler_name:
            self.load_handler_and_file_list(
                log_handler_name=log_handler_name,
                log_handler_obj=log_handler_obj,
                parsed_file_dict=parsed_file_dict
            )

    # ===================================
    # ============ functions ============
    # ===================================

    def change_buttons_text_and_information_param(self, widgets_text: dict):
        no_supported_log_found = self.__widgets_text['no_supported_log_found']
        select_log_type = self.__widgets_text['select_log_type']
        self.__widgets_text = widgets_text
        self.__lunch_jmp_button_Tooltip = ToolTip(
            self.__lunch_jmp_button,
            msg=self.__widgets_text['open_jmp_tooltip'],
            refresh=2,
            delay=1
        )
        self.__lunch_excel_button_Tooltip = ToolTip(
            self.__lunch_excel_button,
            msg=self.__widgets_text['open_excel_tooltip'],
            refresh=2,
            delay=1
        )
        self.__take_image_button_Tooltip = ToolTip(
            self.__take_image_button,
            msg=self.__widgets_text['copy_graph_to_clipboard'],
            refresh=2,
            delay=1
        )
        if self.log_type_dropdown.get() == no_supported_log_found:
            self.log_type_dropdown.configure(
                values=[],
                variable=customtkinter.StringVar(master=self, value=self.__widgets_text['no_supported_log_found'])
            )
        if self.log_type_dropdown.get() == select_log_type:
            self.log_type_dropdown.configure(
                variable=customtkinter.StringVar(master=self, value=self.__widgets_text['select_log_type'])
            )
        if type(self.tab_view) == customtkinter.CTkLabel:
            self.tab_view.configure(text=self.__widgets_text['No_Data'])

    def on_closing(self):
        self.withdraw()

    def destroy_tab_view(self, make_label: bool = False):
        if self.tab_view:
            self.tab_view.destroy()
            self.tab_view = None
        if make_label:
            self.tab_view = customtkinter.CTkLabel(
                master=self.tab_view_frame,
                text=self.__widgets_text['No_Data']
            )
            self.tab_view.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

    def teb_view_place_holder_message(self, teb_view_message_text: str, is_error: bool = False):
        self.destroy_tab_view()
        if is_error:
            self.tab_view = customtkinter.CTkLabel(
                master=self.tab_view_frame,
                text=teb_view_message_text,
                text_color='red',
                font=('', 15, 'bold'),
                width=250
            )
        else:
            self.tab_view = customtkinter.CTkLabel(
                master=self.tab_view_frame,
                text=teb_view_message_text
            )
        self.tab_view.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

    def load_handler_and_file_list(self, log_handler_name: str, log_handler_obj, parsed_file_dict: dict):
        self.destroy_tab_view(make_label=True)
        if type(parsed_file_dict) is dict:
            if log_handler_name not in self.__parsed_file_dict.keys():
                self.__parsed_file_dict[log_handler_name] = {
                    'log_handler_object': log_handler_obj,
                    'file_list': parsed_file_dict
                }
            else:
                for file_name in parsed_file_dict.keys():
                    if self.selected_log_file == file_name:
                        self.selected_log_file = None
                    self.__parsed_file_dict[log_handler_name]['file_list'][file_name] = parsed_file_dict[file_name]
            self.log_type_dropdown.configure(
                values=[log_handler for log_handler in self.__parsed_file_dict.keys()],
                variable=customtkinter.StringVar(master=self, value=log_handler_name)
            )
            self.log_type_selection()
            self.update()

    def log_type_selection(self, *args):
        self.log_file_list_box.add_items_list([])
        self.log_file_list_box.disable()
        self.selected_log_file = None
        self.teb_view_place_holder_message(self.__widgets_text['No_Data'])
        self.__selected_log_type = self.log_type_dropdown.get()
        if (self.__selected_log_type != self.__widgets_text['select_log_type']
                or self.__selected_log_type != self.__widgets_text['no_supported_log_found']):
            self.log_file_list_box.enable()
            self.log_file_list_box.add_items_list(
                [file_name for file_name in self.__parsed_file_dict[self.__selected_log_type]['file_list'].keys()]
            )

    def plot_selected_logs_file(self, event=None):
        selected_log = self.log_file_list_box.get_selected()

        if len(selected_log) > 0:
            if self.selected_log_file != selected_log[0]:
                self.log_file_list_box.disable()
                self.log_type_dropdown.configure(state=customtkinter.DISABLED)
                self.selected_log_file = selected_log[0]
                logging.info(f'===Plotting {self.selected_log_file} Logs=== START:')
                self.destroy_tab_view()

                running_progress_bar_frame = customtkinter.CTkFrame(
                    master=self.tab_view_frame, width=200, height=100
                )
                running_progress_bar_frame.grid(row=0, column=0, padx=15, pady=0)

                running_progress_bar_label = customtkinter.CTkLabel(
                    master=running_progress_bar_frame,
                    text=self.__widgets_text['Plotting']
                )
                running_progress_bar_label.grid(row=0, column=0, padx=0, pady=(0, 0))

                running_progress_bar = customtkinter.CTkProgressBar(
                    master=running_progress_bar_frame, width=200
                )
                running_progress_bar.grid(row=1, column=0, padx=0, pady=(0, 0))
                running_progress_bar.start()

                def gui_callback(datatable):
                    running_progress_bar.stop()
                    running_progress_bar_frame.destroy()

                    if datatable is None or type(datatable) is str:
                        self.teb_view_place_holder_message(
                            teb_view_message_text=self.__widgets_text['plotting_error_message'],
                            is_error=True
                        )
                        raise NlhException(f'Failed to upload result file {self.selected_log_file}')
                    elif isinstance(datatable, BaseException):
                        self.teb_view_place_holder_message(
                            teb_view_message_text=self.__widgets_text['plotting_error_message'],
                            is_error=True
                        )
                        raise NlhException(f'Failed to upload result file {self.selected_log_file}') from datatable
                    else:
                        self.tab_view = PlotTab(
                            master=self.tab_view_frame,
                            selected_log=self.selected_log_file,
                            plotting_error_msgs=self.__widgets_text['plotting_error_message'],
                            log_handler_obj=self.__parsed_file_dict[self.__selected_log_type]['log_handler_object'],
                            datatable=datatable
                        )
                        self.tab_view.grid(row=0, column=0, padx=1, pady=1, sticky='nsew')

                    logging.info(f'===Plotting {self.selected_log_file} Logs=== END:')
                    self.log_file_list_box.enable()
                    self.log_type_dropdown.configure(state=customtkinter.NORMAL)

                try:
                    thread_runner(
                        self,
                        self.__parsed_file_dict[self.__selected_log_type]['log_handler_object'].load_data_table,
                        gui_callback,
                        args=(self.__parsed_file_dict[self.__selected_log_type]['file_list'][self.selected_log_file],)
                    )
                except Exception as e:
                    if running_progress_bar_frame:
                        running_progress_bar_frame.destroy()
                    elif self.tab_view:
                        self.destroy_tab_view()
                    self.log_file_list_box.enable()
                    self.log_type_dropdown.configure(state=customtkinter.NORMAL)
                    global_exception_handler(
                        type(e), e, e.__traceback__,
                        error_message=self.__widgets_text['plotting_error_message'],
                        root=self
                    )
                    return

        self.log_file_list_box.enable()

    def open_log_in_jmp(self):
        selected_log = self.log_file_list_box.get_selected()
        self.log_file_list_box.disable()
        self.log_type_dropdown.configure(state=customtkinter.DISABLED)

        if selected_log:
            jmp_base_path = r"C:\Program Files\SAS\JMP"
            selected_log = self.log_file_list_box.get_selected()
            self.log_file_list_box.disable()
            self.log_type_dropdown.configure(state=customtkinter.DISABLED)
            try:
                if not selected_log:
                    self.log_file_list_box.enable()
                    return

                file_path = self.__parsed_file_dict[self.__selected_log_type]['file_list'][selected_log[0]]

                if not os.path.isfile(file_path):
                    self.log_file_list_box.enable()
                    raise NlhException("Error", f"The file {file_path} does not exist.")

                jmp_versions = [int(name) for name in os.listdir(jmp_base_path) if name.isdigit()]
                highest_jmp_version = str(max(jmp_versions)) if jmp_versions else None
                jmp_exe = (
                    os.path.join(jmp_base_path, highest_jmp_version, 'jmp.exe')
                    if highest_jmp_version else None
                )

                if jmp_exe and os.path.exists(jmp_exe):
                    subprocess.Popen([jmp_exe, f"{file_path}"])
                else:
                    raise NlhException("No valid JMP executable found.")
            except Exception as e:
                raise NlhException('Open JMP Error', str(e)) from e

        self.log_file_list_box.enable()
        self.log_type_dropdown.configure(state=customtkinter.NORMAL)

    def open_log_in_excel(self):
        selected_log = self.log_file_list_box.get_selected()
        self.log_file_list_box.disable()
        self.log_type_dropdown.configure(state=customtkinter.DISABLED)

        if not selected_log:
            self.log_file_list_box.enable()
            return

        file_path = self.__parsed_file_dict[self.__selected_log_type]['file_list'][selected_log[0]]

        if not os.path.isfile(file_path):
            self.log_file_list_box.enable()
            raise NlhException("Error", f"The file {file_path} does not exist.")

        try:
            subprocess.Popen(f'start EXCEL.EXE "{file_path}"', shell=True)
            logging.info(f"Opened {file_path} in Excel.")
        except Exception as e:
            raise NlhException("Error", f"Failed to open the file in Excel: {e}") from e
        finally:
            self.log_file_list_box.enable()
            self.log_type_dropdown.configure(state=customtkinter.NORMAL)

    def capture_to_clipboard(self, frame):
        frame.update_idletasks()
        x = self.winfo_rootx() + frame.winfo_x()
        y = self.winfo_rooty() + frame.winfo_y()
        x1 = x + frame.winfo_width()
        y1 = y + frame.winfo_height()

        im = ImageGrab.grab(bbox=(x, y, x1, y1))

        output = BytesIO()
        im.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()