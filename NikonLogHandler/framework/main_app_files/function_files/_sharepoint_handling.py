"""
This module provides functionality for interacting with SharePoint, including checking for updates,
downloading files, and handling authentication. It includes a SharePointHandler class that manages
SharePoint connections and operations.

Classes:
    IncorrectCredentialsException: Exception for incorrect username or password.
    NetworkConnectionException: Exception for network connection issues.
    AccessDeniedException: Exception for denied access to SharePoint site.
    SharePointHandler: Main class for SharePoint operations.

This module requires the following external libraries:
    - Office 365
    - packaging
    - pathlib
"""
import logging
import re
import zipfile
import os

from pathlib import Path
from typing import List

from packaging import version
from office365.sharepoint.client_context import ClientContext
from main_app_files.function_files._nlh_xml_handler import available_version_type
from main_app_files.function_files.exception_handler_and_reporting import global_exception_handler, NlhException


class IncorrectCredentialsException(Exception):
    """Exception raised when the provided username or password is incorrect."""
    pass


class NetworkConnectionException(Exception):
    """Exception raised when there is no network connection or an error occurs during login."""
    pass


class AccessDeniedException(Exception):
    """Exception raised when the user does not have access to the SharePoint site."""
    pass


class SharePointHandler:
    """
    A class to handle SharePoint operations with persistent authentication.
    """

    def __init__(self, sharepoint_url: str, auto_authenticate: bool = False):
        """
        Initialize SharePoint handler.

        Args:
            sharepoint_url (str): The SharePoint site URL
            auto_authenticate (bool): Whether to automatically authenticate on initialization
        """
        self.sharepoint_url = sharepoint_url
        self.ctx = None
        self.is_authenticated = False
        self.authentication_error = None

        if auto_authenticate:
            self.authenticate()

    def authenticate(self):
        """
        Authenticate to SharePoint (blocking call).
        Returns True if successful, False if failed.
        """
        try:
            self._perform_authentication()
            self.is_authenticated = True
            self.authentication_error = None
            return True
        except Exception as e:
            self.authentication_error = str(e)
            self.is_authenticated = False
            # Log the exception using global_exception_handler
            global_exception_handler(type(e), e, e.__traceback__, show_popup=False, error_message=f"SharePoint authentication failed: {str(e)}")
            return False

    def retry_authentication(self):
        """
        Retry authentication (can be called from outside, e.g., login button).
        Returns True if successful, False if failed.
        """
        try:
            self._perform_authentication()
            self.is_authenticated = True
            self.authentication_error = None
            return True
        except Exception as e:
            self.authentication_error = str(e)
            self.is_authenticated = False
            # Log the exception using global_exception_handler
            global_exception_handler(type(e), e, e.__traceback__, show_popup=False, error_message=f"SharePoint re-authentication failed: {str(e)}")
            return False

    def _perform_authentication(self):
        """
        Internal method to perform the actual authentication with timeout.
        """
        import re
        import threading
        import time

        tenant_match = re.search(r'https://([^.]+ )\.sharepoint\.com', self.sharepoint_url)
        tenant = f"{tenant_match.group(1)}.onmicrosoft.com" if tenant_match else "organizations"

        # Try client IDs in order of likelihood to have SharePoint API access
        client_configs = [
            # SharePoint specific clients (try these first)
            ("9bc3ab49-b65d-410a-85ad-de819febfddc", "SharePoint Online Management Shell"),
        ]

        last_error = None

        for client_id, name in client_configs:
            try:
                logging.info(f"Trying {name} (Client ID: {client_id})")

                # Use threading to implement timeout for authentication
                auth_result = {"ctx": None, "error": None, "completed": False}

                def authenticate_with_timeout():
                    try:
                        ctx = ClientContext(self.sharepoint_url).with_interactive(
                            tenant=tenant,
                            client_id=client_id
                        )

                        # Test the connection with actual API call
                        web = ctx.web
                        ctx.load(web)
                        ctx.execute_query()

                        auth_result["ctx"] = ctx
                        auth_result["completed"] = True

                    except Exception as e:
                        auth_result["error"] = e
                        auth_result["completed"] = True

                # Start authentication in a separate thread
                auth_thread = threading.Thread(target=authenticate_with_timeout)
                auth_thread.daemon = True  # Dies when main thread dies
                auth_thread.start()

                # Wait for authentication with timeout (60 seconds)
                timeout_seconds = 10
                start_time = time.time()

                while not auth_result["completed"] and (time.time() - start_time) < timeout_seconds:
                    time.sleep(0.5)  # Check every 500ms

                if auth_result["completed"]:
                    if auth_result["ctx"] is not None:
                        logging.info(f"Success with {name}!")
                        self.ctx = auth_result["ctx"]
                        return
                    elif auth_result["error"] is not None:
                        # Authentication completed but with error
                        error_msg = str(auth_result["error"])
                        if "401" in error_msg or "Unauthorized" in error_msg:
                            last_error = f"{name} failed: Authentication worked but API access denied"
                        elif "redirect" in error_msg.lower():
                            last_error = f"{name} failed: Redirect URI issue"
                        else:
                            last_error = f"{name} failed: {error_msg[:100]}..."
                        continue
                else:
                    # Timeout occurred
                    last_error = f"{name} failed: Authentication timeout after {timeout_seconds} seconds"
                    logging.warning(f"Authentication timeout for {name}")
                    continue

            except Exception as e:
                error_msg = str(e)
                last_error = f"{name} failed: {error_msg[:100]}..."
                logging.error(last_error)
                continue

        # If all failed, raise the last error
        raise NlhException("Unable to login")

    def _check_authentication(self):
        """
        Check if authenticated before performing operations.
        """
        if not self.is_authenticated or self.ctx is None:
            raise NetworkConnectionException("Not authenticated to SharePoint. Please authenticate first.")

    def check_for_updates(self, sharepoint_folder: str, current_version_number: str,
                          current_version_type: available_version_type, participate_in_testing: bool):
        """
        Check for the latest version of a file in a SharePoint folder.
        """
        self._check_authentication()

        try:
            # Get the folder from the SharePoint site
            folder = self.ctx.web.get_folder_by_server_relative_url(sharepoint_folder)
            latest_version_number = version.parse(current_version_number)
            latest_version_type = current_version_type
            latest_version_file = None
            latest_version_file_size = None

            # Get the list of files in the folder
            file_list = folder.files
            self.ctx.load(file_list)
            self.ctx.execute_query()

            # Filter out testing versions if participate_in_testing is False
            if not participate_in_testing:
                file_list = [file for file in file_list if 'testing' not in file.properties["Name"]]

            # Iterate through the list of files
            for file in file_list:
                file_name = file.properties["Name"]
                file_size = file.length

                # Extract the version number from the file name using a regular expression
                file_version = re.search(r'\d+\.\d+\.\d+\.\d+', file_name)
                if file_version:
                    file_version_obj = version.parse(file_version.group(0))

                    # Check if the extracted version number is higher than the current latest version number
                    if file_version_obj > latest_version_number:
                        latest_version_number = file_version_obj
                        latest_version_type = 'release' if 'release' in file_name else 'testing'
                        latest_version_file = file_name
                        latest_version_file_size = file_size

            # Check if a new version was found and return the appropriate result
            if latest_version_number > version.parse(current_version_number):
                return [str(latest_version_number), latest_version_type, latest_version_file, latest_version_file_size]
            else:
                return 'No update available'

        except Exception as exp:
            global_exception_handler(type(exp), exp, exp.__traceback__, show_popup=False)
            return 'Error, checking for updates Failed'

    def load_file_from_sharepoint(self, sharepoint_folder: str, file_to_download: str, output_file_location: str):
        """
        Downloads a file from SharePoint.
        """
        self._check_authentication()

        try:
            # Correctly handle the file download by using a file object
            file_url = f"{sharepoint_folder}/{file_to_download}"
            output_file_location += file_to_download
            with open(output_file_location, 'wb') as local_file:
                self.ctx.web.get_file_by_server_relative_url(file_url).download(local_file).execute_query()
            return output_file_location
        except Exception as exp:
            global_exception_handler(type(exp), exp, exp.__traceback__, show_popup=False)
            return f'Error, loading data from SharePoint failed\n {str(exp)}'

    def download_update_file(self, sharepoint_folder: str, new_version_file_name: str, new_version_file_size: int, chunk_downloaded: callable):
        """
        Download a file from a SharePoint location, unzip it, and return the full path to the unzipped file.
        """
        self._check_authentication()

        # Construct the output file location for the downloaded file
        output_file_location = f'c:\\temp\\{new_version_file_name}'

        try:
            # Download the file from SharePoint
            with open(output_file_location, 'wb') as output_file:
                self.ctx.web.get_file_by_server_relative_url(f'{sharepoint_folder}/{new_version_file_name}').download_session(
                    output_file, chunk_downloaded, int(new_version_file_size / 10)).execute_query()

            # Remove the .zip extension if present
            if new_version_file_name.endswith('.zip'):
                unzipped_file_name = new_version_file_name[:-4]
            else:
                unzipped_file_name = new_version_file_name

            # Unzip the downloaded file
            unzip_folder = Path(os.path.dirname(output_file_location))
            with zipfile.ZipFile(output_file_location, 'r') as zip_ref:
                # Get the first file from the zip archive
                first_file = zip_ref.namelist()[0]
                # Extract the first file to the unzip folder
                zip_ref.extract(first_file, unzip_folder)

            # Construct the full path to the unzipped file
            unzipped_file_path = unzip_folder / Path(first_file).name
            return str(unzipped_file_path)
        except Exception as exp:
            global_exception_handler(type(exp), exp, exp.__traceback__, show_popup=False)
            return 'Error, downloading updates failed'

    def upload_file(self, sharepoint_folder: str, file_path: str) -> str:
        """
        Upload a file to SharePoint and check it in as version 1.0.
        """
        self._check_authentication()

        # Check if local file exists
        if not os.path.exists(file_path):
            return "Error: Local file not found"

        # Get the file name from the path
        file_name = os.path.basename(file_path)

        # Get the target folder
        target_folder = self.ctx.web.get_folder_by_server_relative_url(sharepoint_folder)
        self.ctx.load(target_folder)
        self.ctx.execute_query()

        # If a file with the same name exists, delete it first
        try:
            file_url = f"{sharepoint_folder}/{file_name}"
            existing_file = self.ctx.web.get_file_by_server_relative_url(file_url)
            self.ctx.load(existing_file)
            self.ctx.execute_query()

            # Undo any existing checkouts before deleting
            existing_file.undo_checkout()
            self.ctx.execute_query()

            # Delete existing file
            existing_file.delete_object()
            self.ctx.execute_query()
        except Exception:
            # File doesn't exist, continue with upload
            pass

        # Read and upload file content
        with open(file_path, 'rb') as content_file:
            file_content = content_file.read()

        uploaded_file = target_folder.upload_file(file_name, file_content)
        self.ctx.load(uploaded_file)
        self.ctx.execute_query()

        # Get the file object after upload
        file_url = f"{sharepoint_folder}/{file_name}"
        file = self.ctx.web.get_file_by_server_relative_url(file_url)

        # Load necessary properties
        self.ctx.load(file)
        self.ctx.execute_query()

        # Check in the file as a major version
        file.checkin("Initial version", 1)  # 1 represents major check-in
        self.ctx.execute_query()

        return f"Successfully uploaded and checked in {file_name} as version 1.0"

    def download_sharepoint_folders(self, sharepoint_folder: str, target_directory: Path) -> List[str]:
        """
        Download all folders from a SharePoint location to a local directory.
        """
        self._check_authentication()

        try:
            # Get the Machine_logs folder
            relative_url = sharepoint_folder.replace('%20', ' ')
            folder = self.ctx.web.get_folder_by_server_relative_url(relative_url)
            self.ctx.load(folder)
            self.ctx.execute_query()

            # Get all subfolders
            folders = folder.folders
            self.ctx.load(folders)
            self.ctx.execute_query()

            downloaded_folders = []

            # Create target directory if it doesn't exist
            target_directory.mkdir(parents=True, exist_ok=True)

            # Process each subfolder
            for subfolder in folders:
                try:
                    # Skip system folders
                    if subfolder.name in ['Forms', 'System']:
                        continue

                    # Create subfolder in target directory
                    local_folder = target_directory / subfolder.name
                    local_folder.mkdir(exist_ok=True)

                    # Get all files in the subfolder
                    files = subfolder.files
                    self.ctx.load(files)
                    self.ctx.execute_query()

                    # Download each file in the subfolder
                    for file in files:
                        try:
                            file_path = local_folder / file.name
                            with open(file_path, 'wb') as local_file:
                                file.download(local_file).execute_query()

                            downloaded_folders.append(str(local_folder))

                        except Exception as file_exp:
                            raise file_exp

                except Exception as folder_exp:
                    raise folder_exp

            return list(set(downloaded_folders))  # Remove duplicates

        except Exception as exp:
            error_msg = f"Error downloading SharePoint folders: {str(exp)}"
            return [f" {error_msg}"]