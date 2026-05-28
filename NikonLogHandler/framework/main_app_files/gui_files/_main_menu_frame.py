"""
This module defines the MainMenuFrame class, which is a customtkinter frame for the main menu of an application.
It includes buttons for updating, accessing help, changing language, and other general functionalities.
The class handles the creation and management of various GUI elements and their associated actions.
"""

import customtkinter
import webbrowser

from tkinter import StringVar
from main_app_files.function_files._nlh_xml_handler import NlhXmlHandler
from main_app_files.function_files.exception_handler_and_reporting import send_bug_report, send_request
from main_app_files.function_files._threading_handler import thread_runner
from main_app_files.gui_files._update_window import UpdateWindow


class MainMenuFrame(customtkinter.CTkFrame):
    def __init__(self, master, app_logo: dict, widgets_text: dict, language_options: list, current_language: str,
                 nlh_xml: NlhXmlHandler, main_window_control_commend: dict, change_language_commend: callable = None,
                 mode='Dark'):
        """
        This is main menu bar, location for all the General buttons (Update, Help and Nikon Icon)
        """
        super().__init__(master)

        # ===================================
        # =========   Parameters    =========
        # ===================================
        self._is_logging_in = None
        self.__app_logo = app_logo
        self.__widgets_text = widgets_text
        self.__mode = mode
        self.__update_window = None
        self.__nlh_xml = nlh_xml
        self.__is_update_available = False
        self.__new_version_param = None
        self.__label_and_text = None
        self.__main_window_control_commend = main_window_control_commend
        self.update_status = False
        self.master = master

        # ===================================
        # ============    GUI    ============
        # ===================================

        # ============ GUI grid config ============
        self.columnconfigure(0, weight=0)  # Nikon icon width don't expend
        self.columnconfigure(1, weight=0)  # language CTkComboBox don't expend
        self.columnconfigure(2, weight=0)  # help menu don't expend
        self.columnconfigure(3, weight=1)  # expending space to keep button at good location
        self.columnconfigure(4, weight=0)  # login button don't expend

        # ============ Nikon Icon Widget ============
        self.__nikon_icon_label = None
        self.__load_nlh_app_logo()

        # ============ language Button Widget ============
        self.__language_var = customtkinter.StringVar(value=current_language)
        self.__Language_menu = customtkinter.CTkOptionMenu(self,
                                                           width=120,
                                                           values=language_options,
                                                           command=change_language_commend,
                                                           variable=self.__language_var)
        self.__Language_menu.grid(row=0, column=1, sticky='ew', padx=(10, 10), pady=5)

        # ============  Help Menu Widget ============
        # NOTE: 'load_scripts_option' is added here; it opens the LoadingWindow
        # but does NOT trigger initialize_sharepoint_connection().
        help_options = [
            self.__widgets_text['update_option'],
            self.__widgets_text['nlh_sharepoint_option'],
            self.__widgets_text['report_issue_option'],
            self.__widgets_text['send_a_request_option'],
            self.__widgets_text['load_scripts_option'],   # ← NEW
        ]
        self.__help_dropdown = customtkinter.CTkOptionMenu(master=self,
                                                           width=90,
                                                           values=help_options,
                                                           variable=StringVar(value=self.__widgets_text['help_menu']),
                                                           command=self.__handle_help_option)
        self.__help_dropdown.grid(row=0, column=2, padx=(10, 10), pady=5)

        # ============ Update Status Label Widget ============
        self.__status_label = customtkinter.CTkLabel(master=self, text='')
        self.__status_label.grid(row=0, column=3, sticky='ew', padx=(10, 10), pady=5)

        # ============ Login Button Widget ============
        self.__login_button = customtkinter.CTkButton(master=self, text=self.__widgets_text['login_button'][0],
                                                      width=80, height=20, command=self.__handle_login_button)
        self.__login_button.grid(row=0, column=4, sticky='nsew', padx=(10, 10), pady=10)

        # ── initialize_sharepoint_connection() is intentionally NOT called
        # here.  It is called by MainWindow.__on_loading_complete() so that
        # it only starts after the LoadingWindow has fully closed on startup.

    # ===================================
    # ============ Functions ============
    # ===================================

    def change_buttons_text(self, widgets_text: dict):
        """
        Change the button text.
        """
        self.__widgets_text = widgets_text
        self.__help_dropdown.set(self.__widgets_text['help_menu'])
        self.__help_dropdown.configure(values=[
            self.__widgets_text['update_option'],
            self.__widgets_text['load_scripts_option'],
            self.__widgets_text['nlh_sharepoint_option'],
            self.__widgets_text['report_issue_option'],
            self.__widgets_text['send_a_request_option'],
        ])

        # Update login button text based on current state
        self.__update_login_button_state()

    def __update_login_button_state(self):
        """
        Update login button text and state based on SharePoint authentication status.
        """
        if self.master.sharepoint_handler and self.master.sharepoint_handler.is_authenticated:
            # Logged in state
            self.__login_button.configure(text=self.__widgets_text['login_button'][1], state="disabled")
        elif hasattr(self, '_is_logging_in') and self._is_logging_in:
            # Logging in state
            self.__login_button.configure(text=self.__widgets_text['login_button'][2], state="disabled")
        else:
            # Not logged in state
            self.__login_button.configure(text=self.__widgets_text['login_button'][0], state="normal")

    def __handle_help_option(self, option):
        """
        Handle the selected option from the help menu.
        """
        if option == self.__widgets_text['update_option']:
            # Check if SharePoint is authenticated before allowing update option
            if not self.master.sharepoint_handler or not self.master.sharepoint_handler.is_authenticated:
                self.change_update_menu_status_text(
                    new_text="Please login to SharePoint to check for updates",
                    color='orange'
                )
                self.__help_dropdown.set(self.__widgets_text['help_menu'])
                return

            if self.update_status:
                self.__open_update_window()
            self.__help_dropdown.set(self.__widgets_text['help_menu'])

        elif option == self.__widgets_text['nlh_sharepoint_option']:
            self.__open_nlh_SharePoint()
            self.__help_dropdown.set(self.__widgets_text['help_menu'])

        elif option == self.__widgets_text['report_issue_option']:
            send_bug_report()
            self.__help_dropdown.set(self.__widgets_text['help_menu'])

        elif option == self.__widgets_text['send_a_request_option']:
            send_request()
            self.__help_dropdown.set(self.__widgets_text['help_menu'])

        elif option == self.__widgets_text['load_scripts_option']:
            # ── NEW ──────────────────────────────────────────────────────────
            # Open the LoadingWindow to re-run discovery.
            # initialize_sharepoint_connection() must NOT be called here —
            # the SharePoint session is already established (or the user
            # deliberately skipped it).  We only refresh scripts/tools.
            self.__help_dropdown.set(self.__widgets_text['help_menu'])
            self.master.open_loading_window()          # delegated to MainWindow
            # ─────────────────────────────────────────────────────────────────

    def __handle_login_button(self):
        """
        Handle login button click.
        """
        if self.master.sharepoint_handler and self.master.sharepoint_handler.is_authenticated:
            # Already logged in, do nothing
            return
        else:
            # Try to log in
            self.retry_sharepoint_login()

    def __load_nlh_app_logo(self):
        if self.__mode == 'Dark':
            self.__nikon_icon = customtkinter.CTkImage(self.__app_logo["dark_mode"], size=(80, 40))
            if self.__nikon_icon_label:
                self.__nikon_icon_label.destroy()
            self.__nikon_icon_label = customtkinter.CTkButton(
                master=self, text='', image=self.__nikon_icon, width=30, height=30,
                fg_color='transparent', hover_color=self._fg_color,
                command=self.__change_appearance_mode_event
            )
            self.__nikon_icon_label.grid(row=0, column=0, sticky='nsew', pady=0, padx=(5, 0))
        else:
            self.__nikon_icon = customtkinter.CTkImage(self.__app_logo["light_mode"], size=(80, 40))
            if self.__nikon_icon_label:
                self.__nikon_icon_label.destroy()
            self.__nikon_icon_label = customtkinter.CTkButton(
                master=self, text='', image=self.__nikon_icon, width=30, height=30,
                fg_color='transparent', hover_color=self._fg_color,
                command=self.__change_appearance_mode_event
            )
            self.__nikon_icon_label.grid(row=0, column=0, sticky='nsew', pady=0, padx=(5, 0))

    def __change_appearance_mode_event(self):
        """
        Function will switch Between Dark and Light mode.
        """
        if self.__mode == 'Dark':
            self.__mode = 'Light'
            customtkinter.set_appearance_mode(self.__mode)
            self.__load_nlh_app_logo()
        else:
            self.__mode = 'Dark'
            customtkinter.set_appearance_mode(self.__mode)
            self.__load_nlh_app_logo()

    def __open_nlh_SharePoint(self):
        """
        Function will send user to the NLH website.
        """
        webbrowser.open(self.__nlh_xml.project_url, new=2)

    def __open_update_window(self):
        """
        Function will open the update window.
        """
        self.master.withdraw()
        self.__status_label.configure(text='')
        if self.__update_window is None or not self.__update_window.winfo_exists():
            self.__update_window = UpdateWindow(
                self,
                nlh_xml_obj=self.__nlh_xml,
                new_version_param=self.__new_version_param,
                widgets_text=self.__widgets_text,
                sharepoint_handler=self.master.sharepoint_handler,
                main_window_control_commend=self.__main_window_control_commend
            )

    def change_update_menu_status_text(self, new_text: str, color: str = 'white'):
        """
        Change the status_label text.
        """
        self.__status_label.configure(text=new_text, text_color=color)

    def get_update_parameters(self, new_version_param: str | list = None):
        """
        Update the NLH update parameters.
        """
        self.__new_version_param = new_version_param

    def initialize_sharepoint_connection(self):
        """
        Initialize SharePoint connection in background thread.

        Called by MainWindow.__on_loading_complete() — i.e. only after the
        startup LoadingWindow has fully closed.  It is never called from
        __init__ and never called when the user opens the LoadingWindow
        via the 'Load Script and Tools' dropdown option.
        """

        def create_and_authenticate_handler():
            """Function to run in background thread."""
            from main_app_files.function_files._sharepoint_handling import SharePointHandler

            # Create handler without auto-authentication
            handler = SharePointHandler(self.__nlh_xml.sharepoint[0], auto_authenticate=False)

            # Authenticate manually
            handler.authenticate()

            return handler

        def gui_callback(handler):
            """Callback when SharePoint initialization is complete."""

            # Store the handler in the master (MainWindow)
            self.master.sharepoint_handler = handler

            self._is_logging_in = False

            if handler.is_authenticated:
                # Authentication successful
                self.change_update_menu_status_text(
                    new_text="SharePoint connected successfully",
                    color='green'
                )
                # Update login button — logged in state
                self.__login_button.configure(
                    text=self.__widgets_text['login_button'][1], state="disabled"
                )

                # Update tools with SharePoint handler
                self.master.update_tools_sharepoint_handler()

                # Now run the update check
                self.run_check_update_function_thread_manger()
            else:
                # Authentication failed
                self.change_update_menu_status_text(
                    new_text=f"SharePoint connection failed: {handler.authentication_error}",
                    color='red'
                )
                # Update login button — not logged in state
                self.__login_button.configure(
                    text=self.__widgets_text['login_button'][0], state="normal"
                )

                # Update tools with SharePoint handler (unauthenticated)
                self.master.update_tools_sharepoint_handler()

        # Set login button to "logging in" state
        self._is_logging_in = True
        self.__login_button.configure(
            text=self.__widgets_text['login_button'][2], state="disabled"
        )

        # Run SharePoint initialization in background
        thread_runner(self.master, create_and_authenticate_handler, gui_callback)

    def retry_sharepoint_login(self):
        """
        Method to retry SharePoint authentication (for login button).
        """
        if not self.master.sharepoint_handler:
            # Create new handler if it doesn't exist
            self.initialize_sharepoint_connection()
            return

        def retry_authentication():
            """Function to run in background thread."""
            return self.master.sharepoint_handler.retry_authentication()

        def gui_callback(success):
            """Callback when retry is complete."""
            self._is_logging_in = False

            if success:
                self.change_update_menu_status_text(
                    new_text="SharePoint re-connected successfully",
                    color='green'
                )
                # Update login button — logged in state
                self.__login_button.configure(
                    text=self.__widgets_text['login_button'][1], state="disabled"
                )

                # Update tools with SharePoint handler
                self.master.update_tools_sharepoint_handler()

                self.run_check_update_function_thread_manger()
            else:
                self.change_update_menu_status_text(
                    new_text=f"SharePoint re-connection failed: "
                             f"{self.master.sharepoint_handler.authentication_error}",
                    color='red'
                )
                # Update login button — not logged in state
                self.__login_button.configure(
                    text=self.__widgets_text['login_button'][0], state="normal"
                )

                # Update tools with SharePoint handler
                self.master.update_tools_sharepoint_handler()

        # Set login button to "logging in" state
        self._is_logging_in = True
        self.__login_button.configure(
            text=self.__widgets_text['login_button'][2], state="disabled"
        )

        # Run retry in background thread
        thread_runner(self.master, retry_authentication, gui_callback)

    def run_check_update_function_thread_manger(self):
        """
        Run check for updates using the existing SharePoint connection.
        """
        if not self.master.sharepoint_handler or not self.master.sharepoint_handler.is_authenticated:
            self.change_update_menu_status_text(
                new_text="No SharePoint connection available",
                color='red'
            )
            return False

        def gui_callback(available_updates):
            """Callback function to update the GUI based on the result of check_for_updates."""
            if type(available_updates) is list:
                self.change_update_menu_status_text(
                    new_text=f'New {available_updates[1]} version available: {available_updates[0]}',
                    color='green'
                )
                self.get_update_parameters(new_version_param=available_updates)
                self.update_status = True
                return True
            elif 'Error' not in available_updates:
                self.change_update_menu_status_text(new_text=available_updates)
                self.update_status = True
                return True
            else:
                self.change_update_menu_status_text(new_text=available_updates, color='red')
                self.get_update_parameters(new_version_param=available_updates)
                self.update_status = True
                return False

        # Use the existing SharePoint handler
        thread_runner(
            self.master,
            self.master.sharepoint_handler.check_for_updates,
            gui_callback,
            args=(
                self.__nlh_xml.sharepoint[1],
                self.__nlh_xml.version_number,
                self.__nlh_xml.version_type,
                self.__nlh_xml.participate_in_testing,
            )
        )
        return True