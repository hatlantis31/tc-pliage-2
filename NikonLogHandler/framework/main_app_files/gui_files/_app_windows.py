"""
Main up window for the Nikon Log Handler application.
"""
import logging
import os
import sys
import customtkinter
import json

from pandas import DataFrame, concat
from PIL import Image
from tkinter import PhotoImage
from main_app_files.core_script_files.discovery import discovery
from main_app_files.function_files._threading_handler import stop_all_threads
from main_app_files.function_files._nlh_xml_handler import NlhXmlHandler
from main_app_files.function_files.exception_handler_and_reporting import global_exception_handler
from main_app_files.gui_files._main_menu_frame import MainMenuFrame
from main_app_files.gui_files._information_frame import InformationFrame
from main_app_files.gui_files._analysis_frame import AnalysisFrame
from main_app_files.gui_files._tools_frames import ToolsFrame
from main_app_files.gui_files._loading_window import LoadingWindow

customtkinter.set_appearance_mode('Dark')
customtkinter.set_default_color_theme('blue')


class MainWindow(customtkinter.CTk):
    """
    Main window for the log Handler app
    """

    def __init__(self, nlh_xml_obj: NlhXmlHandler):
        super().__init__()

        self.report_callback_exception = self._report_callback_exception

        # ===================================
        # ============ Variables ============
        # ===================================
        self.languages = {}
        self.run_stats = None
        self.mode = 'Dark'
        self.test = None
        self.index = 0
        self.nlh_xml_obj = nlh_xml_obj
        self.current_language = self.nlh_xml_obj.default_language
        self.load_languages()
        self.language_options = ['English', 'japanese']
        self.image_folder = os.path.abspath(os.curdir) + '\\image_files\\'
        app_main_menu_logo = {
            "light_mode": Image.open(self.image_folder + 'app_images\\NikonLogHandler_icon_no_back_light_mode.png'),
            "dark_mode": Image.open(self.image_folder + 'app_images\\NikonLogHandler_icon_no_back_dark_mode.png')
        }
        pdf_logo = Image.open(self.image_folder + 'app_images\\pdf_logo.png')
        graph_logo = Image.open(self.image_folder + 'app_images\\graph_logo.png')
        excel_logo = Image.open(self.image_folder + 'app_images\\excel_logo.png')
        jmp_logo = Image.open(self.image_folder + 'app_images\\jmp_Logo.png')
        copy_graph = Image.open(self.image_folder + 'app_images\\copy_graph.png')

        # Discovery has not run yet; start with an empty dict.
        # refresh_from_discovery() (called via LoadingWindow) will populate it.
        self.log_handlers_dict = discovery.log_handlers_dict

        self.doc_location = 'https://nikonglobaleu.sharepoint.com/sites/NPE-ESHardware/Nikon%20Log%20Handler/Handlers_doc/'
        self.selected_log_type = 'Nikon Log Handler'
        self.sharepoint_handler = None

        # ===================================
        # ============    GUI    ============
        # ===================================

        WIDTH = 1000
        HEIGHT = 550
        self.title(
            f'{self.nlh_xml_obj.title} {self.nlh_xml_obj.full_app_version} '
            f'{self.languages[self.current_language]["nikon_confidential"]}'
        )
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.minsize(WIDTH, HEIGHT)
        app_icon = PhotoImage(file=self.image_folder + 'app_images\\nikon_icon.png')
        self.iconphoto(False, app_icon)

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.menu_bar = MainMenuFrame(
            master=self,
            app_logo=app_main_menu_logo,
            widgets_text={
                'update_option': self.languages[self.current_language]['update_option'],
                'help_menu': self.languages[self.current_language]['help_menu'],
                "login_button": self.languages[self.current_language]['login_button'],
                "login_required_message": self.languages[self.current_language]['login_required_message'],
                "update_option_login_required": self.languages[self.current_language]['update_option_login_required'],
                'nlh_sharepoint_option': self.languages[self.current_language]['nlh_sharepoint_option'],
                'report_issue_option': self.languages[self.current_language]['report_issue_option'],
                'send_a_request_option': self.languages[self.current_language]['send_a_request_option'],
                'load_scripts_option': self.languages[self.current_language]['load_scripts_option'],  # ← NEW
                'title_update_window': self.languages[self.current_language]['title_update_window'],
                "__participate_in_testing_button": self.languages[self.current_language]["__participate_in_testing_button"],
                "close_button": self.languages[self.current_language]["close_button"],
                "check_update_button": self.languages[self.current_language]["check_update_button"],
                "checking_for_update_status": self.languages[self.current_language]["checking_for_update_status"],
                "new_version_available_status": self.languages[self.current_language]["new_version_available_status"],
                "press_update_status": self.languages[self.current_language]["press_update_status"],
                "latest_version_status": self.languages[self.current_language]["latest_version_status"],
                "press_check_update_status": self.languages[self.current_language]["press_check_update_status"],
                "updating_status": self.languages[self.current_language]["updating_status"],
                "error_downloading_updates": self.languages[self.current_language]["error_downloading_updates"],
                'password': self.languages[self.current_language]['password'],
                'ok_button': self.languages[self.current_language]['ok_button'],
                'cancel_button': self.languages[self.current_language]['cancel_button'],
                'title_user_credentials': self.languages[self.current_language]['title_user_credentials'],
            },
            language_options=self.language_options,
            current_language=self.current_language,
            nlh_xml=self.nlh_xml_obj,
            main_window_control_commend={
                'withdraw': self.withdraw,
                'deiconify': self.deiconify,
                'on_closing': self.on_closing
            },
            change_language_commend=self.change_language,
            mode=self.mode
        )
        self.menu_bar.grid(row=0, column=0, sticky='nsew', padx=5, pady=(5, 0), columnspan=2)

        self.log_analysis_main_frame = customtkinter.CTkFrame(master=self)
        self.log_analysis_main_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.log_analysis_main_frame.grid_propagate(False)
        self.log_analysis_main_frame.columnconfigure(0, weight=1, minsize=int(WIDTH * 0.3))
        self.log_analysis_main_frame.columnconfigure(1, weight=2)
        self.log_analysis_main_frame.rowconfigure(0, weight=0)
        self.log_analysis_main_frame.rowconfigure(1, weight=1)

        self.log_analysis_label = customtkinter.CTkLabel(
            master=self.log_analysis_main_frame,
            text=self.languages[self.current_language]['log_analysis_label'],
            font=('Roboto Medium', 16, "underline"),
            height=11
        )
        self.log_analysis_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=0, pady=0)

        self.information_frame = InformationFrame(
            master=self.log_analysis_main_frame,
            pdf_logo=pdf_logo,
            fg_color="transparent",
            widgets_text={
                'available_handler_table_button': self.languages[self.current_language]['available_handler_table_button'],
                'description_label': self.languages[self.current_language]['description_label'],
                'group_dropdown_label': self.languages[self.current_language]['group_dropdown_label'],
                'handle_info_dropdown_label': self.languages[self.current_language]['handle_info_dropdown_label']
            },
            information_param=self.create_handler_information_param(
                description_text=self.languages[self.current_language]['description_text'],
                general_description_text=self.languages[self.current_language]['general_description_text']
            )
        )
        self.information_frame.grid(row=1, column=0, sticky='nsew', padx=0, pady=0)
        self.information_frame.grid_propagate(False)

        self.analysis_frame = AnalysisFrame(
            master=self.log_analysis_main_frame,
            graph_logo=graph_logo,
            app_logo=app_main_menu_logo,
            jmp_logo=jmp_logo,
            excel_logo=excel_logo,
            copy_graph=copy_graph,
            fg_color="transparent",
            widgets_text={
                'open_folder': self.languages[self.current_language]['open_folder'],
                'no_folder_selected': self.languages[self.current_language]['no_folder_selected'],
                'no_supported_log_found': self.languages[self.current_language]['no_supported_log_found'],
                'no_log_selected': self.languages[self.current_language]['no_log_selected'],
                '__log_file_list': self.languages[self.current_language]['__log_file_list'],
                'select_log_type': self.languages[self.current_language]['select_log_type'],
                'run_button': self.languages[self.current_language]['run_button'],
                'running': self.languages[self.current_language]['running'],
                'done': self.languages[self.current_language]['done'],
                'error': self.languages[self.current_language]['error'],
                'plotting_end': self.languages[self.current_language]['plotting_end'],
                'plotting_start': self.languages[self.current_language]['plotting_start'],
                'error_message': self.languages[self.current_language]['error_message'],
                'error_while_parsing': self.languages[self.current_language]['error_while_parsing'],
                'error_while_saving': self.languages[self.current_language]['error_while_saving'],
                'No_Data': self.languages[self.current_language]['No_Data'],
                'Plotting': self.languages[self.current_language]['Plotting'],
                'plotting_error_message': self.languages[self.current_language]['plotting_error_message'],
                'open_plot_window_tooltip': self.languages[self.current_language]['open_plot_window_tooltip'],
                'open_jmp_tooltip': self.languages[self.current_language]['open_jmp_tooltip'],
                'open_excel_tooltip': self.languages[self.current_language]['open_excel_tooltip'],
                'copy_graph_to_clipboard': self.languages[self.current_language]['copy_graph_to_clipboard']
            },
            set_description=self.information_frame.set_dropdown_value
        )
        self.analysis_frame.grid(row=1, column=1, sticky='nsew', padx=0, pady=0)
        self.analysis_frame.grid_propagate(False)

        self.tool_main_frame = customtkinter.CTkFrame(master=self, width=int(WIDTH * 0.15))
        self.tool_main_frame.grid(row=1, column=1, sticky='nsew', padx=(0, 5), pady=5)

        self.tool_main_frame.columnconfigure((0, 2), weight=0)
        self.tool_main_frame.columnconfigure(1, weight=1)

        self.tool_label = customtkinter.CTkLabel(
            master=self.tool_main_frame,
            text=self.languages[self.current_language]['tools_label'],
            font=('Roboto Medium', 16, "underline"),
            height=11
        )
        self.tool_label.grid(row=0, column=1, sticky='ew', padx=5, pady=0)

        self.tools_frame = ToolsFrame(
            master=self.tool_main_frame,
            app_logo=app_main_menu_logo,
            fg_color="transparent",
            widgets_text={},
            set_description=self.information_frame.set_dropdown_value
        )
        self.tools_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        # Open the LoadingWindow on startup.
        # SharePoint init happens AFTER the loading window closes
        # via __on_loading_complete → menu_bar.initialize_sharepoint_connection().
        self.after(0, self.__open_loading_window)

    # ===================================
    # ============ functions ============
    # ===================================

    def _report_callback_exception(self, exc, val, tb):
        global_exception_handler(exc, val, tb, root=self)

    def on_closing(self, event=0):
        self.destroy()
        stop_all_threads()
        sys.exit(0)

    def load_languages(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        language_file = os.path.join(script_dir, '../../languages.json')
        with open(language_file, encoding='utf8') as file:
            self.languages = json.load(file)

    # ===================================
    # == Loading Window helpers =========
    # ===================================

    def __open_loading_window(self):
        """
        Open the LoadingWindow immediately after the main window is drawn.
        Called automatically on startup via self.after(0, ...).

        The LoadingWindow will:
          - Hide this window (withdraw)
          - Run discovery.discover() on a background thread
          - Show progress and result messages
          - Call __on_loading_complete when the user clicks OK
          - Restore this window (deiconify)

        SharePoint connection is NOT started here — it is started only
        inside __on_loading_complete, after this window fully closes.
        """
        LoadingWindow(
            master=self,
            main_window_control_commend={
                'withdraw': self.withdraw,
                'deiconify': self.deiconify,
            },
            on_load_complete=self.__on_loading_complete,
            widgets_text=self.languages[self.current_language].get('loading_window'),
        )

    def open_loading_window(self):
        """
        Public method called by MainMenuFrame when the user selects
        'Load Script and Tools' from the help dropdown.

        Re-runs discovery and refreshes the GUI.
        SharePoint connection is intentionally NOT touched here — it was
        already established (or skipped) during startup and must not be
        re-triggered by this action.
        """
        LoadingWindow(
            master=self,
            main_window_control_commend={
                'withdraw': self.withdraw,
                'deiconify': self.deiconify,
            },
            # On OK: only refresh handlers/tools, no SharePoint work.
            on_load_complete=self.__on_loading_complete_no_sharepoint,
            widgets_text=self.languages[self.current_language].get('loading_window'),
        )

    def __on_loading_complete(self):
        """
        Called by LoadingWindow (startup path) after the user clicks OK.

        Two things happen here, in order:
          1. Refresh handlers/tools from the discovery results.
          2. Start the SharePoint connection for the first (and only) time.

        initialize_sharepoint_connection() is called here — and only here —
        so it is guaranteed to run after the LoadingWindow has fully closed.
        """
        self.refresh_from_discovery()
        # ── Start SharePoint ONLY after the loading window is gone ──────────
        self.menu_bar.initialize_sharepoint_connection()
        # ────────────────────────────────────────────────────────────────────

    def __on_loading_complete_no_sharepoint(self):
        """
        Called by LoadingWindow when opened from the help dropdown
        ('Load Script and Tools').

        Only refreshes handlers/tools from the new discovery results.
        The SharePoint session is left completely untouched.
        """
        self.refresh_from_discovery()

    # ===================================
    # ============ Language =============
    # ===================================

    def change_language(self, language):
        self.current_language = language
        self.nlh_xml_obj.change_default_language(default_language=language)
        self.menu_bar.change_buttons_text(widgets_text={
            'update_option': self.languages[self.current_language]['update_option'],
            'help_menu': self.languages[self.current_language]['help_menu'],
            "login_button": self.languages[self.current_language]['login_button'],
            "login_required_message": self.languages[self.current_language]['login_required_message'],
            "update_option_login_required": self.languages[self.current_language]['update_option_login_required'],
            'nlh_sharepoint_option': self.languages[self.current_language]['nlh_sharepoint_option'],
            'report_issue_option': self.languages[self.current_language]['report_issue_option'],
            'send_a_request_option': self.languages[self.current_language]['send_a_request_option'],
            'load_scripts_option': self.languages[self.current_language]['load_scripts_option'],  # ← NEW
            'title_update_window': self.languages[self.current_language]['title_update_window'],
            "__participate_in_testing_button": self.languages[self.current_language]["__participate_in_testing_button"],
            "close_button": self.languages[self.current_language]["close_button"],
            "check_update_button": self.languages[self.current_language]["check_update_button"],
            "checking_for_update_status": self.languages[self.current_language]["checking_for_update_status"],
            "new_version_available_status": self.languages[self.current_language]["new_version_available_status"],
            "press_update_status": self.languages[self.current_language]["press_update_status"],
            "latest_version_status": self.languages[self.current_language]["latest_version_status"],
            "press_check_update_status": self.languages[self.current_language]["press_check_update_status"],
            "updating_status": self.languages[self.current_language]["updating_status"],
            "error_downloading_updates": self.languages[self.current_language]["error_downloading_updates"],
            'ok_button': self.languages[self.current_language]['ok_button'],
            'cancel_button': self.languages[self.current_language]['cancel_button'],
            'title_user_credentials': self.languages[self.current_language]['title_user_credentials'],
            'version_available': self.languages[self.current_language]['version_available'],
            'new': self.languages[self.current_language]['new']
        })
        self.information_frame.change_buttons_text_and_information_param(
            widgets_text={
                'available_handler_table_button': self.languages[self.current_language]['available_handler_table_button'],
                'description_label': self.languages[self.current_language]['description_label'],
                'group_dropdown_label': self.languages[self.current_language]['group_dropdown_label'],
                'handle_info_dropdown_label': self.languages[self.current_language]['handle_info_dropdown_label']
            },
            information_param=self.create_handler_information_param(
                description_text=self.languages[self.current_language]['description_text'],
                general_description_text=self.languages[self.current_language]['general_description_text']
            ),
            current_handler=self.selected_log_type
        )
        self.analysis_frame.change_buttons_text_and_information_param(widgets_text={
            'open_folder': self.languages[self.current_language]['open_folder'],
            'no_folder_selected': self.languages[self.current_language]['no_folder_selected'],
            'no_supported_log_found': self.languages[self.current_language]['no_supported_log_found'],
            'no_log_selected': self.languages[self.current_language]['no_log_selected'],
            '__log_file_list': self.languages[self.current_language]['__log_file_list'],
            'select_log_type': self.languages[self.current_language]['select_log_type'],
            'run_button': self.languages[self.current_language]['run_button'],
            'running': self.languages[self.current_language]['running'],
            'done': self.languages[self.current_language]['done'],
            'error': self.languages[self.current_language]['error'],
            'plotting_end': self.languages[self.current_language]['plotting_end'],
            'plotting_start': self.languages[self.current_language]['plotting_start'],
            'error_message': self.languages[self.current_language]['error_message'],
            'error_while_parsing': self.languages[self.current_language]['error_while_parsing'],
            'error_while_saving': self.languages[self.current_language]['error_while_saving'],
            'No_Data': self.languages[self.current_language]['No_Data'],
            'Plotting': self.languages[self.current_language]['Plotting'],
            'plotting_error_message': self.languages[self.current_language]['plotting_error_message'],
            'open_plot_window_tooltip': self.languages[self.current_language]['open_plot_window_tooltip'],
            'open_jmp_tooltip': self.languages[self.current_language]['open_jmp_tooltip'],
            'open_excel_tooltip': self.languages[self.current_language]['open_excel_tooltip'],
            'copy_graph_to_clipboard': self.languages[self.current_language]['copy_graph_to_clipboard']
        })
        self.title(
            f'{self.nlh_xml_obj.title} {self.nlh_xml_obj.full_app_version} '
            f'{self.languages[self.current_language]["nikon_confidential"]}'
        )
        self.log_analysis_label.configure(text=self.languages[self.current_language]['log_analysis_label'])
        self.tool_label.configure(text=self.languages[self.current_language]['tools_label'])

    # ===================================
    # ======== Handler Information ======
    # ===================================

    def create_handler_information_param(self, description_text: list, general_description_text: list):
        new_line = '\n'
        description_dict = {}
        log_handlers_information_table = None

        Log_handlers_names_list = [
            handler_info.log_handler_name
            for handler_info_list in self.log_handlers_dict.values()
            for handler_info in handler_info_list
        ]

        groups_set = set()
        for handler_info_list in self.log_handlers_dict.values():
            for handler_info in handler_info_list:
                groups_set.add(handler_info.log_handler_group)
        groups_list = ["All Log Handler Types"] + sorted(list(groups_set))

        handler_to_group = {}
        for handler_info_list in self.log_handlers_dict.values():
            for handler_info in handler_info_list:
                handler_to_group[handler_info.log_handler_name] = handler_info.log_handler_group

        for handler, handler_info_list in self.log_handlers_dict.items():
            for handler_info in handler_info_list:
                description_dict[handler_info.log_handler_name] = {
                    'description': (
                        f'{description_text[0]}:\n'
                        f'{handler_info.log_handler_description_str}\n\n'
                        f'{description_text[7]}:\n'
                        f'{handler_info.version}\n\n'
                        f'{description_text[1]}:\n'
                        f'{"".join(f"• {x}{new_line}" for x in handler_info.log_supported_machine_types_list)}\n'
                        f'{description_text[2]}\n'
                        f'{"".join(f"• {x}{new_line}" for x in handler_info.log_supported_logs_list)}\n'
                        f'{description_text[3]}\n'
                        f'{"".join(f"• {x}{new_line}" for x in handler_info.logs_locations_list)}\n'
                        f'{description_text[4]}\n'
                        f'{handler_info.log_analysis_option_str}\n'
                        f'{description_text[5]}\n'
                        f'{description_text[6]} "_{handler_info.log_parsed_file_inductor_str}.'
                        f'{"xlsx" if handler_info.log_handler_save_method_str == "excel" else "csv"}"'
                    ),
                    'pdf link': f'{self.doc_location}{handler_info.log_handler_class}.pdf'
                }

                if type(log_handlers_information_table) is not DataFrame:
                    log_handlers_information_table = DataFrame(
                        handler_info.log_handler_information_dict, index=[1, ]
                    )
                else:
                    log_handlers_information_table = concat([
                        log_handlers_information_table,
                        DataFrame(handler_info.log_handler_information_dict, index=[1, ])
                    ])

        description_dict['Nikon Log Handler'] = {
            'pdf link': f'{self.doc_location}NikonLogHandler.pdf',
            'description': (
                f'{general_description_text[0]}\n'
                f'• {general_description_text[1]}\n\n'
                f'• {general_description_text[2]}\n\n'
                f'• {general_description_text[3]} \n\n'
            )
        }

        handler_to_group['Nikon Log Handler'] = "All Log Handler Types"
        Log_handlers_names_list.insert(0, 'Nikon Log Handler')

        return {
            'description_dict': description_dict,
            'Log_handlers_names_list': Log_handlers_names_list,
            'log_handlers_information_table': log_handlers_information_table,
            'groups_list': groups_list,
            'handler_to_group': handler_to_group
        }

    # ===================================
    # ======== SharePoint / Tools =======
    # ===================================

    def update_tools_sharepoint_handler(self):
        if hasattr(self, 'tools_frame'):
            self.tools_frame.set_sharepoint_handler(self.sharepoint_handler)

    # ===================================
    # ======== Discovery / Refresh ======
    # ===================================

    def refresh_from_discovery(self):
        """
        Pull already-discovered data from the discovery singleton into the GUI.

        IMPORTANT: This method does NOT call discovery.discover() itself.
        Discovery is run inside LoadingWindow on a background thread.
        This method is called only after the user clicks OK on the
        LoadingWindow, meaning discovery has already completed.

        Call sites:
          - __on_loading_complete             (startup loading window OK)
          - __on_loading_complete_no_sharepoint (dropdown loading window OK)
        """
        # Log what was found (discovery already ran)
        if discovery.load_errors:
            for filename, exc in discovery.load_errors:
                logging.error(f"Plugin load error in '{filename}': {exc}")

        logging.info(
            f"Discovery results pulled into GUI: "
            f"{len(discovery.handler_classes_dict)} handler(s), "
            f"{len(discovery.tools_list)} tool(s)."
        )

        # ── 1. Sync local reference ──────────────────────────────────────────
        self.log_handlers_dict = discovery.log_handlers_dict

        # ── 2. Refresh analysis frame handler dropdown ───────────────────────
        self.analysis_frame.reload_handlers()

        # ── 3. Refresh tools frame tool buttons ─────────────────────────────
        self.tools_frame.reload_tools()

        # ── 4. Refresh information frame with updated handler data ───────────
        self.information_frame.change_buttons_text_and_information_param(
            widgets_text={
                'available_handler_table_button': self.languages[self.current_language]['available_handler_table_button'],
                'description_label': self.languages[self.current_language]['description_label'],
                'group_dropdown_label': self.languages[self.current_language]['group_dropdown_label'],
                'handle_info_dropdown_label': self.languages[self.current_language]['handle_info_dropdown_label']
            },
            information_param=self.create_handler_information_param(
                description_text=self.languages[self.current_language]['description_text'],
                general_description_text=self.languages[self.current_language]['general_description_text']
            ),
            current_handler='Nikon Log Handler'
        )