"""
This module defines the `InformationFrame` class, which is a custom frame used for displaying information about log handlers.

The frame includes:
- A button to display a table with available handlers.
- A dropdown menu to select different log handlers.
- A button to open a PDF document related to the selected log handler.
- A text box to display descriptions for the selected log handler.

The `InformationFrame` class also includes methods to update its content dynamically based on provided parameters.

Classes:
    InformationFrame: A custom frame for displaying log handler information.

Dependencies:
    - webbrowser
    - customtkinter
    - PIL.Image
    - CustomTable from analysis_files.core_script_files.custom_graphs
"""
import webbrowser
import customtkinter

from PIL import Image
from main_app_files.core_script_files.custom_graphs import CustomTable


class InformationFrame(customtkinter.CTkFrame):
    def __init__(self, master, pdf_logo: Image.Image, widgets_text: dict, information_param: dict, **kwargs):
        """
        information pane (Description text box, links to pdf and logs table
        master:
        pdf_logo:
        widgets_text: dict with all the buttons and messages text {'description_label':'text',
                                                                          'available_handler_table_button':'text',
                                                                          'group_dropdown_label':'text',
                                                                          'handle_info_dropdown_label':'text',
                                                                          'Log_handlers_names_list': list of handler names,
                                                                          'description_dict': dict of handler names,
                                                                          'information_param': information table dataframe}
        information_param: dic with the Log_handlers_names_list, description_dict and log_handlers_information_table
        """
        super().__init__(master, **kwargs)

        # ===================================
        # =========   Parameters    =========
        # ===================================

        self.__pdf_logo = pdf_logo
        self.__widgets_text = widgets_text
        self.__Log_handlers_names_list = information_param['Log_handlers_names_list']
        self.__description_dict = information_param['description_dict']
        self.__log_handlers_information_table = information_param['log_handlers_information_table']
        self.__groups_list = information_param['groups_list']
        self.__handler_to_group = information_param['handler_to_group']
        self.__current_group = "All Log Handler Types"

        # ===================================
        # ============    GUI    ============
        # ===================================

        # ============ GUI grid config ============
        self.grid_rowconfigure((0, 1, 2, 3, 5), weight=0)  # information label, handler table button, dropdown menu and PDf link height don't expend
        self.grid_rowconfigure(4, weight=1)  # TextBox height expend
        self.grid_columnconfigure(0, weight=0)  # All width expend
        self.grid_columnconfigure(1, weight=1)

        # ============ available handler table button ============
        self.__available_handler_table_button = customtkinter.CTkButton(master=self,
                                                                        text=f'{self.__widgets_text["available_handler_table_button"]}',
                                                                        height=11, border_spacing=0,
                                                                        command=self.__open_info_table)
        self.__available_handler_table_button.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=(5, 0))

        # ============  Group Label and Dropdown Menu ============
        self.__group_label = customtkinter.CTkLabel(master=self, text=self.__widgets_text['group_dropdown_label'],
                                                    font=customtkinter.CTkFont(weight="bold"))
        self.__group_label.grid(row=2, column=0, sticky='w', padx=(5, 2), pady=(2, 0))

        self.__group_dropdown = customtkinter.CTkOptionMenu(master=self,
                                                            values=self.__groups_list,
                                                            command=self.__on_group_change,
                                                            height=20)
        self.__group_dropdown.grid(row=2, column=1, sticky='ew', padx=(2, 5), pady=(2, 0))
        self.__group_dropdown.set('All Log Handler Types')

        # ============  Handler Label and Dropdown Menu ============
        self.__handler_label = customtkinter.CTkLabel(master=self, text=self.__widgets_text['handle_info_dropdown_label'],
                                                      font=customtkinter.CTkFont(weight="bold"))
        self.__handler_label.grid(row=3, column=0, sticky='w', padx=(5, 2), pady=0)

        self.__log_info_dropdown = customtkinter.CTkOptionMenu(master=self,
                                                               values=self.__Log_handlers_names_list,
                                                               command=self.__on_handler_change,
                                                               height=20)
        self.__log_info_dropdown.grid(row=3, column=1, sticky='ew', padx=(2, 5), pady=0)
        self.__log_info_dropdown.set('Nikon Log Handler')

        # ============ Description Text Box ============
        self.__description_text_box = customtkinter.CTkTextbox(master=self, wrap='word')
        self.__description_text_box.grid(row=4, column=0, columnspan=2, sticky='nsew', padx=5, pady=(5, 0))
        self.__description_text_box.insert('0.0', self.__description_dict['Nikon Log Handler']['description'])  # Put the App description in the info textBox at the start
        self.__description_text_box.configure(state='disabled')  # disabled is so you can edit the line

        # ============  Lunch PDF button ============
        self.__pdf_logo = customtkinter.CTkImage(self.__pdf_logo, size=(20, 20))
        self.__lunch_pdf_button = customtkinter.CTkButton(master=self,
                                                          image=self.__pdf_logo, text='Open PDF Documentation', width=20, command=self.__open_pdf)
        self.__lunch_pdf_button.grid(row=5, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

    # ===================================
    # ============ functions ============
    # ===================================

    def change_buttons_text_and_information_param(self, widgets_text: dict, information_param: dict, current_handler: str):
        """
        change the button text
        information_param:
        current_handler:
        widgets_text: dict with all the buttons and messages text {'description_label':'text',
                                                                          'available_handler_table_button':'text',
                                                                          'group_dropdown_label':'text',
                                                                          'handle_info_dropdown_label':'text',
                                                                          'Log_handlers_names_list': list of handler names,
                                                                          'description_dict': dict of handler names,
                                                                          'information_param': information table dataframe}
        :return: None
        """
        self.__widgets_text = widgets_text

        # Update button text
        self.__available_handler_table_button.configure(text=self.__widgets_text['available_handler_table_button'])

        # Update label texts
        self.__group_label.configure(text=self.__widgets_text['group_dropdown_label'])
        self.__handler_label.configure(text=self.__widgets_text['handle_info_dropdown_label'])

        # Update data
        self.__Log_handlers_names_list = information_param['Log_handlers_names_list']
        self.__description_dict = information_param['description_dict']
        self.__log_handlers_information_table = information_param['log_handlers_information_table']
        self.__groups_list = information_param['groups_list']
        self.__handler_to_group = information_param['handler_to_group']

        # Update group dropdown
        self.__group_dropdown.configure(values=self.__groups_list)

        # Update handler dropdown with all handlers initially
        self.__log_info_dropdown.configure(values=self.__Log_handlers_names_list)
        self.set_dropdown_value(current_handler)

    def set_dropdown_value(self, dropdown_value: str):
        """
        dropdown_value:
        """
        if dropdown_value == 'Nikon Log Handler':
            # Special case for 'Nikon Log Handler' - only available in "All Log Handler Types"
            self.__current_group = "All Log Handler Types"
            self.__group_dropdown.set("All Log Handler Types")
            handlers_for_group = self.__get_handlers_for_group("All Log Handler Types")
            self.__log_info_dropdown.configure(values=handlers_for_group)
            self.__log_info_dropdown.set(dropdown_value)
            self.__change_description_text_box_text()
        elif dropdown_value in self.__Log_handlers_names_list:
            # Update group dropdown to match handler's group
            if dropdown_value in self.__handler_to_group:
                handler_group = self.__handler_to_group[dropdown_value]
                self.__current_group = handler_group
                self.__group_dropdown.set(handler_group)
                # Update handler dropdown to show only handlers in this group
                handlers_for_group = self.__get_handlers_for_group(handler_group)
                self.__log_info_dropdown.configure(values=handlers_for_group)
                self.__log_info_dropdown.set(dropdown_value)
                self.__change_description_text_box_text()

    def __get_handlers_for_group(self, group: str):
        """Get list of handlers for a specific group"""
        if group == "All Log Handler Types":
            # For "All" group, include 'Nikon Log Handler' at the beginning
            handlers_list = self.__Log_handlers_names_list.copy()
            if 'Nikon Log Handler' not in handlers_list:
                handlers_list.insert(0, 'Nikon Log Handler')
            return handlers_list
        else:
            # For specific groups, only return handlers that belong to that group
            # Do NOT include 'Nikon Log Handler'
            handlers_in_group = [handler for handler, handler_group in self.__handler_to_group.items()
                                 if handler_group == group and handler != 'Nikon Log Handler']
            return handlers_in_group

    def __on_group_change(self, selected_group: str):
        """Handle group dropdown change"""
        self.__current_group = selected_group
        handlers_for_group = self.__get_handlers_for_group(selected_group)
        self.__log_info_dropdown.configure(values=handlers_for_group)

        # Set the first handler in the group as selected
        if handlers_for_group:
            self.__log_info_dropdown.set(handlers_for_group[0])
            self.__change_description_text_box_text()

    def __on_handler_change(self, selected_handler: str):
        """Handle handler dropdown change"""
        # Update group dropdown to match handler's group
        if selected_handler in self.__handler_to_group:
            handler_group = self.__handler_to_group[selected_handler]
            if self.__current_group != handler_group:
                self.__current_group = handler_group
                self.__group_dropdown.set(handler_group)
                # Update handler dropdown to show only handlers in this group
                handlers_for_group = self.__get_handlers_for_group(handler_group)
                self.__log_info_dropdown.configure(values=handlers_for_group)

        self.__change_description_text_box_text()

    def __change_description_text_box_text(self, *args):
        """
        param text: text to put in description_text_box if none will put up app description
        """
        self.__description_text_box.configure(state='normal')
        self.__description_text_box.delete('0.0', 'end')
        self.__description_text_box.insert('0.0', self.__description_dict[self.__log_info_dropdown.get()]['description'])
        self.__description_text_box.configure(state='disabled')

    def __open_info_table(self):
        """
        Open a table with all the handlers information
        :return: None
        """
        info_table = customtkinter.CTkToplevel(self)
        info_table.title(self.__widgets_text['available_handler_table_button'])
        info_table.geometry(f'{1000}x{500}')
        table = CustomTable(info_table, data_table=self.__log_handlers_information_table)
        table.pack(fill='both', expand=1)

    def __open_pdf(self):
        """
        Open handler PDF doc
        :return: None
        """
        new = 2  # open in a new tab, if possible
        webbrowser.open(self.__description_dict[self.__log_info_dropdown.get()]['pdf link'], new=new)
