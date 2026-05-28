"""
This module provides the NlhXmlHandler class which is responsible for handling
the XML configuration of the NLH application. It includes methods to validate
version numbers and types, update XML content, and retrieve various attributes
from the XML.
"""

import re

from xml.etree import ElementTree
from typing import Literal
from main_app_files.function_files._in_version_number import version_number as int_version_number
from main_app_files.function_files._in_version_number import version_type as int_version_type
from main_app_files.function_files.exception_handler_and_reporting import NlhException

available_version_type = Literal['testing', 'release']


class NlhXmlHandler:
    """
    Class will import the XML of NLH and get attribute from like title and more
    will also validate the version
    """
    __version_number = int_version_number
    __version_type: available_version_type = int_version_type
    __available_version_type = ('testing', 'release')

    def __init__(self, app_xml: str):
        """
        Initialize the NlhXmlHandler with the given XML file.

        :param app_xml: Path to the application XML file.
        :raise NlhException: If there is an issue with the XML or version validation.
        """
        self.__app_xml = app_xml
        self.__nikon_log_handler_xml = ElementTree.parse(app_xml)
        self.__xml_version_number = self.__nikon_log_handler_xml.find("./info/version_number").text
        self.__xml_version_type = self.__nikon_log_handler_xml.find("./info/version_type").text
        try:
            self.__check_version_number_format(version_number=self.__version_number, version_type=self.__version_type, location='APP')
            self.__check_version_number_format(version_number=self.__xml_version_number, version_type=self.__xml_version_type, location='XML')
            self.__check_version_match()
        except Exception as e:
            raise NlhException("NLH installation is corrupted, please reinstall the NLH using the install file") from e

    def __check_version_type_value(self, location: str, version_type: str = __version_type, ):
        """
        Check if the version type value is one of the allowed ones
        :param location: location form witch version type is taken from
        :param version_type: the version type value
        :return: rise exception if there is an issue
        """
        if not version_type in self.__available_version_type:
            raise ValueError(f'The {location} version type need to be either {self.__available_version_type[0]} or {self.__available_version_type[1]} instead got {version_type}')

    def __check_version_number_format(self, location: str, version_number: str = __version_number, version_type: str = __version_type):
        """
        Check if the version number is in the correct format
        :param location: location form witch version number is taken from
        :param version_type: the version type value
        :param version_number: version number str to check by default it will check the internal string
        :return: rise exception if there is an issue
        """
        self.__check_version_type_value(version_type=version_type, location=location)
        if not re.match("^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$", version_number):
            raise ValueError(f'The {location} version number format expected to be x.y.z.n')

    def __check_version_match(self):
        """
        Check if the XML version and internal version are matched
        :return: rise an exception if there is an issue
        """
        if self.__xml_version_number != self.__version_number or self.__xml_version_type != self.__version_type:
            raise ValueError('XML Version and App version are mismatch')

    def _change_version_number_and_type(self, new_version_number: str, new_version_type: available_version_type):
        """
        Update version number and type in the XML
        :param new_version_number:
        :param new_version_type:
        :return: None
        """
        self.__check_version_number_format(version_number=new_version_number, version_type=new_version_type, location='XML')
        self.__nikon_log_handler_xml.find('./info/current_version_number').text = new_version_number
        self.__nikon_log_handler_xml.find('./info/current_version_type').text = new_version_type
        self.__nikon_log_handler_xml.write(self.__app_xml)

    def change_participate_in_testing_status(self):
        """
        Switch participate_in_testing value between True and False in the XML
        :return: None
        """
        # Check if we should participate in testing and set the corresponding XML value
        if self.participate_in_testing:
            # Find the XML element. If the 'Update_Variables' is the root element, './' is not necessary.
            element = self.__nikon_log_handler_xml.find('Update_Variables/participate_in_testing')
            # If the element is found, update its text value to 'False'
            if element is not None:
                element.text = 'False'
            else:
                # If the element is not found, handle it appropriately (e.g., log an error)
                raise NlhException("Error: 'participate_in_testing' element not found in the XML.")

        else:
            # Find the XML element. If the 'Update_Variables' is the root element, './' is not necessary.
            element = self.__nikon_log_handler_xml.find('Update_Variables/participate_in_testing')
            # If the element is found, update its text value to 'True'
            if element is not None:
                element.text = 'True'
            else:
                # If the element is not found, handle it appropriately (e.g., log an error)
                raise NlhException("Error: 'participate_in_testing' element not found in the XML.")

        # After updating the XML, write the changes back to the file
        self.__nikon_log_handler_xml.write(self.__app_xml)

    def change_default_language(self, default_language: str):
        """
        Switch participate_in_testing value between True and False in the XML
        :return: None
        """
        self.__nikon_log_handler_xml.find('./setting/default_language').text = default_language
        self.__nikon_log_handler_xml.write(self.__app_xml)

    @property
    def full_app_version(self):
        """
        Get the full application version including type.

        :return: Full application version string.
        """
        if self.__version_type == self.__available_version_type[1]:
            return f'{self.version_number_short} {self.__version_type}'
        else:
            return f'{self.__version_number}.{self.__version_type}'

    @property
    def version_number(self):
        """
        Get the application version number.

        :return: Application version number string.
        """
        return self.__version_number

    @property
    def version_number_short(self):
        """
        Get the short version of the application version number x.y.z.

        :return: Short version number string.
        """
        version_number = self.__version_number.split('.')
        return f'{version_number[0]}.{version_number[1]}.{version_number[2]}'

    @property
    def release_version_number(self):
        """
        Get the release version of the application version number x.y.

        :return: Short version number string.
        """
        version_number = self.__version_number.split('.')
        return f'{version_number[0]}.{version_number[1]}'

    @property
    def version_type(self):
        """
        Get the application version type.

        :return: Application version type string.
        """
        return self.__version_type

    @property
    def project_name(self):
        """
        Get the project name from the XML.

        :return: Project name string.
        """
        return self.__nikon_log_handler_xml.find("./info/project_name").text

    @property
    def project_url(self):
        """
        Get the project URL from the XML.

        :return: Project URL string.
        """
        return self.__nikon_log_handler_xml.find("./info/project_url").text

    @property
    def update_server(self):
        """
        Get the update server URL from the XML.

        :return: Update server URL string.
        """
        return self.__nikon_log_handler_xml.find("./Update_Variables/update_server").text + self.project_name + "/"

    @property
    def participate_in_testing(self):
        """
        Get the participate_in_testing status from the XML.

        :return: Boolean indicating participation in testing.
        """
        return self.__nikon_log_handler_xml.find("./Update_Variables/participate_in_testing").text == 'True'

    @property
    def title(self):
        """
        Get the title from the XML.

        :return: Title string.
        """
        return self.__nikon_log_handler_xml.find("./info/title").text

    @property
    def sharepoint(self):
        """
        Get the SharePoint URLs from the XML.

        :return: Tuple containing SharePoint URL and folder URL.
        """
        return self.__nikon_log_handler_xml.find("./Update_Variables/sharepoint_url").text, self.__nikon_log_handler_xml.find("./Update_Variables/sharepoint_url_folder_url").text

    @property
    def default_language(self):
        """
        Get the default language from the XML.

        :return: Default language string.
        """
        return self.__nikon_log_handler_xml.find("./setting/default_language").text