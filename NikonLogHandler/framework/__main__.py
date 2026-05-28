"""
This script initializes the Nikon Log Handler application. It handles parsing command line arguments,
verifying package dependencies against a requirements.txt file, configuring logging based on user inputs,
and managing exceptions that might arise during application startup, including import issues.

It leverages `importlib.metadata` for introspection of installed packages, adhering to modern Python practices
for compatibility and maintenance ease. Furthermore, it enhances error diagnostics by automatically appending
tracebacks to log messages for warnings and above in debug mode.
"""

import argparse
import logging
import os
import sys
import traceback
import atexit
from importlib.metadata import distributions
from logging.handlers import RotatingFileHandler
from tkinter import messagebox

from win32api import GetLastError, MessageBox, CloseHandle
from win32con import MB_OK, MB_ICONWARNING
from win32event import CreateMutex
from winerror import ERROR_ALREADY_EXISTS

from main_app_files.function_files.exception_handler_and_reporting import global_exception_handler, save_import_test_result  # Import global exception handler and logger

# Set the global exception handler
sys.excepthook = global_exception_handler

# Detect if running in PyCharm
is_pycharm = "PYCHARM_HOSTED" in os.environ

# Setup command line argument parsing
parser = argparse.ArgumentParser(description="Initialize Nikon Log Handler application.")
parser.add_argument('--test_import_lib', help="Run test to check if libraries can be imported", action='store_true')
parser.add_argument('--log_level', help="Set logging level", default=None)  # Default is None to decide based on debug mode later
parser.add_argument('--debug', help="Enable debug options", default=False, action='store_true')
args, unknown = parser.parse_known_args()
args = vars(args)

# Set up the logger
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = RotatingFileHandler('NikonLogHandlerError.log', maxBytes=5 * 1024 * 1024, backupCount=1)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# Prevent propagation to avoid duplicate logs
error_logger.propagate = False

# Determine the default logging level based on debug mode
if args["debug"]:
    default_log_level = 'INFO'  # Default to INFO in debug mode
else:
    default_log_level = 'WARNING'  # Default to WARNING when not in debug mode

# Override the default log level if one was explicitly provided
log_level = args["log_level"].upper() if args["log_level"] else default_log_level

# Configure logging
handlers = [logging.FileHandler('NikonLogHandlerError.log')]
if args["debug"]:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s:%(message)s', handlers=handlers)


# Custom logging filter to append traceback information conditionally
class TracebackFilter(logging.Filter):
    """
    Custom logging filter to append traceback information conditionally.
    """

    def filter(self, record):
        """
        Append full traceback to log message if debug is enabled and log level is WARNING or above.
        """
        if args["debug"] and record.levelno >= logging.WARNING:
            record.exc_info = True
            record.exc_text = traceback.format_exc(limit=-1)  # Append full traceback
        return True


# Apply the TracebackFilter to each handler
for handler in handlers:
    handler.addFilter(TracebackFilter())

logging.info('Application started')

# Warn if running in PyCharm without debug mode activated
if not args["test_import_lib"] and is_pycharm and not args["debug"]:
    messagebox.showwarning("Warning", "You are running NLH as developer but didn't activate development mode. Please run __Main__.py with parameter --debug True")

# Python version and virtual environment checks
if args["debug"]:
    major_version = sys.version_info.major
    minor_version = sys.version_info.minor
    if not (major_version == 3 and (minor_version == 10 or minor_version == 11)):
        warning_message = f"Warning: This script is intended for Python versions 3.10 or 3.11. You are currently using Python {major_version}.{minor_version}."
        logging.warning(warning_message)
        messagebox.showwarning("Python Version Warning", warning_message)
    if getattr(sys, 'base_prefix', sys.prefix) == sys.prefix:
        messagebox.showwarning("Warning", "You are not running inside a Python virtual environment.")

# Function definitions and application logic...

PACKAGE_ALIAS_MAP = {
    'PIL': 'Pillow',
    'office365': 'Office365-REST-Python-Client',
}


def get_package_name(import_name):
    """
    Resolves the actual package name from an alias using PACKAGE_ALIAS_MAP.

    Parameters:
        import_name (str): The import name or alias of the package.

    Returns:
        str: The actual package name as listed in the distribution.
    """
    return PACKAGE_ALIAS_MAP.get(import_name, import_name)


def check_packages():
    """
    Verifies that all packages listed in the requirements.txt file are installed.
    Alerts the user via messagebox if any required packages are missing or have mismatched versions.
    """
    requirements_path = 'requirements.txt'
    if not os.path.isfile(requirements_path):
        logging.error('Package Check: requirements.txt file not found')
        messagebox.showerror('Package Check', 'requirements.txt file not found')
        return

    with open(requirements_path, 'r') as file:
        required_packages = {line.strip().lower() for line in file.readlines()}

    installed_packages = {pkg.metadata['Name'].lower() + "==" + pkg.version for pkg in distributions()}

    # Check for missing or mismatched packages
    missing_packages = [pkg for pkg in required_packages if not any(
        req_pkg.split('==')[0] == pkg.split('==')[0] and req_pkg.split('==')[1] == pkg.split('==')[1]
        for req_pkg in installed_packages
    )]

    if missing_packages:
        warning_message = 'These packages are NOT installed or have mismatched versions:\n' + '\n'.join(missing_packages)
        logging.warning('Package Check: ' + warning_message)
        messagebox.showwarning('Package Check', warning_message)


def prevent_multiple_instances():
    """
    Prevents multiple instances of the program from running simultaneously.
    Returns mutex handle if this is the first instance, None otherwise.
    """
    mutex_name = "Global\\NikonLogHandler_Mutex"

    try:
        # Try to create a named mutex
        mutex = CreateMutex(None, False, mutex_name)
        last_error = GetLastError()

        # Check if the mutex already exists
        if last_error == ERROR_ALREADY_EXISTS:
            MessageBox(0,
                       "An instance of Nikon Log Handler is already running.",
                       "Multiple Instances Detected",
                       MB_OK | MB_ICONWARNING)
            return None

        return mutex  # Return the mutex handle

    except Exception as e:
        logging.error(f"Error in mutex creation: {str(e)}")
        return None


def cleanup_mutex(mutex_handle):
    """
    Cleanup function to properly close the mutex handle
    """
    if mutex_handle:
        try:
            CloseHandle(mutex_handle)
        except Exception as e:
            logging.error(f"Error closing mutex handle: {str(e)}")


if args["debug"]:
    check_packages()

# Try-except block for application startup and exception handling...

try:
    from main_app_files.function_files._nlh_xml_handler import NlhXmlHandler
    from main_app_files.gui_files._app_windows import MainWindow

    # ── NEW: import and run plugin discovery before the GUI starts ──────────
    from main_app_files.core_script_files.discovery import discovery

    # ────────────────────────────────────────────────────────────────────────

    if __name__ == "__main__":
        mutex_handle = prevent_multiple_instances()
        if not mutex_handle:
            sys.exit(1)

        atexit.register(cleanup_mutex, mutex_handle)

        if args["test_import_lib"]:
            save_import_test_result("Library import test passed.")
        else:
            app_xml = 'NikonLogHandler.xml'
            nikon_log_obj = NlhXmlHandler(app_xml)
            app = MainWindow(nikon_log_obj)
            app.mainloop()

except Exception as e:
    global_exception_handler(type(e), e, e.__traceback__)
finally:
    logging.info('Application finished')