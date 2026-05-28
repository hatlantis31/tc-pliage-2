"""
This file has General functions to use with NLH that aren't GUI
"""
import logging
import threading
import traceback
import queue

from main_app_files.function_files.exception_handler_and_reporting import global_exception_handler

# Global list to keep track of all running threads
RUNNING_THREADS = []


def thread_runner(master, func, gui_callback, args=(), kwargs=None):
    """
    Runs a function in a separate thread and uses a callback to update the GUI
    when the function is finished. If the function raises an exception, the
    exception is printed with traceback.

    :param master: The Tk root widget.
    :param func: The function to run in a separate thread.
    :param gui_callback: The callback function to run when 'func' is finished.
                         This function should accept as meny argument as you like, which will be
                         the result of 'func'.
    :param args: Additional positional arguments to pass to 'func'.
    :param kwargs: Additional keyword arguments to pass to 'func'.
    """
    if kwargs is None:
        kwargs = {}
    q = queue.Queue()  # Queue to hold the result of 'func'

    def wrapper():
        """
        Runs 'func' and puts its result on a queue. If 'func' raises an exception,
        the exception is put on the queue instead.
        """
        try:
            result = func(*args, **kwargs)  # Run the function
            q.put((False, result, None))  # Put the result on the queue
        except Exception as e:
            exc_traceback = traceback.format_exc()  # Get formatted traceback
            q.put((True, e, exc_traceback))
        finally:
            RUNNING_THREADS.remove(t)

    # Start the new thread
    t = threading.Thread(target=wrapper)
    RUNNING_THREADS.append(t)
    t.start()

    def check_thread():
        """
        Checks if the thread 't' is still running. If it is, it schedules another
        check in 100ms. If 't' has finished, it gets the result from the queue and
        calls 'gui_callback' with the result. If an error occurred, it prints the
        error and traceback.
        """
        if t.is_alive():
            # Reschedule check_thread to run again after 100ms
            master.after(100, check_thread)
        else:
            # Get the result from the queue
            is_error, result, tb = q.get()
            if is_error:
                # An error occurred, so print the error and traceback
                gui_callback(result)
                # raise result
                # logging.error("An error occurred in the thread:\n" + tb)  # Print the traceback
            else:
                # No error occurred, so call the GUI callback with the result
                if isinstance(result, tuple):
                    gui_callback(*result)  # Pass the result as separate arguments
                else:
                    gui_callback(result)  # Pass the result as a single argument

    # Start checking if the thread has finished
    check_thread()


class ReturnValueThread(threading.Thread):
    """
    class is an addon to the Thread class in order to get value when join is called.
    """

    def __init__(self, *args: object, **kwargs: object):
        super(ReturnValueThread, self).__init__(*args, **kwargs)
        self.result = None
        self._stop_event = threading.Event()
        RUNNING_THREADS.append(self)

    def run(self):
        """
        Overrides the run method of threading.Thread.

        This method executes the target function of the thread and stores its result.
        If an exception occurs during execution, it logs the error.
        Finally, it removes itself from the RUNNING_THREADS list.
        """
        if self._target is None:
            return  # could alternatively raise an exception, depends on the use case
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc:
            logging.error(f'{type(exc).__name__}: {exc}')  # properly handle the exception
        finally:
            RUNNING_THREADS.remove(self)

    def join(self, *args, **kwargs):
        """
        Overrides the join method of threading.Thread.

        Waits for the thread to complete and returns the result of the thread's execution.

        :param args: Positional arguments to pass to the superclass join method.
        :param kwargs: Keyword arguments to pass to the superclass join method.
        :return: The result of the thread's target function execution.
        """
        super().join(*args, **kwargs)
        return self.result

    def stop(self):
        """
        Signals the thread to stop execution.

        This method sets an internal event flag that can be used to indicate
        that the thread should terminate.
        """
        self._stop_event.set()

    def stopped(self):
        """
        Checks if the thread has been signaled to stop.

        :return: True if the thread has been signaled to stop, False otherwise.
        """
        return self._stop_event.is_set()


def stop_all_threads():
    """
    Stops all running threads.
    """
    for thread in RUNNING_THREADS:
        if thread.is_alive():
            try:
                thread._stop()
            except:
                pass

    # Force quit any threads that didn't finish
    for thread in threading.enumerate():
        if thread != threading.main_thread():
            try:
                thread._stop()
            except:
                pass
