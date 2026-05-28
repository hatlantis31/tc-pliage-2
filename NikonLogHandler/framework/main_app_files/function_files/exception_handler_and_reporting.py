"""
This script defines custom exception handling for the Nikon Log Handler application.
It includes functionality to send bug reports via email when exceptions occur, with the error log attached.
"""

import sys
import os

import traceback
import logging
import threading
import textwrap
import win32com.client
import tkinter as tk

from types import TracebackType
from typing import Type, Optional
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('error_logger')


class NlhException(Exception):
    """
    Custom exception class for Nikon Log Handler.

    This Exception class is used by the NLH to identify exceptions and to send error messages to the user.
    """

    def __init__(self, message, original_traceback=None):
        """
          :param original_traceback: this is used to pass traceback for Exception you convert to NlhException
        """
        super().__init__(message)
        self.original_traceback = original_traceback


def send_request():
    """
    Send a request email with relevant attachments.

    This function creates a new email in Outlook with a predefined template for making requests.
    The email includes placeholders for the user to describe the request, provide context,
    and add any additional information. Relevant files can be automatically attached to the email.

    Returns:
        None
    """
    # Construct the email details
    subject = 'Request: [Brief Description]'
    body = textwrap.dedent("""\
    Dear NLH Team,

    I hope this email finds you well. I am writing to make the following request:

    Request Details:
    [Clearly state your request here]
    
    [What should the output look like]
    
    [How should the result be verified]
    
    [Add log files that can be used for development and verification]
    
    [Detail the reference documentation for this request]

    Context:
    [Provide any necessary background information or context for your request]

    Importance/Urgency:
    [Explain the importance or urgency of this request, if applicable]

    Required Action:
    [Specify what action or response you need from the recipient]

    Timeline:
    [If applicable, mention any deadlines or preferred timelines]

    Additional Information:
    [Include any other relevant details, references, or explanations]

    Attachments:
    [List any attachments you've included with this email]

    Please let me know if you need any further information or clarification regarding this request.

    Thank you for your attention to this matter.

    Best regards,
    [Your Name]
    """)
    recipient = 'nlh-team.npe@nikonglobal.onmicrosoft.com'  # Replace with the appropriate email address

    # Create the Outlook application and email item
    try:
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        # Configure the email
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body

        # Display the email for review and send
        mail.Display()  # Uncomment this line to display the email before sending
        # mail.Send()  # Uncomment this line to send the email automatically

        logging.info('Request email created successfully!')
    except Exception as e:
        logging.error(f"Error creating or sending request email: {e}")


def send_bug_report():
    """
    Send a bug report email with all error log files attached.

    This function creates a new email in Outlook with a predefined template for reporting bugs.
    The email includes placeholders for the user to describe the issue, steps to reproduce,
    expected and actual behavior, and additional information. All error log files are automatically
    attached to the email.

    Returns:
        None
    """
    # Construct the email details
    subject = 'Bug Report'
    body = textwrap.dedent("""\
    Dear NLH Team,

    Please find the error logs attached to this email. I'm reporting the following issue:

    [Describe the issue or bug you encountered]

    Steps to reproduce:
    1. [Step 1]
    2. [Step 2]
    3. [Step 3]
    ...

    Expected behavior:
    [Describe the expected behavior]

    Actual behavior:
    [Describe the actual behavior you observed]

    Additional information:
    [Provide any additional information that might be helpful, such as screenshots, system configuration, or error messages]

    Please let me know if you need any further details or assistance.

    Thank you for your attention to this matter.
    """)
    recipient = 'nlh-team.npe@nikonglobal.onmicrosoft.com'

    # Get the log file paths
    log_file_handler = next((log_handler for log_handler in logger.handlers if isinstance(log_handler, RotatingFileHandler)), None)
    if log_file_handler:
        base_log_path = log_file_handler.baseFilename
        log_dir = os.path.dirname(base_log_path)
        base_log_name = os.path.basename(base_log_path)
        log_paths = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.startswith(base_log_name)]
    else:
        logging.error("Error: Log files not found.")
        return

    # Create the Outlook application and email item
    try:
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        # Configure the email
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body

        # Attach all log files
        for log_path in log_paths:
            try:
                if os.path.exists(log_path):
                    mail.Attachments.Add(log_path)
                    logging.info(f"Attached log file: {log_path}")
            except Exception as e:
                logging.error(f"Error attaching log file {log_path}: {e}")

        # Display the email for review and send
        mail.Display()  # Uncomment this line to display the email before sending
        # mail.Send()  # Uncomment this line to send the email automatically

        logging.info('Email created successfully!')
    except Exception as e:
        logging.error(f"Error creating or sending email: {e}")


def is_running_in_ide():
    """
    Heuristic to determine if the script is running in an IDE.
    This can be enhanced with more checks for different IDEs.
    """
    # Check for specific environment variables set by popular IDEs
    ide_env_vars = ['PYCHARM_HOSTED', 'VSCODE_PID', 'JPY_PARENT_PID']
    if any(var in os.environ for var in ide_env_vars):
        return True

    # Check if running in a Jupyter Notebook
    try:
        import ipykernel
        return True
    except ImportError:
        pass

    return False


def global_exception_handler(exctype: Optional[Type[BaseException]], value: Optional[BaseException],
                             tb: Optional[TracebackType], root=None, show_popup: bool = True, error_message: Optional[str] = None, log_exception=True):
    """
    Global exception handler for uncaught exceptions.

    This function handles uncaught exceptions by printing the exception and traceback,
    logging the exception, and optionally sending a bug report email with the error log attached.

    If --test_import_lib is in sys.argv, it uses save_import_test_result instead of showing a popup.

    Parameters:
        exctype (Type[BaseException]): The type of the exception.
        value (BaseException): The exception instance.
        tb (TracebackType): The traceback object.
        root (Tk): The root Tkinter window.
        show_popup (bool): Whether to show a popup message for the error. Default is True.
        error_message (str): Custom error message to display in the popup. If None, use default logic.
        log_exception (bool): Whether to log exception log or not
    Returns:
        None
    """
    if is_running_in_ide():
        # Print the traceback and error message if running in an IDE
        if error_message is not None:
            logging.error("Error Message: ", error_message)
        traceback.print_exception(exctype, value, tb)

    if log_exception:
        # Log the exception using the logger
        if error_message is not None:
            logger.error("Uncaught exception: %s", error_message, exc_info=(exctype, value, tb))
        else:
            logger.error("Uncaught exception", exc_info=(exctype, value, tb))

        # Check if the exception is an instance of NlhException and has an original traceback
        if isinstance(value, NlhException) and value.original_traceback:
            logger.error("Original traceback from NlhException:\n%s", value.original_traceback)

    if "--test_import_lib" in sys.argv:
        save_import_test_result("Library import test failed.")
    elif show_popup:
        def show_error_popup():
            """
            Display an error popup with the exception details.

            This function creates a Tkinter window to show the error message
            and provides options to report the error or close the window.
            """
            try:
                nonlocal root
                is_root_created_here = False

                if root is None:
                    root = tk.Tk()
                    root.withdraw()
                    is_root_created_here = True

                def show_message():
                    """
                    Create and display the error message window.

                    This function sets up the Tkinter window with the error message
                    and buttons for reporting the error or closing the window.
                    """
                    try:
                        # Create a new Toplevel window for the error dialog
                        error_window = tk.Toplevel(root)
                        error_window.title("Error")

                        # Set a fixed size for the window
                        error_window.geometry("500x200")
                        error_window.resizable(False, False)
                        error_window.grab_set()

                        # Get the background color of the error window
                        bg_color = error_window.cget("bg")
                        # Check if a custom error message is provided
                        if error_message:
                            message = error_message
                        else:
                            if exctype and issubclass(exctype, NlhException):
                                message = str(value)
                            else:
                                message = "NLH encountered an error. Please check the error log for more details."

                        log_file_handler = next((log_handler for log_handler in logger.handlers if isinstance(log_handler, RotatingFileHandler)), None)
                        if log_file_handler:
                            error_log_name = os.path.basename(log_file_handler.baseFilename)
                            message += f"\n\nFor more information, please check the error log: {error_log_name}"

                        text_frame = tk.Frame(error_window)
                        text_frame.pack(padx=5, pady=5, expand=True, fill="both")

                        # Create a Text widget for the message with transparent background
                        text_box = tk.Text(text_frame, wrap=tk.WORD, width=40, height=8,
                                           bg=bg_color, relief=tk.FLAT, borderwidth=0)
                        text_box.pack(side=tk.LEFT, expand=True, fill="both")

                        # Create a scrollbar and associate it with the Text widget
                        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_box.yview, width=15)
                        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                        text_box.configure(yscrollcommand=scrollbar.set)

                        text_box.insert(tk.END, message)
                        text_box.config(state=tk.DISABLED)  # Make it read-only

                        # Attempt to set system transparency (works on some systems)
                        try:
                            text_box.config(bg="systemtransparent")
                        except tk.TclError:
                            pass  # If 'systemtransparent' is not available, stick with the background color

                        def on_report():
                            """Handle the 'Report Error' button click."""
                            send_bug_report()
                            error_window.destroy()

                        def on_close():
                            """Handle the 'Close' button click."""
                            error_window.destroy()

                        # Create a frame to hold the buttons
                        button_frame = tk.Frame(error_window)
                        button_frame.pack(side='bottom', fill='x', padx=10, pady=10)

                        # Create a sub-frame to center the buttons
                        center_frame = tk.Frame(button_frame)
                        center_frame.pack(expand=True)

                        button_report_error = tk.Button(center_frame, text="Report Error", command=on_report)
                        button_report_error.pack(side='left', padx=5)

                        button_close = tk.Button(center_frame, text="Close", command=on_close)
                        button_close.pack(side='left', padx=5)

                        # Ensure the error window is destroyed when closed
                        error_window.protocol("WM_DELETE_WINDOW", on_close)

                        # Center the window on the screen
                        error_window.update_idletasks()
                        width = error_window.winfo_width()
                        height = error_window.winfo_height()
                        x = (error_window.winfo_screenwidth() // 2) - (width // 2)
                        y = (error_window.winfo_screenheight() // 2) - (height // 2)
                        error_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

                        # If root was created here, destroy it when the error window is closed
                        if is_root_created_here:
                            error_window.bind("<Destroy>", lambda e: root.destroy() if not error_window.winfo_exists() else None)

                    except Exception:
                        # Log the error without calling global_exception_handler
                        traceback.print_exc()

                root.after(0, show_message)

            except Exception:
                # Log the error without calling global_exception_handler
                traceback.print_exc()

        # Show the error popup in the main thread
        if threading.current_thread() is threading.main_thread():
            show_error_popup()
        else:
            if root is None:
                root = tk.Tk()
            root.after(0, show_error_popup)
            root.mainloop()


def save_import_test_result(message: str):
    """
    Save the result of the library import test to a log file.

    This function writes the outcome of the library import test to a log file, which is useful for debugging.

    Parameters:
        message (str): Outcome message of the test.

    Returns:
        None
    """
    with open("testing.log", 'w') as test_result_file:
        test_result_file.write("test_import_lib:" + message)


# Set the global exception handler
sys.excepthook = global_exception_handler
