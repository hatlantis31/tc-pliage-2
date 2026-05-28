"""
This module contains the UpdateWindow class, which is responsible for handling the update process of the application.

The UpdateWindow class creates a graphical user interface that allows users to check for updates, download and install new versions of the application.
It interacts with SharePoint to check for and download updates, and manages the update process including user authentication and progress display.

Classes:
    UpdateWindow: A customtkinter.CTkToplevel window for managing application updates.

Dependencies:
    - subprocess
    - sys
    - customtkinter
    - time
    - main_app_files.function_files._sharepoint_handling
    - main_app_files.function_files.exception_handler_and_reporting
    - main_app_files.function_files._threading_handler
    - main_app_files.function_files._nlh_xml_handler
    - typing

The module defines a Literal type 'sharepoint_action_choices' for specifying SharePoint actions.
"""
import subprocess
import sys

import customtkinter
import time

from main_app_files.function_files._threading_handler import thread_runner
from main_app_files.function_files._nlh_xml_handler import NlhXmlHandler
from typing import Literal

sharepoint_action_choices = Literal['download_update_file', 'perform_sharepoint_action']


class UpdateWindow(customtkinter.CTkToplevel):
    """
    the UpdateWindow Class is window that will allow user to check for new version and started the update process
    """

    def __init__(self, *args, nlh_xml_obj: NlhXmlHandler, main_window_control_commend: dict,
                 sharepoint_handler=None, new_version_param: str | list = None, widgets_text: dict = None,
                 **kwargs):
        super().__init__(*args, **kwargs)

        # ============ General GUI Settings ============
        WIDTH = 450
        HEIGHT = 150
        self.geometry(f'{WIDTH}x{HEIGHT}')
        self.resizable(False, False)
        # self.attributes('-topmost', 'true')
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ============ Update Window specific GUI Variables ============

        self.button_list: list = []
        self.progress_bar = None
        self.__main_window_control_commend = main_window_control_commend

        # ============ Update Window Variables ============
        self.__widgets_text = widgets_text
        self.__nlh_xml_obj = nlh_xml_obj
        self.__sharepoint_handler = sharepoint_handler
        self.__new_version_param = new_version_param
        self.__run_thread = None
        self.__download_step = 0
        self.sharepoint_status = True

        # =================================
        # ============ Graphic ============
        # =================================

        self.title(self.__widgets_text['title_update_window'])

        # ========= TOP -> Status Message  =========
        self.__status_message_frame = customtkinter.CTkFrame(master=self)
        self.__status_message_frame.pack(fill='both', side='top', expand=True, padx=5, pady=(5, 0))

        self.__status_message_label = customtkinter.CTkLabel(master=self.__status_message_frame,
                                                             text='')
        self.__status_message_label.pack(fill='both', expand=True, padx=5, pady=5)

        # ========= BOTTOM RIGHT -> Participate In Testing =========

        self.__participate_in_testing_frame = customtkinter.CTkFrame(master=self)
        self.__participate_in_testing_frame.pack(fill='x', side='right', padx=5, pady=5)

        self.__participate_in_testing_button = customtkinter.CTkSwitch(master=self.__participate_in_testing_frame,
                                                                       text=self.__widgets_text['__participate_in_testing_button'])
        if self.__nlh_xml_obj.participate_in_testing:
            self.__participate_in_testing_button.select()
        else:
            self.__participate_in_testing_button.deselect()
        self.__participate_in_testing_button.pack(fill='x', side='right', padx=5, pady=6)
        self.__participate_in_testing_button.configure(command=self.__change_participate_in_testing_status, state='disabled')

        # ========= BOTTOM LEFT -> buttons and Progress bar=========
        self.__frame_buttons = customtkinter.CTkFrame(master=self)
        self.__frame_buttons.pack(fill='x', side='left', expand=True, padx=5, pady=5)

        # ========= Initial behavior of the window =========
        self.__check_update_and_sharepoint_status()

    # ===================================
    # ============ functions ============
    # ===================================

    # ============ General functions ============
    def on_closing(self):
        """
        destroy window on close
        """
        # Kill any running threads
        if self.__run_thread:
            self.__run_thread.stop()
            self.__run_thread.join()
        # Make the Main Window visible Again
        self.__main_window_control_commend['deiconify']()
        self.destroy()

    def __create_buttons(self, button_dict: dict):
        """
        create buttons
        button_dict: {button 1 name, }
        """
        self.__destroy_buttons_in_list()
        for button_name, button_function in button_dict.items():
            button = customtkinter.CTkButton(master=self.__frame_buttons,
                                             text=button_name,
                                             width=100,
                                             border_width=2,
                                             command=button_function)
            button.pack(padx=5, pady=5, side='left')
            self.button_list.append(button)

    def __destroy_buttons_in_list(self):
        """
        kills all buttons
        """
        if len(self.button_list) > 0:
            for button in self.button_list:
                button.destroy()
            self.button_list = []

    def __crate_and_start_progress_bar(self, statu_text, progress_bar_speed: float = 1, progress_bar_auto_start: bool = True):
        """
        Make a new progress_bar and update the statu_text
        progress_bar_speed:
        progress_bar_auto_start:
        statu_text: the __status_message_label text
        """
        if not self.progress_bar:
            self.__status_message_label.configure(text=statu_text, text_color='white')
            self.progress_bar = customtkinter.CTkProgressBar(self.__status_message_frame, orientation="horizontal", determinate_speed=progress_bar_speed)
            self.progress_bar.set(0)
            self.progress_bar.pack(padx=5, pady=5)
            if progress_bar_auto_start:
                self.progress_bar.start()

    def __kill_progress_bar(self):
        """
        destroy the progress_bar
        """
        if self.progress_bar:
            self.progress_bar.destroy()
            self.progress_bar = None

    def __change_participate_in_testing_status(self):
        """
        change the statues of the participate_in_testing
        """
        self.__nlh_xml_obj.change_participate_in_testing_status()
        self.__check_update_and_sharepoint_status(participate_in_testing_button_status_change=True)

    # ============ Check for update functions ============
    def __check_update_and_sharepoint_status(self, participate_in_testing_button_status_change: bool = False):
        """
        Check SharePoint authentication status and handle update checking accordingly.
        """
        self.__participate_in_testing_button.configure(state='disabled')

        # Check if SharePoint handler is available and authenticated
        if not self.__sharepoint_handler or not self.__sharepoint_handler.is_authenticated:
            self.__status_message_label.configure(
                text="SharePoint authentication required.\nPlease login from the main window.",
                text_color='red'
            )
            self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
            return

        # If we have version parameters, and it's not a button status change, show update info
        if type(self.__new_version_param) is list and not participate_in_testing_button_status_change:
            self.__status_message_label.configure(text=f'{self.__widgets_text["new_version_available_status"]}\n '
                                                       f'{self.__new_version_param[0]} {self.__new_version_param[1]}\n'
                                                       f'{self.__widgets_text["press_update_status"]}\n ', text_color='green')
            self.__create_buttons({self.__widgets_text['close_button']: self.on_closing, self.__widgets_text['update_option']: self.__update_app})
            self.__participate_in_testing_button.configure(state='normal')
        # If there's an error or button status change, check for updates
        elif (self.__new_version_param and 'Error' in self.__new_version_param) or participate_in_testing_button_status_change:
            self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
            self.__run_check_update_function_thread_manger()
        else:
            self.__status_message_label.configure(text=self.__widgets_text['latest_version_status'])
            self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
            self.__participate_in_testing_button.configure(state='normal')

    def __run_check_update_function_thread_manger(self):
        """
        Manages the process of checking for updates using the shared SharePoint handler.
        """
        if not self.__sharepoint_handler or not self.__sharepoint_handler.is_authenticated:
            self.__status_message_label.configure(
                text="SharePoint not authenticated.\nPlease login from the main window.",
                text_color='red'
            )
            self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
            return False

        self.__participate_in_testing_button.configure(state='disabled')
        self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
        self.__crate_and_start_progress_bar(self.__widgets_text['checking_for_update_status'])

        def check_for_updates_callback(available_updates):
            """
            Callback function to handle the result of the update check.
            """
            self.__kill_progress_bar()
            if type(available_updates) is list:
                self.__new_version_param = available_updates
                self.__status_message_label.configure(text=f'{self.__widgets_text["new_version_available_status"]}\n '
                                                           f'{self.__new_version_param[0]} {self.__new_version_param[1]}\n'
                                                           f'{self.__widgets_text["press_update_status"]}\n ', text_color='green')
                self.__create_buttons({self.__widgets_text['close_button']: self.on_closing, self.__widgets_text['update_option']: self.__update_app})
                self.__participate_in_testing_button.configure(state='normal')
                self.sharepoint_status = True
                return True
            elif 'Error' not in available_updates:
                self.__status_message_label.configure(text=available_updates, text_color='white')
                self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
                self.__new_version_param = None
                self.__participate_in_testing_button.configure(state='normal')
                self.sharepoint_status = True
                return True
            else:
                self.__status_message_label.configure(text=f'{available_updates}\n {self.__widgets_text["press_check_update_status"]}', text_color='red')
                self.__create_buttons({self.__widgets_text['close_button']: self.on_closing,
                                       self.__widgets_text['check_update_button']: self.__check_update_and_sharepoint_status})
                self.__new_version_param = available_updates
                self.__participate_in_testing_button.configure(state='normal')
                self.sharepoint_status = False
                return False

        # Use the shared SharePoint handler
        thread_runner(self, self.__sharepoint_handler.check_for_updates, check_for_updates_callback,
                      args=(self.__nlh_xml_obj.sharepoint[1],
                            self.__nlh_xml_obj.version_number,
                            self.__nlh_xml_obj.version_type,
                            self.__nlh_xml_obj.participate_in_testing))
        return self.sharepoint_status

    def __update_app_tread_manger(self):
        """
        Manages the process of downloading and updating the application using the shared SharePoint handler.
        """
        if not self.__sharepoint_handler or not self.__sharepoint_handler.is_authenticated:
            self.__status_message_label.configure(
                text="SharePoint not authenticated.\nPlease login from the main window.",
                text_color='red'
            )
            self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
            return False

        self.__participate_in_testing_button.configure(state='disabled')
        self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
        self.__crate_and_start_progress_bar(f"{self.__new_version_param[1]}  {self.__new_version_param[0]} {self.__widgets_text['updating_status']}.",
                                            progress_bar_speed=0.1)

        def download_update_file_callback(update_file_local_location):
            """
            Callback function to handle the result of the update file download.
            """
            self.__kill_progress_bar()
            self.__download_step = 0
            # Remove the .zip extension if present
            if self.__new_version_param[2].endswith('.zip'):
                self.__new_version_param[2] = self.__new_version_param[2][:-4]
            if self.__new_version_param[2] in update_file_local_location:
                subprocess.Popen(update_file_local_location, creationflags=subprocess.DETACHED_PROCESS, shell=True)
                if type(self.button_list) is list:
                    for button in self.button_list:
                        button.configure(state='disabled')
                self.sharepoint_status = True
                time.sleep(2)
                sys.exit()
            else:
                self.__status_message_label.configure(text=self.__widgets_text['error_downloading_updates'], text_color='Red')
                self.__create_buttons({self.__widgets_text['close_button']: self.on_closing})
                self.__participate_in_testing_button.configure(state='normal')
                self.sharepoint_status = False
                return False

        # Use the shared SharePoint handler
        thread_runner(self, self.__sharepoint_handler.download_update_file, download_update_file_callback,
                      args=(self.__nlh_xml_obj.sharepoint[1],
                            self.__new_version_param[2],
                            self.__new_version_param[3],
                            self.__chunk_downloaded))
        return self.sharepoint_status

    def __update_app(self):
        """
        Start the update process using the shared SharePoint handler
        """
        self.__update_app_tread_manger()

    def __chunk_downloaded(self, offset: int):
        """
        advance the __download_step by one
        offset:
        """
        self.__download_step += offset / self.__new_version_param[3]
