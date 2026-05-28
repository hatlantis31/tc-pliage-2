"""
A script to create the package NLH
"""
import logging
import sys
import time
from tkinter import messagebox

import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # Open the log file in write mode to clear it at the start
        logging.FileHandler('build_package_error.log', mode='w'),
        logging.StreamHandler()
    ]
)

import tkinter
import customtkinter
import git
import traceback
import pyinstaller_versionfile
import os
import shutil
import subprocess
import re
import zipfile
import requests
import warnings
import keyring
import json
import queue
import keyring.errors

from xml.etree import ElementTree
from typing import Literal, Union
from pathlib import Path
from main_app_files.function_files._threading_handler import thread_runner
from main_app_files.function_files._sharepoint_handling import SharePointHandler
from contextlib import contextmanager
from comtypes import CoInitialize, CoUninitialize

available_version_type = Literal['testing', 'release']

customtkinter.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class QueueHandler(logging.Handler):
    """Class to send logging records to a queue"""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """
        Emit a logging record by putting it into the queue.

        Args:
            record: The logging record to be emitted
        """
        self.log_queue.put(record)


# noinspection PyTypeChecker
class ConsoleFrame(customtkinter.CTkFrame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Create text widget for logs with dark theme
        self.log_text = customtkinter.CTkTextbox(
            self,
            fg_color="black",  # Black background
            text_color="white",  # White text
            font=("Courier", 12),  # Monospace font for better readability
            border_width=1,
            border_color="gray50"
        )
        self.log_text.grid(row=0, column=0, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Configure tags for different log levels with colors
        self.log_text.tag_config("INFO", foreground="white")
        self.log_text.tag_config("DEBUG", foreground="gray70")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")  # Make sure ERROR tag is configured
        self.log_text.tag_config("CRITICAL", foreground="red", underline=1)

        # Create logging queue and handler
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.queue_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.queue_handler)

        # Start queue checking
        self.after(100, self.check_queue)

    def check_queue(self):
        """Check for new log records"""
        # Process up to 100 records at a time to prevent GUI freezing
        for _ in range(100):
            try:
                record = self.log_queue.get_nowait()
                msg = self.queue_handler.format(record)
                self.log_text.configure(state='normal')

                # Insert message with appropriate color tag based on log level
                self.log_text.insert('end', msg + '\n', record.levelname)

                self.log_text.configure(state='disabled')
                self.log_text.see('end')  # Scroll to bottom
                self.update_idletasks()
            except queue.Empty:
                break

        # Schedule next check
        self.after(100, self.check_queue)

    def clear(self):
        """Clear the console"""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')


@contextmanager
def no_ssl_verification():
    """Context manager to temporarily disable SSL verification warnings"""
    old_merge_environment_settings = requests.Session.merge_environment_settings
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        """
        Merge environment settings for requests session with SSL verification disabled.

        Args:
            self: The session instance
            url (str): The URL for the request
            proxies (dict): Proxy settings for the request
            stream (bool): Whether to stream the request
            verify (bool): SSL verification setting
            cert (str | tuple): SSL certificate path or (cert, key) tuple

        Returns:
            dict: Modified settings dictionary with SSL verification disabled

        Note:
            This function is used within the no_ssl_verification context manager
            to temporarily disable SSL verification for requests.
        """
        opened_adapters.add(self.get_adapter(url))
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings

    requests.Session.merge_environment_settings = merge_environment_settings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
        yield
    requests.Session.merge_environment_settings = old_merge_environment_settings

    for adapter in opened_adapters:
        try:
            adapter.close()
        except Exception:
            pass


def check_python_version():
    """
    Check what version of python you run
    """
    python_major_version = sys.version_info.major
    python_minor_version = sys.version_info.minor
    if not (python_major_version == 3 and python_minor_version == 10):
        error_message = f"Error: This script is intended for Python versions 3.10. You are currently using Python {major_version}.{minor_version}."
        logging.error(error_message)
        raise Exception(error_message)
    if getattr(sys, 'base_prefix', sys.prefix) == sys.prefix:
        messagebox.showwarning("Warning", "You are not running inside a Python virtual environment.")


def handle_operation(operation_name):
    """
    A decorator that provides consistent error handling for PackageBuilder operations.

    This decorator wraps class methods to provide:
    - Consistent error handling
    - Automatic error logging with tracebacks
    - Standardized return format (success_flag, message)

    Args:
        operation_name (str): A descriptive name for the operation being performed.
                            This will be used in error messages.

    Returns:
        decorator: A decorator function that wraps the original method.

    Usage Example:
        @handle_operation("database connection")
        def connect_to_db(self):
            # Method implementation
            pass

    Note:
        - The decorated method should return a tuple of (bool, str) indicating success/failure
          and a message.
        - All exceptions are caught and logged, returning (False, error_message)
        - The decorator automatically logs errors with full tracebacks
    """

    def decorator(func):
        """
        A decorator that wraps functions to provide error handling.

        Args:
            func: The function to be decorated

        Returns:
            wrapper: The wrapped function that includes error handling

        Note:
            The wrapped function returns a tuple (bool, str) indicating success/failure
            and an error message if applicable.
        """

        def wrapper(*args, **kwargs):
            """
            Inner wrapper function that provides error handling for decorated functions.

            Args:
                *args: Variable length argument list passed to the decorated function
                **kwargs: Arbitrary keyword arguments passed to the decorated function

            Returns:
                tuple: A tuple containing:
                    - bool: True if function execution was successful, False otherwise
                    - str: Success message or error message if execution failed

            Note:
                This wrapper catches all exceptions, logs them with traceback,
                and returns a standardized (False, error_message) tuple on failure.
                The original function's return value is passed through on success.
            """
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {operation_name}: {str(e)}"
                logging.error(f"{error_msg}\n{traceback.format_exc()}")
                return False, error_msg

        return wrapper

    return decorator


class CredentialManager:
    """Handles secure storage and retrieval of credentials"""

    def __init__(self):
        self.system_name = "NLH_Builder"

    def save_credentials(self, sharepoint_username: str, gitea_username: str, password: str):
        """
        Save credentials securely using keyring.
        Only used in non-GUI mode.
        """
        # Only save credentials in non-GUI mode
        if '--no-gui' in sys.argv:
            user_credentials = {
                "sharepoint_username": sharepoint_username,
                "gitea_username": gitea_username,
                "password": password
            }
            keyring.set_password(self.system_name, "credentials", json.dumps(user_credentials))

    def get_credentials(self):
        """
        Retrieve credentials from keyring.
        In GUI mode, returns None to force password prompt.
        In non-GUI mode, returns stored credentials.
        """
        # In GUI mode, always return None to force password prompt
        if '--no-gui' not in sys.argv:
            return None

        # In non-GUI mode, return stored credentials
        try:
            credentials_json = keyring.get_password(self.system_name, "credentials")
            if credentials_json:
                return json.loads(credentials_json)
            return None
        except Exception:
            return None

    def clear_credentials(self):
        """Clear stored credentials"""
        try:
            keyring.delete_password(self.system_name, "credentials")
        except keyring.errors.PasswordDeleteError:
            pass

    @staticmethod
    def get_current_credentials():
        """
        Get current user credentials for GUI mode.
        Returns dict with SharePoint (AD email) and Gitea (Windows) usernames.
        """
        try:
            windows_username = os.getenv('username')
            ad_email = get_user_email_from_ad()

            if not windows_username or not ad_email:
                return None

            return {
                "sharepoint_username": ad_email,
                "gitea_username": windows_username,
                "password": None  # This will need to be set later
            }
        except Exception as e:
            logging.error(f"Error getting current credentials: {str(e)}")
            return None


def get_user_email_from_ad():
    """
    Retrieve the user's email address from Active Directory (AD).
    """
    try:
        # Initialize COM
        CoInitialize()

        try:
            from pyad import pyad

            # Get current username from system environment variables
            username = os.getenv('username')
            if not username:
                raise ValueError("Could not get username from environment variables")

            # Query AD to get user object using the username
            user = pyad.adobject.ADObject.from_cn(username)

            # Extract and return the email address from the user's AD properties
            if hasattr(user, 'mail') and user.mail:
                return user.mail
            else:
                raise ValueError("Email address not found in AD properties")

        finally:
            # Always uninitialize COM
            CoUninitialize()

    except ImportError as e:
        logging.error("Failed to import pyad module. Please ensure it's installed.")
        logging.error(traceback.format_exc())
        return None
    except Exception as e:
        logging.error(f"Failed to get user email from AD: {str(e)}")
        logging.error(traceback.format_exc())
        return None


class CredentialsDialog(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Enter Password")
        self.geometry("300x100")

        # Get Windows username for Gitea
        self.windows_username = os.getenv('username')
        if not self.windows_username:
            messagebox.showerror("Error", "Could not get Windows username")
            self.destroy()
            return

        # Get email from Active Directory for SharePoint
        self.ad_email = get_user_email_from_ad()
        if not self.ad_email:
            messagebox.showerror("Error", "Could not get email from Active Directory")
            self.destroy()
            return

        # Common password
        self.password_label = customtkinter.CTkLabel(self, text="Password:")
        self.password_label.grid(row=0, column=0, pady=5, padx=5)
        self.password_entry = customtkinter.CTkEntry(self, show="*")
        self.password_entry.grid(row=0, column=1, pady=5, padx=5)

        # Buttons
        self.ok_button = customtkinter.CTkButton(self, text="OK", command=self.ok_clicked)
        self.ok_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.result = None

    def ok_clicked(self):
        """
        Handle the OK button click event in the credentials dialog.
        Uses AD email for SharePoint and Windows username for Gitea.
        """
        self.result = {
            "sharepoint_username": self.ad_email,  # Use AD email for SharePoint
            "gitea_username": self.windows_username,  # Use Windows username for Gitea
            "password": self.password_entry.get()
        }
        self.destroy()


class PackageBuilder:
    """
    Base class for Package Builder, this is where all the logic is.
    """

    def __init__(self):
        super().__init__()
        self.credential_manager = CredentialManager()
        self.stop_flag = False
        self.sharepoint_handler = None  # Add SharePoint handler
        # ===================================
        # ============ Variables ============
        # ===================================
        self.version_number = {}
        self.make_release_tag = False
        self.repo = MangeRepo()
        self.version_number['repo_version'] = self.repo.current_repo_version_number
        self.app_xml_full_path = '../NikonLogHandler.xml'
        self.nikon_log_handler_xml = ElementTree.parse(self.app_xml_full_path)
        self.version_file_perm = {'Active branch': self.repo.active_brunch_name,
                                  'internal_version_number': '../main_app_files/function_files/_in_version_number.py',
                                  'version_file_full_path': '../version.rc',
                                  'company_name': self.nikon_log_handler_xml.find("./info/company_name").text,
                                  'file_description': self.nikon_log_handler_xml.find("./info/description").text,
                                  'internal_name': self.nikon_log_handler_xml.find("./info/title").text,
                                  'original_filename': f'{self.nikon_log_handler_xml.find("./info/project_name").text}.exe',
                                  'product_name': self.nikon_log_handler_xml.find("./info/project_name").text,
                                  'legal_copyright': self.nikon_log_handler_xml.find("./info/legal_copyright").text}
        self.version_number['xml_version'] = VersionNumber(f'{self.nikon_log_handler_xml.find("./info/version_number").text}.{self.nikon_log_handler_xml.find("./info/version_type").text}')
        self.version_number['new_version'] = self.auto_create_new_version_number()
        self.requirement = self.load_list_from_txt_file('../requirements.txt')
        self.files_folders_to_move = self.load_list_from_txt_file('files_folders_move.txt')
        self.step_done = False
        self.ifp_file_path = Path(__file__).parent / "nlh_install_build.ifp"
        self.installforge_path = r"C:\Program Files (x86)\solicus\InstallForge\bin\ifbuilderenvx86.exe"
        self.files_to_commit = ["NikonLogHandler.XML",
                                "./main_app_files/function_files/_in_version_number.py",
                                "NikonLogHandler.spec",
                                "./CD/nlh_install_builder_config_file.iss",
                                "./CD/nlh_install_build.ifp"]
        self.installer_zip_file_path = None
        # Define the path to the .iss file
        self.iss_file_path = Path(__file__).parent / "nlh_install_builder_config_file.iss"

    def stop_build(self):
        """Set the stop flag to True"""
        self.stop_flag = True

    @staticmethod
    def run_command(command, real_time=False):
        """
        Utility function to run a shell command.

        :param command: Command to be executed.
        :param real_time: If True, logs the output in real-time without opening a terminal window.
                          If False, captures and logs after completion.
        :return: Success status and output or error message.
        """
        if real_time:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
            output = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    logging.info(line.strip())
                    output.append(line.strip())
            return process.returncode == 0, "\n".join(output)
        else:
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
                logging.info(result.stdout)
                return True, result.stdout
            except subprocess.CalledProcessError as e:
                logging.error(f"Command '{command}' failed with error: {e.output}")
                return False, e.output

    def verify_credentials(self, sharepoint_username: str = None, gitea_username: str = None, password: str = None) -> tuple[bool, str]:
        """
        Verify SharePoint and Gitea credentials.
        Now uses SharePoint handler for authentication.

        Args:
            sharepoint_username: SharePoint username (not used with new handler)
            gitea_username: Gitea username
            password: Common password

        Returns:
            tuple[bool, str]: Success status and message
        """
        timeout = 10  # Set timeout to 10 seconds
        try:
            # Test SharePoint connection using SharePoint handler
            logging.info("Verifying SharePoint credentials...")

            if not self.sharepoint_handler:
                # Initialize SharePoint handler if not already done
                success, message = self.initialize_sharepoint_handler()
                if not success:
                    return False, f"SharePoint initialization failed: {message}"

            # Check if SharePoint handler is authenticated
            if not self.sharepoint_handler.is_authenticated:
                return False, f"SharePoint authentication failed: {self.sharepoint_handler.authentication_error}"

            logging.info("SharePoint authentication successful")

            # Test Gitea connection (if credentials provided)
            if gitea_username and password:
                logging.info("Verifying Gitea credentials...")
                remote_url = self.repo._current_repo.remotes.origin.url
                gitea_server = remote_url.split('/')[2]
                gitea_api_url = f"https://{gitea_server}/api/v1/user"

                with no_ssl_verification():
                    gitea_response = requests.get(
                        gitea_api_url,
                        auth=(gitea_username, password),
                        verify=False,
                        timeout=timeout
                    )

                logging.info(f"Gitea response status: {gitea_response.status_code}")

                if gitea_response.status_code != 200:
                    return False, f"Gitea authentication failed (Status: {gitea_response.status_code})"
                logging.info("Gitea authentication successful")

            return True, "Authentication successful"

        except requests.exceptions.Timeout:
            error_msg = "Connection timed out while verifying credentials"
            logging.error(error_msg)
            return False, error_msg
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error while verifying credentials: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logging.error(f"Full error: {traceback.format_exc()}")
            return False, error_msg

    @staticmethod
    def load_list_from_txt_file(txt_file_path):
        """
        return a list of all lines in file
        :param txt_file_path:
        :return:
        """
        with open(txt_file_path) as file:
            lines = [line.replace('\n', '') for line in file]
            return lines

    def auto_create_new_version_number(self):
        """
        Set new version number automatically based on active branch name,
        current version, and release conditions.
        :return:
        """
        active_branch = self.repo.active_brunch_name
        xml_version = self.version_number['xml_version']
        current_dev_stage = xml_version.Development_stage

        # Helper function to validate if branch name follows x.y.z.n pattern
        def is_version_pattern(branch_name):
            """
            Check if branch name is x.y.z.n (x,y,z and n are numbers)
            """
            return bool(re.match(r'^\d+\.\d+$', branch_name))

        if is_version_pattern(active_branch):
            if current_dev_stage == "release":
                # Rule 1: Branch matches pattern and current stage is release
                return VersionNumber(f"{self.version_number['xml_version'].version_number_hotfix_plus_one}.testing")

            elif current_dev_stage == "testing":
                if self.make_release_tag:
                    # Rule 3: Branch matches pattern, stage is testing, and make_release_tag is True
                    return VersionNumber(f"{self.version_number['xml_version'].version_number_build_plus_one}.release")
                else:
                    # Rule 2: Branch matches pattern, stage is testing, and make_release_tag is False
                    return VersionNumber(f"{self.version_number['xml_version'].version_number_build_plus_one}.testing")
            return None

        elif active_branch == "Development":
            if self.make_release_tag:
                # Rule 5: Active branch is Development and make_release_tag is True
                return VersionNumber(f"{self.version_number['xml_version'].version_number_build_plus_one}.release")
            else:
                # Rule 4: Active branch is Development and make_release_tag is False
                return VersionNumber(f"{self.version_number['xml_version'].version_number_build_plus_one}.testing")
        else:
            # Rule 6: Active branch is doesn't match pattern nor is Development
            return VersionNumber(f"{self.version_number['xml_version'].version_number_build_plus_one}.testing")

    def update_version_xml_handler(self):
        """
        Update a version number on intrnel file and xml
        :return:
        """
        self.nikon_log_handler_xml.find("./info/version_number").text = self.version_number['new_version'].version_number
        self.nikon_log_handler_xml.find('./info/version_type').text = self.version_number['new_version'].Development_stage
        if self.version_number['new_version'].Development_stage == 'release':
            self.nikon_log_handler_xml.find('Update_Variables/participate_in_testing').text = 'False'
        else:
            self.nikon_log_handler_xml.find('Update_Variables/participate_in_testing').text = 'True'
        self.nikon_log_handler_xml.write(self.app_xml_full_path)
        with open(self.version_file_perm['internal_version_number'], 'w') as file:
            file.writelines([f"version_number = '{self.version_number['new_version'].version_number}'\n",
                             f"version_type = '{self.version_number['new_version'].Development_stage}'"])

    def check_manual_version_number_input(self, manual_version_input):
        """
        Check if manual version number input is valid
        :param manual_version_input: string containing the version number
        :return: tuple (bool, str) indicating success/failure and message
        """
        try:
            # Create version number object with the input and current Development stage
            manual_version_number = VersionNumber(f'{manual_version_input}.{self.version_number["new_version"].Development_stage}')

            # Check if the new version is lower than the XML version
            if manual_version_number.version_number < self.version_number["xml_version"].version_number:
                return False, "New Version Number can't be lower than the XML version"

            # Update the version number if valid
            self.version_number["new_version"] = manual_version_number
            return True, f"Version number successfully updated to {manual_version_number.version_number}"

        except ValueError as exception:
            return False, str(exception)

    def make_version_file(self):
        """
        crate a version file
        """
        pyinstaller_versionfile.create_versionfile(
            output_file=self.version_file_perm['version_file_full_path'],
            version=self.version_number['new_version'].version_number,
            company_name=self.version_file_perm['company_name'],
            file_description=self.version_file_perm['file_description'],
            internal_name=self.version_file_perm['internal_name'],
            legal_copyright=self.version_file_perm['legal_copyright'],
            original_filename=self.version_file_perm['original_filename'],
            product_name=self.version_file_perm['product_name']
        )

    @staticmethod
    def check_and_update_spec(spec_file_path='../NikonLogHandler.spec'):
        """
        No-op: does not modify or validate the spec file.
        Returns (success: bool, message: str)
        """
        return True, "Spec check skipped."

    def update_install_build_file(self):
        """
        Update the Inno Setup configuration file with new version numbers and paths.

        This function performs several operations:
        1. Validates the original ISS file structure
        2. Updates version numbers in both #define and [Setup] sections
        3. Updates the output filename based on development stage
        4. Updates source paths for distribution files
        5. Validates the modified content before saving

        The function ensures the ISS file maintains its correct structure throughout modifications.
        It handles file encoding (UTF-8 with or without BOM) and performs thorough validation
        at each step.

        Raises:
            ValueError: If the ISS file structure is invalid
            Exception: For any other errors during the update process

        Returns:
            tuple[bool, str]: Success status and message, though typically raises exception on failure
        """

        def validate_iss_file(content, stage=""):
            """
            Validate Inno Setup Script (ISS) file content structure.

            Args:
                content (str): The content of the ISS file to validate
                stage (str): Description of the validation stage for error messages

            Raises:
                ValueError: If the content fails any validation check
            """
            # Remove BOM if present and clean content
            content = content.replace('\ufeff', '').strip()

            # Check if content is empty
            if not content:
                raise ValueError(f"{stage}: ISS file content is empty")

            # Split into lines and get first non-empty line
            lines = [line_n.strip() for line_n in content.split('\n') if line.strip()]
            if not lines:
                raise ValueError(f"{stage}: File contains no valid content")

            # Check for required sections
            required_sections = ['[Setup]', '[Files]', '[Icons]', '[Languages]', '[Code]']
            missing_sections = [section for section in required_sections if section not in content]
            if missing_sections:
                raise ValueError(f"{stage}: Missing required sections: {', '.join(missing_sections)}")

            # Find all #define statements and [Setup] section
            setup_index = -1
            define_statements = []

            for parm, line_n in enumerate(lines):
                if line_n.startswith('[Setup]'):
                    setup_index = parm
                    break
                elif line_n.startswith('#define'):
                    define_statements.append(line_n)

            # If there are no #define statements at the start, that's fine
            # If there are #define statements, they must all come before [Setup]
            if define_statements and setup_index > -1:
                for parm, line_n in enumerate(lines[setup_index:]):
                    if line_n.startswith('#define'):
                        raise ValueError(f"{stage}: Found #define statement after [Setup] section")

        logging.info(f"Updating ISS file at: {self.iss_file_path}")
        try:
            # Read original content with UTF-8-sig to handle BOM
            with open(self.iss_file_path, "r", encoding="utf-8-sig") as file:
                original_content = file.read()

            # Log original content for debugging
            logging.debug("Original ISS file content:")
            for i, line in enumerate(original_content.splitlines()):
                logging.debug(f"Line {i + 1}: {line}")

            # Validate original content
            validate_iss_file(original_content, "Original file")
            logging.info("Original ISS file validation passed")

            # Get version information
            new_version = self.version_number['new_version'].version_number
            dev_stage = self.version_number['new_version'].Development_stage
            logging.info(f"New version: {new_version}, Stage: {dev_stage}")

            # Determine output filename based on development stage
            output_base_filename = (
                f"NikonLogHandler_{new_version}.testing" if dev_stage == "testing"
                else f"NikonLogHandler_{new_version}.release"
            )
            logging.info(f"Output filename will be: {output_base_filename}")

            # Create modified content starting with original
            iss_content = original_content

            # Update version numbers
            replacements = [
                (r'AppVersion=[\d\.]+', f'AppVersion={new_version}'),
                (r'#define AppVersion "[\d\.]+"', f'#define AppVersion "{new_version}"'),
                (r'OutputBaseFilename=[^\r\n]+', f'OutputBaseFilename={output_base_filename}')
            ]

            # Apply all replacements
            for pattern, replacement in replacements:
                iss_content = re.sub(pattern, replacement, iss_content)

            # Update Source path for distribution files
            dist_path = Path(__file__).resolve().parent.parent / 'CD' / 'dist' / 'NikonLogHandler'
            dist_path_str = str(dist_path).replace(os.sep, '/')

            # Update the Source path in the .iss file
            source_pattern = r'Source: "[^"]+(/\*")'
            replacement = f'Source: "{dist_path_str}\\1'
            iss_content = re.sub(source_pattern, replacement, iss_content)

            # Validate modified content before writing
            validate_iss_file(iss_content, "Modified content")
            logging.info("Modified ISS file validation passed")

            # Log changes for debugging
            if iss_content != original_content:
                logging.info("Changes made to ISS file:")
                for i, (old_line, new_line) in enumerate(zip(original_content.splitlines(),
                                                             iss_content.splitlines())):
                    if old_line != new_line:
                        logging.info(f"Line {i + 1} changed:")
                        logging.info(f"  Old: {old_line}")
                        logging.info(f"  New: {new_line}")

            # Write updated content without BOM
            with open(self.iss_file_path, "w", encoding="utf-8") as file:
                file.write(iss_content.replace('\ufeff', ''))
            logging.info("Successfully wrote updated ISS file")

            # Final validation of written file
            with open(self.iss_file_path, "r", encoding="utf-8") as file:
                final_content = file.read()

            # Validate final content
            validate_iss_file(final_content, "Final file")
            logging.info("Final ISS file validation passed")

            return True, "Install build file updated successfully"

        except Exception as e:
            error_msg = f"Failed to update install build file: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg)  # Re-raise with the full error message

    def make_commit(self, files_to_commit: list, commit_message: str, tag: str) -> tuple[bool, str]:
        """
        Wrapper for MangeRepo.make_commit to work with thread_runner.

        Args:
            files_to_commit (list): List of files to commit
            commit_message (str): Commit message
            tag (str): Tag name for the commit

        Returns:
            tuple[bool, str]: Success status and message from repo commit operation
        """
        try:
            self.repo.make_commit(files_to_commit, commit_message, tag)
            return True, "Changes committed successfully"
        except Exception as e:
            error_msg = f"Failed to commit and push changes: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    def rollback_changes(self):
        """
        Rollback changes to files that were modified during the build process.
        Uses Git to reset changes to tracked files and removes SharePoint upload if exists.
        """
        try:
            logging.info("Rolling back changes...")

            # Get stored credentials for SharePoint cleanup
            user_credentials = self.credential_manager.get_credentials()

            # Try to delete from SharePoint if credentials are available
            if user_credentials and self.installer_zip_file_path:
                success, message = self.delete_from_sharepoint(
                    user_credentials['sharepoint_username'],
                    user_credentials['password']
                )
                if success:
                    logging.info("Successfully removed file from SharePoint")
                else:
                    logging.warning(f"Failed to remove SharePoint file: {message}")

            # Reset changes to tracked files
            for file_path in self.files_to_commit:
                try:
                    self.repo.repo.git.checkout('--', file_path)
                    logging.info(f"Successfully rolled back changes to {file_path}")
                except git.exc.GitCommandError as e:
                    logging.warning(f"Failed to rollback {file_path}: {str(e)}")

            return True, "Changes successfully rolled back"

        except Exception as e:
            error_msg = f"Failed to rollback changes: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    @staticmethod
    def cleanup_environment():
        """
        Remove the app_clean_python directory, build and dist folders, and specific files
        (requirements_current.txt, build_package_error.log) if they exist.
        """
        # List of items to remove
        items_to_remove = [
            'app_clean_python',  # Folder
            'build',  # Folder
            'dist',  # Folder
            'Output',  # Folder
            'requirements_current.txt',  # File
        ]

        logging.info("Starting cleanup process...")

        for item in items_to_remove:
            if os.path.exists(item):
                if os.path.isdir(item):
                    # If the item is a directory, remove it
                    shutil.rmtree(item)
                    logging.info(f"Folder '{item}' has been removed.")
                elif os.path.isfile(item):
                    # If the item is a file, remove it
                    os.remove(item)
                    logging.info(f"File '{item}' has been removed.")
            else:
                logging.info(f"'{item}' does not exist.")

        logging.info("Cleanup process completed.")

    def create_clean_python_env_non_gui(self, real_time=False):
        """
        Create a python Venv for the build without GUI operations, with detailed logging.
        :param real_time: If True, command output is logged in real-time. If False, output is logged after command completion.
        :return: A boolean indicating success or failure, and a message.
        """
        # Step 1: Remove existing environment
        logging.info("Step 1: Remove existing environment")
        # Remove the existing app_clean_python directory
        if os.path.exists('app_clean_python'):
            shutil.rmtree('app_clean_python')

        # Step 2: Create new virtual environment
        logging.info("Step 2: Create new virtual environment")
        success, message = self.run_command(r'python -m venv app_clean_python', real_time)
        if not success:
            return False, "Failed to create virtual environment"

        # Step 3: Install packages
        logging.info("Step 3: Install packages")
        success, message = self.run_command(r'.\app_clean_python\Scripts\python.exe -m pip install -r ../requirements.txt', real_time)
        if not success:
            return False, "Failed to install required packages"

        # Step 4: Verify installation
        venv_installed_packages_file = os.getcwd() + "\\requirements_current.txt"
        success, message = self.run_command(f'.\\app_clean_python\\Scripts\\python.exe -m pip freeze > {venv_installed_packages_file}', real_time)
        if not success:
            return False, "Failed to list installed packages"

        with open(venv_installed_packages_file, 'r') as file:
            current_installed_packages_list = [package.split('==')[0] for package in file]
        with open("../requirements.txt", 'r') as file:
            requirements_list = [requirement.split('==')[0] for requirement in file]

        if all(requirement in current_installed_packages_list for requirement in requirements_list):
            return True, "venv has all the required packages"
        else:
            missing_packages = [requirement for requirement in requirements_list if requirement not in current_installed_packages_list]
            for package in missing_packages:
                logging.error(f"Missing package: {package}")
            return False, f"Not all required packages are installed. Missing packages: {', '.join(missing_packages)}"

    def create_package_non_gui(self, real_time=False):
        """
        Non-GUI function to create package using PyInstaller.

        :param real_time: how to run the function.
        :return: Tuple (success: bool, output: str)
        """
        try:
            command = f'.\\app_clean_python\\Scripts\\python.exe -m PyInstaller ..\\{self.version_file_perm["product_name"]}.spec -y --log-level WARN'
            success, output = self.run_command(command, real_time)
            if success:
                self.organize_package()
                return True, "Package created successfully!"
            else:
                return False, output
        except Exception as e:
            logging.error(traceback.format_exc())
            return False, str(e)

    def organize_package(self):
        """
        Move files and folders to the root directory
        """
        full_path_to_build_folder = f"dist/{self.version_file_perm['product_name']}"
        internal_path = f"{full_path_to_build_folder}/_internal"

        for file_or_folder in self.files_folders_to_move:
            src = f"{internal_path}/{file_or_folder}"
            dst = f"{full_path_to_build_folder}/{file_or_folder}"
            if os.path.exists(src):
                shutil.move(src, dst)

    def check_package_imported_on_start(self, ):
        """
        Check if NLH mange to import all packages on start
        """
        command = f'{os.getcwd()}\\run_lib_test.bat'
        logging.info(f'program output:\n {os.popen(command).read()}')
        test_list = {}
        with open(f'.\\dist\\{self.version_file_perm["product_name"]}\\testing.log', 'r') as testing_log_reader:
            logging.info(f'Import Test, file Content')
            for test in testing_log_reader.readlines():
                logging.info(f'{test}\n')
                test_list[test.split(":")[0].strip()] = test.split(":")[1].strip()
        if "test_import_lib" in test_list.keys():
            if test_list["test_import_lib"] == "Library import test passed.":
                logging.info(test_list["test_import_lib"])
                os.remove(f'.\\dist\\{self.version_file_perm["product_name"]}\\testing.log')
                return True, "NLH imported test passed"
            else:
                logging.error(test_list["test_import_lib"])
                os.remove(f'.\\dist\\{self.version_file_perm["product_name"]}\\testing.log')
                return False, "NLH imported test Failed"
        else:
            return False, "NLH imported test Failed"

    def create_installer_non_gui(self, real_time=False):
        """
        Function to create Windows installer using Inno Setup.

        :param real_time: Whether to show output in real-time
        :return: Tuple (success: bool, output: str)
        """
        try:
            # Path to Inno Setup Compiler
            iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

            # Check if Inno Setup is installed
            if not os.path.exists(iscc_path):
                raise FileNotFoundError(
                    "Inno Setup is not installed or not found in the expected location. "
                    "Please install Inno Setup from: https://jrsoftware.org/isdl.php"
                )

            # Path to your .iss script (assuming it's in the CD directory)
            iss_script = "nlh_install_builder_config_file.iss"

            # Create Output directory if it doesn't exist
            output_dir = os.path.join(os.path.dirname(iss_script), "Output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Construct the command
            command = f'"{iscc_path}" "{iss_script}"'

            # Run the command using the existing run_command method
            success, output = self.run_command(command, real_time)

            if success:
                self.zip_installer()
                return True, "Installer created successfully!"
            else:
                return False, f"Failed to create installer: {output}"

        except FileNotFoundError as e:
            logging.error(traceback.format_exc())
            return False, str(e)
        except Exception as e:
            logging.error(traceback.format_exc())
            return False, str(e)

    def zip_installer(self):
        """
        Zip the installer .exe file from the Output folder.
        """
        try:
            # Get the Output directory path
            output_dir = Path(__file__).parent / "Output"

            # Find the .exe file in the Output directory
            exe_file = next(output_dir.glob("*.exe"))
            zip_file = output_dir / (exe_file.stem + ".zip")
            self.installer_zip_file_path = zip_file
            # Create zip file
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(exe_file, exe_file.name)

            return True, "Installer zipped successfully!"

        except Exception as e:
            logging.error(traceback.format_exc())
            return False, f"Failed to zip installer: {str(e)}"

    def create_gitea_release(self, user_credential, release_notes: str = "") -> tuple[bool, str]:
        """
        Create a release in Gitea based on current version and branch conditions.

        Args:
            user_credential : user credential
            release_notes (str): Release notes to include in the release

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            # Check branch conditions
            active_branch = self.repo.active_brunch_name
            is_version_pattern = bool(re.match(r'^\d+\.\d+$', active_branch))

            # Only proceed if on Development or version pattern branch
            if not (active_branch == "Development" or is_version_pattern):
                return False, "Release creation skipped: Not on Development or version pattern branch"

            # Get version info
            version = self.version_number['new_version']
            is_pre_release = version.Development_stage == 'testing'

            # Add SharePoint link to release notes
            sharepoint_link = f"[NikonLogHandler_{version.version_number}.{version.Development_stage}]"
            sharepoint_link += f"( https://nikonglobaleu.sharepoint.com/:u:/r/sites/NPE-ESHardware/Nikon%20Log%20Handler/NLH_files/"
            sharepoint_link += f"NikonLogHandler_{version.version_number}.{version.Development_stage}.zip?csf=1&web=1&e=gw91kA)"

            full_release_notes = f"{release_notes}\n\n{sharepoint_link}"

            # Create release using repo function

            success, message = self.repo.create_release_from_tag(
                user_credentials=user_credential,
                tag_name=version.version_number,
                is_pre_release=is_pre_release,
                release_message=full_release_notes
            )

            if success:
                # If successful and it's a release on Development branch, create new branch
                if active_branch == "Development" and not is_pre_release:
                    return self.create_version_branch()

            return success, message

        except Exception as e:
            error_msg = f"Failed to create release: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    def create_version_branch(self) -> tuple[bool, str]:
        """
        Create a new branch based on major.minor version number (x.y) from Development branch.
        Only creates branch if on Development branch and making a release.

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            version = self.version_number['new_version']
            if self.repo.active_brunch_name == "Development" and version.Development_stage == "release":
                # Create branch name using only major and minor version numbers
                new_branch_name = f"{version.major}.{version.minor}"
                logging.info(f"Creating new branch '{new_branch_name}' from Development")

                # Store current development branch reference
                development_branch = self.repo.repo.active_branch

                # Create new branch from current Development state
                new_branch = self.repo.repo.create_head(new_branch_name)

                # Push new branch
                origin = self.repo.repo.remote(name='origin')
                origin.push(new_branch.name, set_upstream=True)
                logging.info(f"Pushed new branch '{new_branch_name}'")

                # Ensure we stay on Development branch
                development_branch.checkout()
                logging.info("Remained on Development branch")

                return True, f"Successfully created and pushed branch '{new_branch_name}' from Development"

            return False, "Branch creation skipped: Conditions not met"

        except Exception as e:
            error_msg = f"Failed to create version branch: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    def initialize_sharepoint_handler(self) -> tuple[bool, str]:
        """
        Initialize SharePoint handler for package builder.

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            sharepoint_url = self.nikon_log_handler_xml.find("./Update_Variables/sharepoint_url").text

            # Create SharePoint handler without auto-authentication
            self.sharepoint_handler = SharePointHandler(sharepoint_url, auto_authenticate=False)

            # Authenticate
            success = self.sharepoint_handler.authenticate()

            if success:
                return True, "SharePoint handler initialized successfully"
            else:
                return False, f"SharePoint authentication failed: {self.sharepoint_handler.authentication_error}"

        except Exception as e:
            error_msg = f"Failed to initialize SharePoint handler: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    @handle_operation("SharePoint upload")
    def upload_to_sharepoint(self) -> tuple[bool, str]:
        """
        Upload the installer zip file to SharePoint using the SharePoint handler.
        """
        try:
            # Check branch conditions
            active_branch = self.repo.active_brunch_name
            is_version_pattern = bool(re.match(r'^\d+\.\d+$', active_branch))

            if not (active_branch == "Development" or is_version_pattern):
                return False, "Upload skipped: Active branch is not 'Development' or version pattern"

            # Check if SharePoint handler is available and authenticated
            if not self.sharepoint_handler or not self.sharepoint_handler.is_authenticated:
                return False, "SharePoint handler not available or not authenticated"

            # Check if installer zip file exists
            if not self.installer_zip_file_path or not os.path.exists(self.installer_zip_file_path):
                return False, "Installer zip file not found"

            # Get SharePoint folder from XML
            sharepoint_folder = self.nikon_log_handler_xml.find("./Update_Variables/sharepoint_url_folder_url").text

            # Upload file using SharePoint handler
            result = self.sharepoint_handler.upload_file(
                sharepoint_folder=sharepoint_folder,
                file_path=str(self.installer_zip_file_path)
            )

            if result.startswith("Successfully"):
                return True, "Upload Complete"
            else:
                return False, f"Upload Failed: {result}"

        except Exception as e:
            error_msg = f"Error uploading to SharePoint: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    @handle_operation("SharePoint file deletion")
    def delete_from_sharepoint(self, sharepoint_username: str, sharepoint_password: str) -> tuple[bool, str]:
        """
        Delete the uploaded file from SharePoint.

        Args:
            sharepoint_username (str): SharePoint username
            sharepoint_password (str): SharePoint password

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            if not self.installer_zip_file_path:
                return False, "No file path available for deletion"

            sharepoint_url = self.nikon_log_handler_xml.find("./Update_Variables/sharepoint_url").text
            sharepoint_folder = self.nikon_log_handler_xml.find("./Update_Variables/sharepoint_url_folder_url").text

            # Get just the filename from the full path
            file_name = os.path.basename(self.installer_zip_file_path)

            # Use the existing no_ssl_verification context
            with no_ssl_verification():
                # Construct SharePoint REST API endpoint for file deletion
                file_url = f"{sharepoint_url}/_api/web/GetFolderByServerRelativeUrl('{sharepoint_folder}')/Files('{file_name}')"

                # Set up headers for SharePoint REST API
                headers = {
                    'Accept': 'application/json;odata=verbose',
                    'Content-Type': 'application/json;odata=verbose',
                    'X-RequestDigest': 'form digest value',
                    'IF-MATCH': '*',
                    'X-HTTP-Method': 'DELETE'
                }

                # Make the delete request
                response = requests.post(
                    file_url,
                    headers=headers,
                    auth=(sharepoint_username, sharepoint_password),
                    verify=False
                )

                if response.status_code in [200, 204]:
                    return True, "Successfully deleted file from SharePoint"
                else:
                    return False, f"Failed to delete file. Status code: {response.status_code}"

        except Exception as e:
            error_msg = f"Failed to delete file from SharePoint: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg


class App(customtkinter.CTk):
    def __init__(self, builder_obj: PackageBuilder):
        super().__init__()
        self.builder_obj = builder_obj
        self.current_credentials = self.builder_obj.credential_manager.get_current_credentials()

        # Initialize SharePoint handler first
        self.initialize_sharepoint_handler()

        # Get current credentials for GUI mode
        if not self.current_credentials:
            messagebox.showerror("Error", "Could not get user credentials")
            self.destroy()
            return

        # Always prompt for password in GUI mode
        max_attempts = 3
        attempts = 0
        while attempts < max_attempts:
            # Create credentials dialog with current Windows/AD credentials
            dialog = CredentialsDialog(self)
            self.wait_window(dialog)
            if not dialog.result:
                messagebox.showerror("Error", "Password is required to continue")
                self.destroy()
                return

            # Verify credentials
            success, message = self.builder_obj.verify_credentials(
                sharepoint_username=dialog.result['sharepoint_username'],
                gitea_username=dialog.result['gitea_username'],
                password=dialog.result['password']
            )

            if success:
                # Store credentials temporarily for this session only
                self.current_credentials = dialog.result
                break
            else:
                attempts += 1
                if attempts >= max_attempts:
                    messagebox.showerror("Error",
                                         f"Failed to verify credentials after {max_attempts} attempts. Exiting.")
                    self.destroy()
                    return
                else:
                    retry = messagebox.askretrycancel("Authentication Error",
                                                      f"{message}\nAttempt {attempts} of {max_attempts}")
                    if not retry:
                        self.destroy()
                        return

        # ===================================
        # ============    GUI    ============
        # ===================================

        # ============ GUI Config ============
        WIDTH = 980
        HEIGHT = 800
        self.title('NLH app builder')
        self.geometry(f'{WIDTH}x{HEIGHT}')
        # self.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.minsize(WIDTH, HEIGHT)
        self.resizable(False, False)  # Disable both horizontal and vertical resizing

        # ============ Main GUI grid config ============
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ============ Information and Parameters ============
        self.sidebar_frame = customtkinter.CTkFrame(self)
        self.sidebar_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.sidebar_frame.grid_columnconfigure((0, 1), weight=0)
        self.sidebar_frame.grid_rowconfigure(0, weight=0)

        # Param Frame
        self.param_frame = customtkinter.CTkFrame(self.sidebar_frame, corner_radius=0, fg_color="transparent")
        self.param_frame.grid(row=0, column=0, sticky='nsew')

        # version program info pane
        self.program_info_frame = customtkinter.CTkFrame(self.param_frame, width=200, corner_radius=0, fg_color="transparent")
        self.program_info_frame.grid(row=1, column=0, sticky='nsew', pady=(15, 5), padx=5)
        self.program_info_frame.grid_columnconfigure(0, weight=1)
        index = 0
        self.program_info_labels = {}
        for parameter_type, value in self.builder_obj.version_file_perm.items():
            self.program_info_labels[parameter_type] = {}
            self.program_info_labels[parameter_type]['label'] = customtkinter.CTkLabel(self.program_info_frame, text=parameter_type.replace('_', ' '),
                                                                                       font=customtkinter.CTkFont(size=12, weight='bold'))
            self.program_info_labels[parameter_type]['label'].grid(row=index, column=0, padx=5, pady=(0, 0), sticky='nsew')
            index += 1
            self.program_info_labels[parameter_type]['value'] = customtkinter.CTkLabel(self.program_info_frame,
                                                                                       width=110,
                                                                                       height=30,
                                                                                       fg_color="yellow" if parameter_type == "Active branch" else "white",
                                                                                       corner_radius=10,
                                                                                       text=value,
                                                                                       font=customtkinter.CTkFont(size=10, weight='bold'))
            self.program_info_labels[parameter_type]['value'].grid(row=index, column=0, padx=5, pady=(0, 5), sticky='nsew')
            index += 1

        # Create a container frame for both panes
        self.lists_container_frame = customtkinter.CTkFrame(master=self.sidebar_frame, corner_radius=0, fg_color="transparent")
        self.lists_container_frame.grid(row=0, column=1, sticky='nsew')
        self.lists_container_frame.grid_rowconfigure(0, weight=0)
        self.lists_container_frame.grid_rowconfigure(1, weight=1)
        self.lists_container_frame.grid_rowconfigure(2, weight=0)
        self.lists_container_frame.grid_rowconfigure(3, weight=1)

        # requirement pane
        self.requirement_label = customtkinter.CTkLabel(master=self.lists_container_frame,
                                                        text='Requirement File',
                                                        font=('', 15, 'bold', 'underline'))
        self.requirement_label.grid(row=0, column=0, sticky='ew', padx=15, pady=(10, 0))

        # Create scrollable frame for requirements with white background
        self.requirement_scroll_frame = customtkinter.CTkScrollableFrame(
            self.lists_container_frame,
            height=200,
            fg_color="white"
        )
        self.requirement_scroll_frame.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 5))

        # Add requirements as labels in the scrollable frame
        for req in self.builder_obj.requirement:
            label = customtkinter.CTkLabel(
                self.requirement_scroll_frame,
                text=req,
                fg_color="white",
                text_color="black"
            )
            label.pack(pady=2, fill='x')

        # files_folders_to_move pane
        self.files_folders_to_move_label = customtkinter.CTkLabel(master=self.lists_container_frame,
                                                                  text='Files Folders To Move',
                                                                  font=('', 15, 'bold', 'underline'))
        self.files_folders_to_move_label.grid(row=2, column=0, sticky='ew', padx=15, pady=(10, 0))

        # Create scrollable frame for files/folders with white background
        self.files_folders_scroll_frame = customtkinter.CTkScrollableFrame(
            self.lists_container_frame,
            height=200,
            fg_color="white"
        )
        self.files_folders_scroll_frame.grid(row=3, column=0, sticky='nsew', padx=15, pady=(0, 5))

        # Add files/folders as labels in the scrollable frame
        for item in self.builder_obj.files_folders_to_move:
            label = customtkinter.CTkLabel(
                self.files_folders_scroll_frame,
                text=str(item[:25]),
                fg_color="white",
                text_color="black"
            )
            label.pack(pady=2, fill='x')

        # ============ running option ============
        self.running_frame = customtkinter.CTkFrame(self)
        self.running_frame.grid(row=0, column=2, sticky='nsew')
        self.running_frame.rowconfigure((0, 1), weight=0)
        self.running_frame.rowconfigure(2, weight=1)
        self.running_frame.grid_columnconfigure(0, weight=1)

        # version number info pane
        self.version_number_frame_back_frame = customtkinter.CTkFrame(self.running_frame, corner_radius=0, fg_color="transparent")
        self.version_number_frame_back_frame.grid_columnconfigure(1, weight=0)
        self.version_number_frame_back_frame.grid_columnconfigure((0, 2), weight=1)
        self.version_number_frame_back_frame.grid(row=0, column=0, sticky='nsew', padx=0, pady=0)

        self.version_number_frame = customtkinter.CTkFrame(self.version_number_frame_back_frame, width=150, corner_radius=0, fg_color="transparent")
        self.version_number_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=1)
        columns = (0,)
        for number in range(1, len(self.builder_obj.version_number)):
            columns += number,
        self.version_number_frame.grid_columnconfigure(columns, weight=1)
        self.version_number_frame.grid_rowconfigure((0, 1, 2), weight=1)
        index = 0
        self.version_number_label = {}
        for parameter_type, value in self.builder_obj.version_number.items():
            self.version_number_label[parameter_type] = {}
            self.version_number_label[parameter_type]['label'] = customtkinter.CTkLabel(self.version_number_frame, text=parameter_type.replace('_', ' '),
                                                                                        font=customtkinter.CTkFont(size=15, weight='bold'))
            self.version_number_label[parameter_type]['label'].grid(row=0, column=index, padx=10, pady=(5, 0))
            self.version_number_label[parameter_type]['version_number'] = customtkinter.CTkLabel(self.version_number_frame,
                                                                                                 width=110,
                                                                                                 height=30,
                                                                                                 fg_color='white',
                                                                                                 corner_radius=10,
                                                                                                 text=value.version_number,
                                                                                                 font=customtkinter.CTkFont(size=10, weight='bold'))
            self.version_number_label[parameter_type]['version_number'].grid(row=1, column=index, padx=10, pady=(0, 10))
            self.version_number_label[parameter_type]['version_type'] = customtkinter.CTkLabel(self.version_number_frame,
                                                                                               width=110,
                                                                                               height=30,
                                                                                               fg_color='white',
                                                                                               corner_radius=10,
                                                                                               text=value.Development_stage,
                                                                                               font=customtkinter.CTkFont(size=10, weight='bold'))
            self.version_number_label[parameter_type]['version_type'].grid(row=2, column=index, padx=10, pady=(0, 10))
            index += 1
        self.version_number_label['new_version']['version_number'].bind('<Button-1>', self.check_manual_version_number_input)
        if self.builder_obj.version_number['new_version'].version_number == '0.0.0.0':
            self.version_number_label['new_version']['version_number'].configure(fg_color='red')

        # button frame
        self.buttons_frame = customtkinter.CTkFrame(self.running_frame)
        self.buttons_frame.grid(row=1, column=0, sticky='nsew', pady=5, padx=5)
        self.buttons_frame.grid_columnconfigure((1, 2), weight=0)
        self.buttons_frame.grid_columnconfigure((0, 3), weight=1)

        # Run button
        self.run_button = customtkinter.CTkButton(
            self.buttons_frame,
            text='Run',
            command=self.toggle_build
        )
        self.run_button.grid(row=0, column=1, sticky='nsew', pady=5, padx=5)
        self.is_building = False

        # Clean env button
        self.cleanup_button = customtkinter.CTkButton(
            self.buttons_frame,
            text='Cleanup Environment',
            command=self.builder_obj.cleanup_environment
        )
        self.cleanup_button.grid(row=0, column=2, sticky='nsew', pady=5, padx=5)

        self.is_debug = customtkinter.StringVar(value="off")
        self.is_debug_switch = customtkinter.CTkSwitch(self.buttons_frame, text="Debug Mode", command=self.is_debug_mode,
                                                       variable=self.is_debug, onvalue="on", offvalue="off")
        self.is_debug_switch.grid(row=1, column=1, sticky='nsew', pady=5, padx=5)

        # make_release_tag
        self.make_release_checkbox = customtkinter.CTkCheckBox(
            self.buttons_frame,
            text="Make Release",
            command=self.toggle_make_release_tag
        )
        self.make_release_checkbox.grid(row=1, column=2, padx=5, pady=(5, 10))

        # ===== Status Pane =====
        self.status_frame = customtkinter.CTkFrame(self.running_frame, corner_radius=0, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, sticky='nsew')
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.is_commit_needed = customtkinter.CTkLabel(master=self.status_frame,
                                                       text='Commit Needed',
                                                       height=17, font=('Roboto Medium', 20),
                                                       bg_color='white')
        self.is_commit_needed.grid(row=0, column=0, sticky='nsew', pady=2, padx=5)
        if not self.builder_obj.repo.file_not_committed:
            self.is_commit_needed.configure(fg_color='green')
        else:
            self.is_commit_needed.configure(fg_color='red')

        self.is_debug_status = customtkinter.CTkLabel(master=self.status_frame,
                                                      text='Debug Mode',
                                                      height=17, font=('Roboto Medium', 20),
                                                      bg_color='white')
        self.is_debug_status.grid(row=1, column=0, sticky='nsew', pady=2, padx=5)
        if self.is_debug.get() == 'off':
            self.is_debug_status.configure(fg_color='transparent')
        else:
            self.is_debug_status.configure(fg_color='red')
        self.spec_file_update_status = CustomFrame(master=self.status_frame, label_text='Spec_file_Updated', fg_color="white")
        self.spec_file_update_status.grid(row=2, column=0, sticky='nsew', pady=2, padx=5)
        self.is_python_venv_installed = CustomFrame(master=self.status_frame, label_text='Python Venv', fg_color="white")
        self.is_python_venv_installed.grid(row=3, column=0, sticky='nsew', pady=2, padx=5)
        self.is_build_dist_done = CustomFrame(master=self.status_frame, label_text='Build Dist', fg_color="white")
        self.is_build_dist_done.grid(row=4, column=0, sticky='nsew', pady=2, padx=5)
        self.is_dist_import_pass = CustomFrame(master=self.status_frame, label_text='Import Test', fg_color="white")
        self.is_dist_import_pass.grid(row=5, column=0, sticky='nsew', pady=2, padx=5)
        self.is_make_install_file_status = CustomFrame(master=self.status_frame, label_text='Install file maker', fg_color="white")
        self.is_make_install_file_status.grid(row=6, column=0, sticky='nsew', pady=2, padx=5)
        self.is_upload_to_sharepoint_status = CustomFrame(master=self.status_frame, label_text='Upload to Sharepoint', fg_color="white")
        self.is_upload_to_sharepoint_status.grid(row=7, column=0, sticky='nsew', pady=2, padx=5)
        self.is_committed_status = CustomFrame(master=self.status_frame, label_text='Changes Committed', fg_color="white")
        self.is_committed_status.grid(row=8, column=0, sticky='nsew', pady=2, padx=5)
        self.is_release_created_status = CustomFrame(master=self.status_frame, label_text='Release Created', fg_color="white")
        self.is_release_created_status.grid(row=9, column=0, sticky='nsew', pady=2, padx=5)
        self.is_branch_created_status = CustomFrame(master=self.status_frame, label_text='Branch Created', fg_color="white")
        self.is_branch_created_status.grid(row=10, column=0, sticky='nsew', pady=2, padx=5)
        self.update_make_release_checkbox_state()
        self.update_status_colors()

        # Add console frame
        self.console_frame = ConsoleFrame(self)
        self.console_frame.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=5, padx=5)
        self.running_frame.rowconfigure(3, weight=1)  # Make console frame expandable

        # # Optional: Add clear button for console
        # self.clear_console_button = customtkinter.CTkButton(
        #     self.buttons_frame,
        #     text='Clear Console',
        #     command=self.console_frame.clear
        # )
        # self.clear_console_button.grid(row=0, column=3, sticky='nsew', pady=5, padx=5)

        self.update_debug_mode_based_on_commits()

        # Create the context menu once during initialization
        self.context_menu = tkinter.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Turn on resizable window",
            command=self.toggle_resizable
        )

        # Bind right-click to all frames and the main window
        self.bind('<Button-3>', self.show_context_menu)

        # Bind to all frames
        for widget in [self.sidebar_frame, self.running_frame, self.status_frame,
                       self.console_frame, self.buttons_frame]:
            widget.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        """Display the context menu and update its label"""
        is_resizable = self.resizable()[0]
        menu_text = "Turn off resizable window" if is_resizable else "Turn on resizable window"

        # Update the existing menu item
        self.context_menu.entryconfigure(0, label=menu_text)

        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def toggle_resizable(self):
        """Toggle window resizable state"""
        current_state = self.resizable()
        new_state = not current_state[0]
        self.resizable(new_state, new_state)

        if new_state:
            self.minsize(980, 800)  # Set minimum size when resizable
        else:
            self.geometry('980x800')  # Reset to default size when not resizable

    def update_debug_mode_based_on_commits(self):
        """Update debug mode and UI elements based on commit status"""
        if self.builder_obj.repo.file_not_committed:
            # Enable debug mode
            self.is_debug.set("on")
            # Disable the debug switch
            self.is_debug_switch.configure(state="disabled")
            # Disable make release checkbox
            self.make_release_checkbox.configure(state="disabled")
            # Update status colors
            self.is_debug_mode()
            # Update the commit needed indicator
            self.is_commit_needed.configure(fg_color='red')
        else:
            # Enable the debug switch
            self.is_debug_switch.configure(state="normal")
            # Update the commit needed indicator
            self.is_commit_needed.configure(fg_color='green')
            # Update make release checkbox state
            self.update_make_release_checkbox_state()

    def mark_frames_as_stopped(self):
        """Mark all custom frames as stopped"""
        frames = [
            self.spec_file_update_status,
            self.is_python_venv_installed,
            self.is_build_dist_done,
            # ... add all your custom frames here ...
        ]

        for frame in frames:
            if isinstance(frame, CustomFrame):
                frame.finish_with_label("Stopped", "red")

    def toggle_build(self):
        """Toggle between running and stopping the build"""
        if not self.is_building:
            # Start build
            self.is_building = True
            self.run_button.configure(text="Stop", fg_color="red")
            self.cleanup_button.configure(state="disabled")  # Disable cleanup during build
            self.builder_obj.stop_flag = False
            self.build_package()
        else:
            # Stop build
            self.run_button.configure(text="Stopping...", state="disabled")
            self.builder_obj.stop_build()

    def is_debug_mode(self):
        """change the status label of debug mode"""
        if self.is_debug.get() == 'off':
            self.is_debug_status.configure(fg_color='transparent')
        else:
            self.is_debug_status.configure(fg_color='red')
        self.update_status_colors()  # Update colors when debug mode changes

    def update_status_colors(self):
        """Update colors of status items based on what will run"""
        is_debug = self.is_debug.get() == "on"
        is_development = self.builder_obj.repo.active_brunch_name == "Development"
        has_uncommitted = bool(self.builder_obj.repo.file_not_committed)
        is_version_pattern = bool(re.match(r'^\d+\.\d+$', self.builder_obj.repo.active_brunch_name))

        # Base conditions for release-related operations
        will_spec_file = (
                not is_debug and  # Not in debug mode
                not has_uncommitted  # No uncommitted changes
        )

        # Base conditions for release-related operations
        will_run_release_operations = (
                (is_development or is_version_pattern) and  # Must be on Development or version pattern branch
                not is_debug and  # Not in debug mode
                not has_uncommitted  # No uncommitted changes
        )

        # Specific condition for branch creation
        will_create_branch = (
                is_development and  # Must be specifically on Development branch
                not is_debug and  # Not in debug mode
                not has_uncommitted and  # No uncommitted changes
                self.builder_obj.make_release_tag and  # Make release must be checked
                self.builder_obj.version_number['new_version'].Development_stage == "release"  # Must be a release version
        )

        # Define conditions for each status item
        status_items = {
            self.spec_file_update_status: will_spec_file,
            self.is_python_venv_installed: True,  # Always runs
            self.is_build_dist_done: True,  # Always runs
            self.is_dist_import_pass: True,  # Always runs
            self.is_make_install_file_status: True,  # Always runs
            self.is_upload_to_sharepoint_status: will_run_release_operations,
            self.is_committed_status: will_run_release_operations,
            self.is_release_created_status: will_run_release_operations,
            self.is_branch_created_status: will_create_branch
        }

        # Update colors with text only for items that won't run
        for status_item, will_run in status_items.items():
            if will_run:
                status_item.configure(fg_color="white")
                status_item.finish_with_label(text="", color="white")
            else:
                status_item.configure(fg_color="yellow")
                status_item.finish_with_label(text="Not running", color="yellow")

    def update_make_release_checkbox_state(self):
        """
        Update the checkbox state based on branch conditions and commit status.
        The checkbox should be enabled when:
        1. On Development branch or version pattern branch AND
        2. Either in debug mode OR no uncommitted changes
        """
        active_branch = self.builder_obj.repo.active_brunch_name
        is_version_pattern = bool(re.match(r'^\d+\.\d+$', active_branch))
        is_debug_mode = self.is_debug.get() == "on"
        has_uncommitted_changes = bool(self.builder_obj.repo.file_not_committed)

        # Enable checkbox if:
        # (on Development or version branch) AND (in debug mode OR no uncommitted changes)
        should_enable = (active_branch == "Development" or is_version_pattern) and \
                        (is_debug_mode or not has_uncommitted_changes)

        if should_enable:
            self.make_release_checkbox.configure(state="normal")
            self.make_release_checkbox.configure(
                text="Make Release"
            )

        else:
            self.make_release_checkbox.configure(state="disabled")
            # Uncheck the box when disabled
            self.make_release_checkbox.deselect()
            self.builder_obj.make_release_tag = False

            # Set appropriate disabled message
            if not (active_branch == "Development" or is_version_pattern):
                disable_reason = "Make Release"
            elif has_uncommitted_changes and not is_debug_mode:
                disable_reason = "Make Release"
            else:
                disable_reason = "Make Release"

            self.make_release_checkbox.configure(text=disable_reason)

    def update_commit_status(self):
        """
        Update UI elements that depend on commit status
        """
        if not self.builder_obj.repo.file_not_committed:
            self.is_commit_needed.configure(fg_color='green')
            self.is_debug_switch.configure(state="normal")
            # Allow debug mode to be toggled off
            if self.is_debug.get() == "on":
                self.is_debug_switch.configure(state="normal")
        else:
            self.is_commit_needed.configure(fg_color='red')
            # Force debug mode on and disable the switch
            self.is_debug.set("on")
            self.is_debug_switch.configure(state="disabled")

        # Update make release checkbox state
        self.update_make_release_checkbox_state()

    def update_gui_based_on_commit(self, success: bool, message: str):
        """
        Updates the GUI elements based on the success or failure of the commit operation.
        """
        if success:
            self.is_committed_status.finish_with_label(text="Committed", color='green')
            self.builder_obj.step_done = "done"
        else:
            self.is_committed_status.finish_with_label(text="Error", color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    def toggle_make_release_tag(self):
        """
        Handle checkbox toggle with branch condition check and update status colors
        for branch creation based on all conditions.
        """
        active_branch = self.builder_obj.repo.active_brunch_name
        is_version_pattern = bool(re.match(r'^\d+\.\d+$', active_branch))
        is_debug_mode = self.is_debug.get() == "on"
        has_uncommitted_changes = bool(self.builder_obj.repo.file_not_committed)

        if active_branch == "Development" or is_version_pattern:
            self.builder_obj.make_release_tag = self.make_release_checkbox.get()

            # Update version number
            new_version = self.builder_obj.auto_create_new_version_number()
            self.builder_obj.version_number['new_version'] = new_version

            # Update GUI to show new version
            self.version_number_label['new_version']['version_number'].configure(
                text=new_version.version_number
            )
            self.version_number_label['new_version']['version_type'].configure(
                text=new_version.Development_stage
            )

            # Update branch creation status color based on all conditions
            will_create_branch = (
                    active_branch == "Development" and  # Must be on Development branch
                    self.builder_obj.make_release_tag and  # Make release must be checked
                    not is_debug_mode and  # Not in debug mode
                    not has_uncommitted_changes and  # No uncommitted changes
                    new_version.Development_stage == "release"  # Must be a release version
            )

            # Update status colors
            if hasattr(self, 'is_branch_created_status'):
                self.is_branch_created_status.configure(
                    fg_color="yellow" if will_create_branch else "white"
                )

            # Update all status colors as other conditions might have changed
            self.update_status_colors()
        else:
            # If conditions aren't met, ensure checkbox is disabled and unchecked
            self.make_release_checkbox.deselect()
            self.make_release_checkbox.configure(state="disabled")
            self.builder_obj.make_release_tag = False

            # Ensure branch creation status is white
            if hasattr(self, 'is_branch_created_status'):
                self.is_branch_created_status.configure(fg_color="white")

    def check_manual_version_number_input(self, arg):
        """
        check if manual version number input is valid
        :param arg:
        """
        try:
            dialog = customtkinter.CTkInputDialog(text="Type in a version number:", title=" New version number")
            manual_version_number = VersionNumber(f'{dialog.get_input()}.{self.builder_obj.version_number["new_version"].Development_stage}')
            if manual_version_number.version_number < self.builder_obj.version_number["xml_version"].version_number:
                tkinter.messagebox.showerror('error', "New Version Number can't be lower then the XML version")
            else:
                self.builder_obj.version_number["new_version"] = manual_version_number
                self.version_number_label['new_version']['version_number'].configure(text=self.builder_obj.version_number["new_version"].version_number)
                self.focus()
                self.version_number_label['new_version']['version_number'].configure(fg_color='white')
                self.run_button.configure(state='normal')
        except ValueError as exception:
            tkinter.messagebox.showerror('error', str(exception))

    def update_gui_based_on_spec_file_status(self, success, message):
        """
        Updates the GUI elements based on the success or failure of the VENV creation.
        :param success: A boolean indicating if the VENV creation was successful.
        :param message: A message to display or log.
        """
        if success:
            # Update GUI for success
            self.spec_file_update_status.finish_with_label(text=message.split(',')[0], color='green')
            self.builder_obj.step_done = "done"
        else:
            # Update GUI for failure
            self.spec_file_update_status.finish_with_label(text="Error", color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    def update_gui_based_on_venv_creation(self, success, message):
        """
        Updates the GUI elements based on the success or failure of the VENV creation.
        :param success: A boolean indicating if the VENV creation was successful.
        :param message: A message to display or log.
        """
        if success:
            # Update GUI for success
            self.is_python_venv_installed.finish_with_label(text=message, color='green')
            self.builder_obj.step_done = "done"
        else:
            # Update GUI for failure
            self.is_python_venv_installed.finish_with_label(text=message, color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    def update_crate_package_gui_status(self, success, message):
        """
        GUI method to handle package creation. It calls a non-GUI function and updates the GUI based on the result.
        """
        if success:
            # GUI update for success
            self.is_build_dist_done.finish_with_label(text=message, color='green')
            self.builder_obj.step_done = "done"
        else:
            # GUI update for failure or error
            self.is_build_dist_done.finish_with_label(text=message, color='red')
            self.builder_obj.step_done = "error"
        self.update()  # Assuming this method refreshes the GUI
        logging.info(message)

    def update_package_imported_on_start_status(self, success, message):
        """
        Updates the GUI elements based on the success or failure of the VENV creation.
        :param success: A boolean indicating if the VENV creation was successful.
        :param message: A message to display or log.
        """
        if success:
            # Update GUI for success
            self.is_dist_import_pass.finish_with_label(text=message, color='green')
            self.builder_obj.step_done = "done"
        else:
            # Update GUI for failure
            self.is_dist_import_pass.finish_with_label(text="Error", color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    def update_gui_based_on_create_installer(self, success, message):
        """
        GUI method to handle package creation. It calls a non-GUI function and updates the GUI based on the result.
        """
        if success:
            # GUI update for success
            self.is_make_install_file_status.finish_with_label(text=message, color='green')
            self.builder_obj.step_done = "done"
        else:
            # GUI update for failure or error
            self.is_make_install_file_status.finish_with_label(text=message, color='red')
            self.builder_obj.step_done = "error"
        self.update()  # Assuming this method refreshes the GUI
        logging.info(message)

    def initialize_sharepoint_handler(self):
        """
        Initialize SharePoint handler in background thread.
        """

        def create_and_authenticate_handler():
            """Function to run in background thread"""
            success, message = self.builder_obj.initialize_sharepoint_handler()
            return success, message

        def gui_callback(*args):
            """Callback when SharePoint initialization is complete"""
            gui_success = None
            gui_message = None
            if len(args) == 2:
                # Two arguments: success, message
                gui_success, gui_message = args
            elif len(args) == 1:
                # One argument: treat as message, assume success
                gui_success = True
                gui_message = str(args[0])

            if gui_success:
                logging.info("SharePoint handler initialized successfully")
            else:
                logging.error(f"SharePoint handler initialization failed: {gui_message}")

        # Run SharePoint initialization in background
        thread_runner(self, create_and_authenticate_handler, gui_callback)

    def update_gui_based_on_sharepoint_upload(self, success: bool, message: str):
        """
        Updates the GUI elements based on the success or failure of the SharePoint upload.
        """
        if success:
            self.is_upload_to_sharepoint_status.finish_with_label(text=message, color='green')
            self.builder_obj.step_done = "done"
        else:
            self.is_upload_to_sharepoint_status.finish_with_label(text="Error", color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    def upload_to_sharepoint(self):
        """
        Handles the SharePoint upload process using the SharePoint handler.
        """
        # Check if SharePoint handler is available
        if not self.builder_obj.sharepoint_handler or not self.builder_obj.sharepoint_handler.is_authenticated:
            self.is_upload_to_sharepoint_status.finish_with_label(text="Not authenticated", color='red')
            self.builder_obj.step_done = "error"
            return

        # Start the upload progress indication
        self.is_upload_to_sharepoint_status.run()

        # Upload to SharePoint using thread
        thread_runner(
            master=self,
            func=self.builder_obj.upload_to_sharepoint,
            gui_callback=self.update_gui_based_on_sharepoint_upload,
            args=()  # No credentials needed - using SharePoint handler
        )

    def get_release_notes(self) -> str:
        """
        Create and display a dialog for entering and previewing release notes.

        This function creates a modal dialog window with two main sections:
        1. Left side: Entry fields for release notes with line numbers and remove buttons
        2. Right side: Real-time preview of how the notes will appear

        Features:
        - Dynamic line numbering
        - Real-time preview updates
        - Scrollable entry and preview areas
        - Add/Remove entry functionality
        - Modal dialog (stays on top)
        - Centered on screen

        Returns:
            str: Formatted release notes with line numbers, or empty string if cancelled
                 Format example:
                 "1. First note
                  2. Second note
                  3. Third note"
        """
        # Create and configure the main dialog window
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Release Notes")
        dialog.geometry("500x300")
        dialog.resizable(False, False)

        # Make dialog stay on top and modal
        dialog.transient(self)
        dialog.focus_set()
        dialog.grab_set()
        dialog.attributes('-topmost', True)

        def keep_on_top():
            """Ensure dialog stays on top of other windows"""
            if dialog.winfo_exists():
                dialog.lift()
                dialog.after(100, keep_on_top)

        keep_on_top()

        # List to store entry widgets for managing line numbers and content
        entries = []

        def update_preview(*args):
            """
            Update the preview text box with numbered entries.
            Only includes non-empty lines.
            """
            preview_text = ""
            for i, entry in enumerate(entries, 1):
                text = entry.get().strip()
                if text:  # Only add non-empty lines
                    preview_text += f"{i}. {text}\n"
            preview_textbox.configure(state="normal")
            preview_textbox.delete("1.0", "end")
            preview_textbox.insert("1.0", preview_text)
            preview_textbox.configure(state="disabled")
            preview_textbox.yview_moveto(0)  # Scroll to top

        def add_entry():
            """
            Add a new entry row with line number, entry field, and remove button.
            Also manages the position of the add button.
            """
            # Remove existing add button if present
            if hasattr(scroll_frame, 'add_btn'):
                scroll_frame.add_btn.destroy()

            # Create frame for new entry
            frame = customtkinter.CTkFrame(scroll_frame, fg_color="transparent")
            frame.pack(fill='both', padx=5, pady=(0, 5))

            # Container for entry components
            container = customtkinter.CTkFrame(frame, fg_color="transparent")
            container.pack(fill='both', expand=True)

            # Line number label
            line_label = customtkinter.CTkLabel(
                container,
                text=f"{len(entries) + 1}.",
                width=25,
                font=("Roboto Medium", 12)
            )
            line_label.pack(side='left', padx=(5, 2))

            # Entry field
            entry = customtkinter.CTkEntry(
                container,
                height=28,
                font=("Roboto", 12)
            )
            entry.pack(side='left', padx=2, fill='x', expand=True)
            entry.bind('<KeyRelease>', update_preview)
            entries.append(entry)

            # Remove button
            remove_btn = customtkinter.CTkButton(
                container,
                text="✕",
                width=28,
                height=28,
                font=("Roboto Medium", 12),
                command=lambda: remove_entry(frame, entry)
            )
            remove_btn.pack(side='left', padx=(5, 0))

            # Add button below the new entry
            scroll_frame.add_btn = customtkinter.CTkButton(
                scroll_frame,
                text="+",
                width=28,
                height=28,
                font=("Roboto Medium", 14),
                command=add_entry
            )
            scroll_frame.add_btn.pack(padx=5, pady=(0, 5))

        def remove_entry(frame, entry):
            """
            Remove an entry and update line numbers.
            Ensures at least one entry remains.

            Args:
                frame: The frame containing the entry to remove
                entry: The entry widget to remove
            """
            entries.remove(entry)
            frame.destroy()

            # Update remaining line numbers
            for i, child in enumerate(scroll_frame.winfo_children()[:-1], 1):
                if isinstance(child, customtkinter.CTkFrame):
                    number_label = child.winfo_children()[0].winfo_children()[0]
                    number_label.configure(text=f"{i}.")

            update_preview()

            # Ensure at least one entry exists
            if not entries:
                add_entry()

        def get_notes():
            """
            Collect and format all non-empty entries.
            Closes the dialog when done.
            """
            notes = []
            for i, entry in enumerate(entries, 1):
                text = entry.get().strip()
                if text:  # Only add non-empty lines
                    notes.append(f"{i}. {text}")
            dialog.notes = "\n".join(notes)
            dialog.destroy()

        # Create main container with grid layout
        container = customtkinter.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill='both', expand=True, padx=10, pady=5)
        container.grid_columnconfigure((0, 1), weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Left side - Entry fields
        left_frame = customtkinter.CTkFrame(container)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        entries_label = customtkinter.CTkLabel(
            left_frame,
            text="Enter Release Notes:",
            font=('Roboto Medium', 13)
        )
        entries_label.grid(row=0, column=0, pady=5)

        scroll_frame = customtkinter.CTkScrollableFrame(left_frame)
        scroll_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Right side - Preview (modified section)
        right_frame = customtkinter.CTkFrame(container)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        right_frame.grid_rowconfigure(1, weight=1)  # Make preview area expand
        right_frame.grid_columnconfigure(0, weight=1)

        preview_label = customtkinter.CTkLabel(
            right_frame,
            text="Preview:",
            font=('Roboto Medium', 13)
        )
        preview_label.grid(row=0, column=0, pady=5)

        # Preview textbox directly in right_frame (removed scrollable frame)
        preview_textbox = customtkinter.CTkTextbox(
            right_frame,
            wrap='word',
            state="disabled",
            font=("Roboto", 12)
        )
        preview_textbox.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Bottom button frame
        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill='x', padx=15, pady=10)

        # Centered OK button
        ok_btn = customtkinter.CTkButton(
            button_frame,
            text="OK",
            width=100,
            height=32,
            font=("Roboto Medium", 12),
            command=get_notes
        )
        ok_btn.pack(side='top', anchor='center')

        # Add initial entry
        add_entry()

        # Center dialog on screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        # Initialize return value and wait for dialog
        dialog.notes = ""
        dialog.wait_window()

        return dialog.notes

    def update_gui_based_on_release_creation(self, success: bool, message: str):
        """
        Updates the GUI elements based on the success or failure of the release creation.
        """
        if success:
            self.is_release_created_status.finish_with_label(text="Release Created", color='green')
            self.builder_obj.step_done = "done"
        else:
            self.is_release_created_status.finish_with_label(text="Error", color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    # def create_release(self):
    #     """
    #     Create a release with user-provided release notes.
    #     """
    #     try:
    #         # Get release notes from user
    #         release_notes = self.get_release_notes()
    #
    #         # Create release
    #         success, message = self.builder_obj.create_gitea_release(release_notes)
    #
    #         if success:
    #             messagebox.showinfo("Success", "Release created successfully")
    #         else:
    #             messagebox.showerror("Error", f"Failed to create release: {message}")
    #
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Error creating release: {str(e)}")

    def update_gui_based_on_branch_creation(self, success: bool, message: str):
        """
        Updates the GUI elements based on the success or failure of the branch creation.
        """
        if success:
            self.is_branch_created_status.finish_with_label(text="Branch Created", color='green')
            self.builder_obj.step_done = "done"
        else:
            self.is_branch_created_status.finish_with_label(text="Error", color='red')
            self.builder_obj.step_done = "error"
        logging.info(message)
        self.update()

    def reset_custom_frames(self):
        """Reset all custom frames to their initial state"""
        # Status frames
        frames_to_reset = [
            self.spec_file_update_status,
            self.is_python_venv_installed,
            self.is_build_dist_done,
            self.is_dist_import_pass,
            self.is_make_install_file_status,
            self.is_upload_to_sharepoint_status,
            self.is_release_created_status,
            self.is_branch_created_status,
            self.is_committed_status
        ]

        for frame in frames_to_reset:
            if isinstance(frame, CustomFrame):
                # Only show "Not running" for frames with yellow background
                if frame.cget("fg_color") == "yellow":
                    frame.finish_with_label(text="Not running", color="yellow")
                else:
                    frame.finish_with_label(text="", color="white")

    def build_package(self):
        """
        Main function to build the NLH package.
        """
        logging.info("Starting Package Build Process")
        self.reset_custom_frames()
        self.update_status_colors()

        try:
            # Step 0: Verify/Request Credentials
            if not self.current_credentials:
                raise Exception("Credentials are required to continue")

            # Step 1: Clean up environment
            logging.info("Cleaning up build environment")
            self.builder_obj.cleanup_environment()

            # Check if running in production mode (not debug) and no uncommitted changes
            if self.is_debug.get() == "off" and not self.builder_obj.repo.file_not_committed:
                # Step 2: Update version information
                logging.info("Updating version information")
                self.builder_obj.update_version_xml_handler()

                # Step 3: Update build configuration files
                logging.info("Updating build configuration files")
                self.builder_obj.update_install_build_file()

                # Step 4: Check and update spec file
                logging.info("Checking and updating spec file")
                self.builder_obj.step_done = False
                self.spec_file_update_status.run()

                thread_runner(
                    master=self,
                    func=self.builder_obj.check_and_update_spec,
                    gui_callback=self.update_gui_based_on_spec_file_status,
                    args=()
                )

                # Wait for spec file update to complete
                while not self.builder_obj.step_done:
                    self.update()
                if self.builder_obj.step_done == 'error':
                    raise Exception('Failed to update spec file')

                if self.builder_obj.stop_flag:
                    self.spec_file_update_status.finish_with_label(text='Stopped', color='red')
                    raise Exception("Build stopped by user")

            # Step 5: Create version file
            logging.info("Creating version file")
            self.builder_obj.make_version_file()

            # Step 6: Set up Python virtual environment
            logging.info("Creating Python virtual environment")
            self.builder_obj.step_done = False
            self.is_python_venv_installed.run()

            thread_runner(
                master=self,
                func=self.builder_obj.create_clean_python_env_non_gui,
                gui_callback=self.update_gui_based_on_venv_creation,
                args=(True,)
            )

            # Wait for venv creation to complete
            while not self.builder_obj.step_done:
                self.update()
            if self.builder_obj.step_done == 'error':
                raise Exception('Failed to create Python virtual environment')

            if self.builder_obj.stop_flag:
                self.is_python_venv_installed.finish_with_label(text='Stopped', color='red')
                raise Exception("Build stopped by user")

            # Step 7: Create executable package
            logging.info("Creating executable package")
            self.builder_obj.step_done = False
            self.is_build_dist_done.run()

            thread_runner(
                master=self,
                func=self.builder_obj.create_package_non_gui,
                gui_callback=self.update_crate_package_gui_status,
                args=(True,)
            )

            # Wait for package creation to complete
            while not self.builder_obj.step_done:
                self.update()
            if self.builder_obj.step_done == 'error':
                raise Exception('Failed to create package')

            if self.builder_obj.stop_flag:
                self.is_build_dist_done.finish_with_label(text='Stopped', color='red')
                raise Exception("Build stopped by user")

            # Step 8: Test package imports
            logging.info("Testing package imports")
            self.builder_obj.step_done = False
            self.is_dist_import_pass.run()

            thread_runner(
                master=self,
                func=self.builder_obj.check_package_imported_on_start,
                gui_callback=self.update_package_imported_on_start_status,
                args=()
            )

            # Wait for import test to complete
            while not self.builder_obj.step_done:
                self.update()
            if self.builder_obj.step_done == 'error':
                raise Exception('Package import test failed')
            if self.builder_obj.stop_flag:
                self.is_dist_import_pass.finish_with_label(text='Stopped', color='red')
                raise Exception("Build stopped by user")

            # Step 9: Create installer
            logging.info("Creating installer")
            self.builder_obj.step_done = False
            self.is_make_install_file_status.run()

            thread_runner(
                master=self,
                func=self.builder_obj.create_installer_non_gui,
                gui_callback=self.update_gui_based_on_create_installer,
                args=()
            )

            # Wait for installer creation to complete
            while not self.builder_obj.step_done:
                self.update()
            if self.builder_obj.step_done == 'error':
                raise Exception('Failed to create installer')

            if self.builder_obj.stop_flag:
                self.is_make_install_file_status.finish_with_label(text='Stopped', color='red')
                raise Exception("Build stopped by user")

            # Production mode specific steps
            if self.is_debug.get() == "off" and not self.builder_obj.repo.file_not_committed:
                # Step 10: Upload to SharePoint
                logging.info("Uploading to SharePoint")
                self.builder_obj.step_done = False
                self.upload_to_sharepoint()

                # Wait for upload to complete
                while not self.builder_obj.step_done:
                    self.update()
                if self.builder_obj.step_done == 'error':
                    raise Exception('Failed to upload to SharePoint')

                if self.builder_obj.stop_flag:
                    self.is_upload_to_sharepoint_status.finish_with_label(text='Stopped', color='red')
                    raise Exception("Build stopped by user")

                self.run_button.configure(text="No Stop", state="disabled")

                # Step 11: Commit changes to Development branch first
                logging.info("Committing changes to Development branch")
                self.builder_obj.step_done = False
                self.is_committed_status.run()

                thread_runner(
                    master=self,
                    func=self.builder_obj.make_commit,
                    gui_callback=self.update_gui_based_on_commit,
                    args=(
                        self.builder_obj.files_to_commit,
                        f"{self.builder_obj.version_number['new_version'].Development_stage} {self.builder_obj.version_number['new_version'].version_number}",
                        self.builder_obj.version_number['new_version'].version_number
                    )
                )

                # Wait for commit to complete
                while not self.builder_obj.step_done:
                    self.update()
                if self.builder_obj.step_done == 'error':
                    raise Exception('Failed to commit changes')

                # Step 12: Create Release
                logging.info("Creating release")
                self.builder_obj.step_done = False
                self.is_release_created_status.run()

                # Get release notes and create release
                release_notes = self.get_release_notes()
                thread_runner(
                    master=self,
                    func=self.builder_obj.create_gitea_release,
                    gui_callback=self.update_gui_based_on_release_creation,
                    args=(self.current_credentials, release_notes,)
                )

                # Wait for release creation to complete
                while not self.builder_obj.step_done:
                    self.update()
                if self.builder_obj.step_done == 'error':
                    raise Exception('Failed to create release')

                # Step 13: Create and push new branch if on Development and making a release
                if (self.builder_obj.repo.active_brunch_name == "Development" and
                        self.builder_obj.version_number['new_version'].Development_stage == "release"):

                    logging.info("Creating new branch")
                    self.builder_obj.step_done = False
                    self.is_branch_created_status.run()

                    thread_runner(
                        master=self,
                        func=self.builder_obj.create_version_branch,
                        gui_callback=self.update_gui_based_on_branch_creation,
                        args=()
                    )

                    # Wait for branch creation to complete
                    while not self.builder_obj.step_done:
                        self.update()
                    if self.builder_obj.step_done == 'error':
                        logging.warning("Branch creation failed but continuing with build")
                    else:
                        logging.info("New branch created and pushed successfully")

            # Step 14: Show completion message
            logging.info("Build process completed successfully")
            tkinter.messagebox.showinfo('Build Status', 'Package Build Complete')

        except Exception as e:
            error_message = str(e)
            logging.error(f"Build failed: {error_message}")

            # Rollback changes if we modified files
            if self.is_debug.get() == "off" and not self.builder_obj.repo.file_not_committed:
                try:
                    rollback_success, rollback_message = self.builder_obj.rollback_changes()
                    if rollback_success:
                        logging.info("Changes have been rolled back")
                        # Update SharePoint status if it was uploaded
                        if hasattr(self, 'is_upload_to_sharepoint_status'):
                            self.is_upload_to_sharepoint_status.finish_with_label(
                                text="Rolled back",
                                color="yellow"
                            )
                    else:
                        logging.error(f"Failed to roll back changes: {rollback_message}")
                except Exception as rollback_error:
                    logging.error(f"Error during rollback: {str(rollback_error)}")

            # Log the full traceback
            logging.error(traceback.format_exc())
            tkinter.messagebox.showerror('Build Error', error_message)

        finally:
            # Reset button states
            self.is_building = False
            self.run_button.configure(text="Run", fg_color="blue", state="normal")
            self.cleanup_button.configure(state="normal")  # Re-enable cleanup button


class VersionNumber:
    """
    split version number to component can expect format x.y.z or x.y.z.str or x.y.z.n or x.y.z.n.str
    """

    def __init__(self, version_str: str):
        self._version: list[Union[str, int]] = []
        _version_list = version_str.split(".")
        if len(_version_list) < 3 or len(_version_list) > 5:
            raise ValueError(f'Version number need to be on the following format "x.y.z" or "x.y.z.str" or "x.y.z.n" or "x.y.z.n.str" got "{version_str}" instead')
        else:
            for index, number in enumerate(_version_list):
                if index < 3:
                    if number.isdigit():
                        self._version.append(number)
                    else:
                        raise ValueError(f'Version number need to start with following formt number.number1.number2 "{version_str}" instead')
                elif index == 3:
                    if number.isdigit():
                        self._version.append(number)
                    else:
                        if number == 'release':
                            self._version.append(0)
                            self._version.append('release')
                        else:
                            self._version.append(0)
                            self._version.append('testing')
                elif index == 4:
                    self._version.append(number)
            if len(self._version) == 3:
                self._version.append(0)
                self._version.append('release')
            if len(self._version) == 4:
                self._version.append('testing')

    @property
    def major(self):
        """
        Get the major version number.

        Returns:
            str: The major version number (first number in version string)
        """
        return self._version[0]

    @property
    def minor(self):
        """
        Get the minor version number.

        Returns:
            str: The minor version number (second number in version string)
        """
        return self._version[1]

    @property
    def maintenance(self):
        """
        Get the maintenance version number.

        Returns:
            str: The maintenance version number (third number in version string)
        """
        return self._version[2]

    @property
    def build(self):
        """
        Get the build version number.

        Returns:
            str: The build version number (fourth number in version string)
        """
        return self._version[3]

    @property
    def Development_stage(self):
        """
        Get the development stage identifier.

        Returns:
            str: The development stage (e.g., 'release', 'testing')
        """
        return self._version[4]

    @property
    def version_number(self):
        """
        Get the complete version number as a string.

        Returns:
            str: Full version number in format 'major.minor.maintenance.build'
        """
        return f'{self._version[0]}.{self._version[1]}.{self._version[2]}.{self._version[3]}'

    @property
    def version_number_build_plus_one(self):
        """
        Get the version number with build number incremented by one.

        Returns:
            str: Version number with build number increased by 1
        """
        return f'{self._version[0]}.{self._version[1]}.{self._version[2]}.{int(self._version[3]) + 1}'

    @property
    def version_number_hotfix_plus_one(self):
        """
        Get the version number with maintenance number incremented by one.

        Returns:
            str: Version number with maintenance number increased by 1
        """
        return f'{self._version[0]}.{self._version[1]}.{int(self._version[2]) + 1}.{int(self._version[3])}'

    @property
    def version_number_no_build(self):
        """
        Get the version number without the build number.

        Returns:
            str: Version number in format 'major.minor.maintenance'
        """
        return f'{self._version[0]}.{self._version[1]}.{self._version[2]}'


class MangeRepo:
    """
    Class for managing Git repository operations with secure credential handling.

    This class handles:
    - Repository initialization and version tracking
    - Secure credential management for SharePoint and Gitea
    - Tag management and version tracking
    - Commit operations
    - Branch creation and management
    - Release management through Gitea API

    Attributes:
        _current_repo (git.Repo): Git repository instance
        _file_not_committed (str): List of uncommitted files
        _active_brunch (str): Name of the active branch
        _current_repo_version (VersionNumber): Current version from repository tags
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize the repository manager.

        Args:
            max_retries (int): Maximum number of authentication retry attempts

        Raises:
            Exception: If authentication fails after max_retries or repository initialization fails
        """
        # Initialize repository instance
        try:
            self._current_repo = git.Repo(search_parent_directories=True)
            self._initialize_repo(max_retries)
        except git.exc.InvalidGitRepositoryError as e:
            logging.error("Failed to initialize git repository")
            raise Exception("Not a valid git repository") from e

    def _initialize_repo(self, max_retries: int) -> None:
        """
        Initialize repository by fetching tags and setting up initial state.

        Args:
            max_retries (int): Maximum number of authentication retry attempts

        Raises:
            Exception: If authentication fails after max retries
        """
        # Clean up existing tags
        for tag in self._current_repo.tags:
            self._current_repo.delete_tag(tag)

        # Fetch remote tags with retry logic
        retry_count = 0
        while retry_count < max_retries:
            try:
                self._current_repo.remotes.origin.fetch(tags=True)
                break
            except git.exc.GitCommandError as e:
                retry_count += 1
                logging.warning(f"Authentication attempt {retry_count} failed")
                if retry_count == max_retries:
                    logging.error("All authentication attempts failed")
                    raise Exception("Failed to authenticate with Git after multiple attempts") from e
                time.sleep(2)  # Wait before retry

        # Initialize repository properties
        self._init_repo_properties()

    def _init_repo_properties(self) -> None:
        """
        Initialize repository properties including uncommitted files,
        active branch, and current version.
        """
        # Check for uncommitted changes
        if self._current_repo.index.diff(None):
            self._file_not_committed = '\n'.join(
                [item.a_path for item in self._current_repo.index.diff(None)]
            )
        else:
            self._file_not_committed = None

        # Store active branch name
        self._active_brunch = str(self._current_repo.active_branch)

        # Get current version from tags
        self._current_repo_version = self._get_highest_version_from_tags()

    def _get_highest_version_from_tags(self) -> VersionNumber:
        """
        Get the highest version number from repository tags.

        Returns:
            VersionNumber: Highest version number found in tags, or 0.0.0.0 if no tags exist
        """
        tags = self._current_repo.tags
        version_numbers = []

        # Extract version numbers from tags
        for tag in tags:
            match = re.match(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", tag.name)
            if match:
                major, minor, patch, build = match.groups()
                version_numbers.append((int(major), int(minor), int(patch), int(build)))

        # Get highest version or default to 0.0.0.0
        highest_version = max(version_numbers) if version_numbers else (0, 0, 0, 0)
        return VersionNumber(".".join(map(str, highest_version)))

    def make_commit(self, files_to_commit: list, commit_message: str, tag: str) -> None:
        """
        Commit changes, create a tag, and push to remote.

        Args:
            files_to_commit (list): List of files to commit
            commit_message (str): Commit message
            tag (str): Tag name for the commit

        Raises:
            Exception: If commit or push operations fail
        """
        logging.info("Committing, tagging, and pushing changes")

        try:
            # Stage specified files
            for file in files_to_commit:
                self._current_repo.git.add(file)

            # Commit changes
            self._current_repo.git.commit('-m', commit_message)

            # Create and push tag
            self._current_repo.create_tag(tag)
            origin = self._current_repo.remote(name='origin')

            # Set up upstream branch if it doesn't exist
            current_branch = self._current_repo.active_branch
            try:
                origin.push(str(self._current_repo.active_branch))
            except git.exc.GitCommandError:
                # Set upstream branch
                self._current_repo.git.branch('--set-upstream-to', f'origin/{current_branch.name}', current_branch.name)
                origin.push()

            # Push the tag
            origin.push(tag)

            logging.info("Changes committed, tagged, and pushed successfully")
        except Exception as e:
            error_msg = f"Failed to commit and push changes: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            raise Exception(error_msg) from e

    def create_new_branch(self, new_branch_name: str) -> tuple[bool, str]:
        """
        Create and push a new branch from the current active branch.

        Args:
            new_branch_name (str): Name of the new branch to create

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            # Create and checkout new branch
            current = self._current_repo.active_branch
            new_branch = self._current_repo.create_head(new_branch_name)
            new_branch.checkout()

            # Push the new branch to remote
            self._current_repo.remote('origin').push(new_branch.name)

            return True, f"Successfully created and pushed branch '{new_branch_name}' from '{current}'"

        except Exception as e:
            error_msg = f"Failed to create branch: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    def create_release_from_tag(self, user_credentials, tag_name: str, is_pre_release: bool = True,
                                release_message: str = "") -> tuple[bool, str]:
        """
        Create a release in Gitea from a specified tag using stored credentials.

        Args:
            user_credentials : user credentials
            tag_name (str): Name of the tag to create release from
            is_pre_release (bool): If True, marks the release as a pre-release
            release_message (str): Description/message for the release

        Returns:
            tuple[bool, str]: Success status and message
        """
        try:
            # Get stored credentials
            if not user_credentials:
                return False, "No credentials found"

            # Suppress SSL warnings for internal servers
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Parse repository information from remote URL
            remote_url = self._current_repo.remotes.origin.url
            repo_parts = remote_url.replace('.git', '').split('/')
            server = repo_parts[2]
            owner = repo_parts[3]
            repo_name = repo_parts[4]

            # Construct API endpoint
            api_url = f"https://{server}/api/v1/repos/{owner}/{repo_name}/releases"

            # Get current branch
            target_branch = str(self._current_repo.active_branch)

            # Prepare release data
            release_data = {
                "tag_name": tag_name,
                "target_commitish": target_branch,
                "name": f"{'testing' if is_pre_release else 'release'} {tag_name}",
                "body": release_message,
                "draft": False,
                "prerelease": is_pre_release
            }

            # Create release using Gitea API
            with no_ssl_verification():
                response = requests.post(
                    api_url,
                    json=release_data,
                    auth=(user_credentials['gitea_username'], user_credentials['password']),
                    verify=False
                )

            if response.status_code == 201:
                return True, f"Successfully created release from tag {tag_name}"
            else:
                error_msg = f"Failed to create release. Status code: {response.status_code}, Response: {response.text}"
                logging.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to create release: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            return False, error_msg

    @property
    def repo(self) -> git.Repo:
        """Get the current repository instance."""
        return self._current_repo

    @property
    def file_not_committed(self) -> str:
        """Get the list of uncommitted files."""
        return self._file_not_committed

    @property
    def active_brunch_name(self) -> str:
        """Get the name of the active branch."""
        return self._active_brunch

    @property
    def current_repo_version_number(self) -> VersionNumber:
        """Get the current version number of the repository."""
        return self._current_repo_version


class CustomFrame(customtkinter.CTkFrame):
    """
    A custom frame widget that displays a label and dynamic content (status/progress) in a horizontal layout.

    This frame is designed to show status information in a compact, single-line format with:
    - A fixed-width label on the left
    - A dynamic space on the right that can show either a progress bar or status label

    Attributes:
        label (CTkLabel): The label widget showing the frame's title/description
        space_filler (Union[CTkLabel, CTkProgressBar]): Dynamic widget showing status or progress
    """

    def __init__(self, master=None, label_text="Default Label", **kwargs):
        """
        Initialize the CustomFrame with a horizontal layout.

        Args:
            master: The parent widget
            label_text (str): Text to display in the label portion
            **kwargs: Additional keyword arguments passed to CTkFrame
        """
        super().__init__(master, **kwargs)

        # Configure grid layout for horizontal arrangement
        # Column 0: Fixed-width label
        # Column 1: Dynamic content (progress bar or status)
        self.grid_columnconfigure(0, weight=0)  # Label column - fixed width
        self.grid_columnconfigure(1, weight=1)  # Space filler column - expandable

        # Create and position the label on the left side
        self.label = customtkinter.CTkLabel(
            self,
            text=label_text,
            width=120  # Fixed width ensures consistent layout
        )
        self.label.grid(
            row=0,
            column=0,
            pady=2,
            padx=2,
            sticky="w"  # West alignment keeps text left-aligned
        )

        # Initialize the space filler (empty label initially)
        self.space_filler = customtkinter.CTkLabel(
            self,
            text="",
            width=200  # Fixed width for consistent layout
        )
        self.space_filler.grid(
            row=0,
            column=1,
            pady=2,
            padx=2,
            sticky="w"
        )

    def run(self):
        """
        Switch the space filler to a progress bar mode.

        Removes any existing content and displays an active progress bar.
        """
        # Clean up existing space filler
        if self.space_filler is not None:
            self.space_filler.destroy()

        # Create and configure the progress bar
        self.space_filler = customtkinter.CTkProgressBar(
            self,
            width=200  # Match width of other states for consistency
        )
        self.space_filler.grid(
            row=0,
            column=1,
            pady=2,
            padx=2,
            sticky="w"
        )
        self.space_filler.start()  # Start the progress bar animation

    def finish_with_label(self, text, color):
        """
        Switch the space filler to a status label with specified text and color.

        Args:
            text (str): The status text to display
            color (str): The background color for the status label
        """
        # Clean up existing space filler
        if self.space_filler is not None:
            self.space_filler.destroy()

        # Create and configure the status label
        self.space_filler = customtkinter.CTkLabel(
            self,
            text=text,
            fg_color=color,
            width=200  # Match width of other states for consistency
        )
        self.space_filler.grid(
            row=0,
            column=1,
            pady=2,
            padx=2,
            sticky="w"
        )


if __name__ == "__main__":
    check_python_version()
    logging.info("Started Build Program")

    # Parse command line arguments
    import argparse

    # Parse command line arguments
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='NLH Package Builder')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')

    # Username/password authentication options
    parser.add_argument('--sp-username', help='SharePoint username')
    parser.add_argument('--gitea-username', help='Gitea username')
    parser.add_argument('--password', help='Common password')

    # Token authentication options
    parser.add_argument('--sp-token', help='SharePoint access token')
    parser.add_argument('--gitea-token', help='Gitea access token')

    # Other options
    parser.add_argument('--make-release', action='store_true', help='Make a release version')
    parser.add_argument('--no-gui', action='store_true', help='Run in non-GUI mode')
    parser.add_argument('--release-notes', help='Release notes for Gitea release')
    main_arg = parser.parse_args()

    # Check Python version
    major_version = sys.version_info.major
    minor_version = sys.version_info.minor
    if not (major_version == 3 and (minor_version == 10 or minor_version == 11)):
        warning_message = (
            f"Warning: This script is intended for Python versions 3.10 or 3.11. "
            f"You are currently using Python {major_version}.{minor_version}."
        )
        logging.warning(warning_message)
        if not main_arg.no_gui:
            try:
                root = tkinter.Tk()
                root.withdraw()
                messagebox.showwarning("Python Version Warning", warning_message)
            except Exception as main_exception:
                logging.error(f"Failed to display GUI warning: {main_exception}")
        print(warning_message)
        sys.exit(1)

    # Initialize builder object
    main_builder_obj = PackageBuilder()
    credential_manager = CredentialManager()

    if main_arg.no_gui:
        # Non-GUI mode
        try:
            # Initialize SharePoint handler
            success, message = main_builder_obj.initialize_sharepoint_handler()
            if not success:
                logging.error(f"SharePoint initialization failed: {message}")
                sys.exit(1)
        except Exception as E:
            sys.exit(1)
        # Handle non-GUI credentials

        if main_arg.sp_token and main_arg.gitea_token:
            # Using tokens
            credentials = {
                "sharepoint_token": main_arg.sp_token,
                "gitea_token": main_arg.gitea_token
            }
        elif main_arg.sp_username and main_arg.gitea_username and main_arg.password:
            # Using username/password
            credentials = {
                "sharepoint_username": main_arg.sp_username,
                "gitea_username": main_arg.gitea_username,
                "password": main_arg.password
            }

            # Verify credentials
            main_success, main_message = main_builder_obj.verify_credentials(**credentials)
            if not main_success:
                logging.error(f"Credential verification failed: {main_message}")
                sys.exit(1)

            # Save verified credentials
            credential_manager.save_credentials(**credentials)
        else:
            logging.error("Either tokens (--sp-token and --gitea-token) or "
                          "username/password combinations (--sp-username, --gitea-username, and --password) "
                          "must be provided in non-GUI mode")
            sys.exit(1)

        credential_manager.save_credentials(**credentials)
        try:
            # Set debug mode if specified
            if main_arg.debug:
                logging.getLogger().setLevel(logging.DEBUG)
                logging.debug("Debug mode enabled")

            # Set make release if specified
            if main_arg.make_release:
                main_builder_obj.make_release_tag = True
                logging.info("Make release tag enabled")

            # Execute build steps
            main_builder_obj.cleanup_environment()

            if not main_arg.debug and not main_builder_obj.repo.file_not_committed:
                main_builder_obj.update_version_xml_handler()
                main_builder_obj.update_install_build_file()

            main_success, main_message = main_builder_obj.check_and_update_spec()
            logging.info(main_message)
            if not main_success:
                raise Exception(f'Failed to update spec file: {main_message}')

            main_builder_obj.make_version_file()

            main_success, main_message = main_builder_obj.create_clean_python_env_non_gui(True)
            logging.info(main_message)
            if not main_success:
                raise Exception(f'Failed to create python environment: {main_message}')

            main_success, main_message = main_builder_obj.create_package_non_gui(True)
            logging.info(main_message)
            if not main_success:
                raise Exception(f'Failed to create package: {main_message}')

            main_success, main_message = main_builder_obj.check_package_imported_on_start()
            logging.info(main_message)
            if not main_success:
                raise Exception(f'Package import test failed: {main_message}')

            main_success, main_message = main_builder_obj.create_installer_non_gui(True)
            logging.info(main_message)
            if not main_success:
                raise Exception(f'Failed to create installer: {main_message}')

            # Upload to SharePoint if credentials provided
            main_success, main_message = main_builder_obj.upload_to_sharepoint()
            if not main_success:
                raise Exception(f'Failed to upload to SharePoint: {main_message}')

            if not main_arg.debug and not main_builder_obj.repo.file_not_committed:
                main_builder_obj.make_commit()
                # After successful build and upload
                main_success, main_message = main_builder_obj.create_gitea_release(main_arg.release_notes or "")
                if not main_success:
                    logging.error(f"Failed to create release: {main_message}")

            logging.info("Build completed successfully")

        except Exception as main_exception:
            logging.error(f"Build failed: {str(main_exception)}")
            # Rollback changes if we modified files
            if not main_arg.debug and not main_builder_obj.repo.file_not_committed:
                main_success, rollback_msg = main_builder_obj.rollback_changes()
                if main_success:
                    logging.info("Changes have been rolled back")
                else:
                    logging.error(f"Failed to roll back changes: {rollback_msg}")

            sys.exit(1)

    else:
        # GUI mode
        app = App(main_builder_obj)
        app.mainloop()
