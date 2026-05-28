"""
_loading_window.py

Startup loading window that runs discovery in a background thread,
shows a progress bar, and reports success or failure to the user.
"""

from __future__ import annotations

import time
import traceback
from typing import Callable

import customtkinter

from main_app_files.core_script_files.discovery import discovery
from main_app_files.function_files._threading_handler import thread_runner
from main_app_files.function_files.exception_handler_and_reporting import send_bug_report

# ── Constants ────────────────────────────────────────────────────────────────

_COLOUR_RED = ("#c0392b", "#e74c3c")
_COLOUR_GREEN = ("#27ae60", "#2ecc71")
_COLOUR_ORANGE = ("#d35400", "#e67e22")

_MIN_LOADING_SECONDS: int = 5


class LoadingWindow(customtkinter.CTkToplevel):
    """
    Modal-style startup window.

    Flow
    ----
    1. Opens, hides the main window.
    2. Runs discovery.discover() in a background thread via thread_runner.
       Records the start time so the screen is visible for at least
       _MIN_LOADING_SECONDS seconds.
    3. On clean success   → green counts, then auto-closes after the minimum
                            display time has elapsed.
       On partial failure → orange header, green counts, red error count,
                            centred red hint, OK + Report a Bug buttons.
       On total failure   → red header, error textbox, Report a Bug + Close.
    4. OK / auto-close restores the main window and calls on_load_complete.
       Close restores the main window without calling on_load_complete.
       Report a Bug calls send_bug_report() from exception_handler_and_reporting.

    Text / language
    ---------------
    All text is supplied by the caller via `widgets_text` (the loading_window
    sub-dict from languages.json).  No internal fallback exists — if a key is
    missing the KeyError surfaces immediately so the translation gap is caught
    and fixed rather than silently hidden.
    """

    def __init__(
            self,
            master,
            main_window_control_commend: dict,
            on_load_complete: Callable,
            widgets_text: dict,
            **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        self._ctrl = main_window_control_commend
        self._on_complete = on_load_complete
        self._text = widgets_text

        self._load_start: float = time.monotonic()

        self.geometry("450x100")
        self.title(self._text["title"])
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.__on_close)

        self._ctrl["withdraw"]()
        self.__build_ui()
        self.__start_discovery()

    # ── UI construction ──────────────────────────────────────────────────────

    def __build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Row 0 — header / status line
        self._status_label = customtkinter.CTkLabel(
            self,
            text=self._text["start_message"],
            wraplength=400,
            justify="center",
            anchor="center",
        )
        self._status_label.grid(row=0, column=0, padx=20, pady=(20, 2), sticky="ew")

        # Row 1 — green counts (handlers + tools) — hidden until needed
        self._counts_label = customtkinter.CTkLabel(
            self,
            text="",
            wraplength=400,
            justify="center",
            anchor="center",
            text_color=_COLOUR_GREEN,
        )
        self._counts_label.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self._counts_label.grid_remove()

        # Row 2 — red error count line — hidden until needed
        self._error_count_label = customtkinter.CTkLabel(
            self,
            text="",
            wraplength=400,
            justify="center",
            anchor="center",
            text_color=_COLOUR_RED,
        )
        self._error_count_label.grid(row=2, column=0, padx=20, pady=0, sticky="ew")
        self._error_count_label.grid_remove()

        # Row 3 — progress bar
        self._progress = customtkinter.CTkProgressBar(
            self, width=380, mode="indeterminate"
        )
        self._progress.grid(row=3, column=0, padx=20, pady=(8, 10), sticky="ew")
        self._progress.start()

        # Row 4 — centred red hint for partial failures
        self._error_hint_label = customtkinter.CTkLabel(
            self,
            text=self._text["load_error_hint"],
            wraplength=400,
            justify="center",
            anchor="center",
            text_color=_COLOUR_RED,
        )
        self._error_hint_label.grid(row=4, column=0, padx=20, pady=(4, 2), sticky="ew")
        self._error_hint_label.grid_remove()

        # Row 5 — error detail heading (total failure only)
        self._error_label = customtkinter.CTkLabel(
            self,
            text=self._text["error_detail_label"],
            anchor="w",
        )
        self._error_label.grid(row=5, column=0, padx=20, pady=(4, 2), sticky="w")
        self._error_label.grid_remove()

        # Row 6 — error detail textbox (total failure only)
        self._error_box = customtkinter.CTkTextbox(self, width=380, height=120)
        self._error_box.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self._error_box.grid_remove()

        # Row 7 — buttons (all hidden until a result is ready)
        self._btn_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self._btn_frame.grid(row=7, column=0, padx=20, pady=(4, 20))

        self._ok_btn = customtkinter.CTkButton(
            self._btn_frame,
            text=self._text["ok_button"],
            command=self.__on_ok,
        )
        self._report_bug_btn = customtkinter.CTkButton(
            self._btn_frame,
            text=self._text["report_bug_button"],
            command=self.__on_report_bug,
        )
        self._close_btn = customtkinter.CTkButton(
            self._btn_frame,
            text=self._text["close_button"],
            command=self.__on_close,
        )

        self._ok_btn.grid(row=0, column=0, padx=6)
        self._report_bug_btn.grid(row=0, column=1, padx=6)
        self._close_btn.grid(row=0, column=2, padx=6)

        self._ok_btn.grid_remove()
        self._report_bug_btn.grid_remove()
        self._close_btn.grid_remove()

    # ── Discovery ────────────────────────────────────────────────────────────

    def __start_discovery(self) -> None:
        thread_runner(
            master=self,
            func=self.__run_discovery,
            gui_callback=self.__on_discovery_done,
        )

    @staticmethod
    def __run_discovery() -> dict:
        try:
            discovery.discover()
            handler_count = sum(
                len(h) for h in discovery.log_handlers_dict.values()
            )
            return {
                "success": True,
                "handler_count": handler_count,
                "tool_count": len(discovery.tools_list),
                "error_count": len(discovery.load_errors),
                "load_errors": list(discovery.load_errors),
            }
        except Exception:
            return {
                "success": False,
                "traceback": traceback.format_exc(),
            }

    def __on_discovery_done(self, result) -> None:
        """
        Called on the main thread when the background discovery thread finishes.
        Waits for the minimum display time before rendering the result.
        """
        elapsed_ms = int((time.monotonic() - self._load_start) * 1000)
        remaining_ms = max(0, _MIN_LOADING_SECONDS * 1000 - elapsed_ms)
        self.after(remaining_ms, lambda: self.__render_result(result))

    def __render_result(self, result) -> None:
        """Render success or failure UI after the minimum loading delay."""

        # Always stop and hide the progress bar first
        self._progress.stop()
        self._progress.grid_remove()

        if isinstance(result, Exception):
            self.__show_total_failure(str(result))
            return

        if result.get("success"):
            self.__show_success(result)
        else:
            self.__show_total_failure(result.get("traceback", "Unknown error"))

    # ── Result rendering ─────────────────────────────────────────────────────

    def __show_success(self, result: dict) -> None:
        if result["load_errors"]:
            # ── Partial success ──────────────────────────────────────────────
            self._status_label.configure(
                text=self._text["partial_message"],
                text_color=_COLOUR_ORANGE,
            )
            self._counts_label.configure(
                text=(
                    f"{self._text['handler_count'].format(count=result['handler_count'])}\n"
                    f"{self._text['tool_count'].format(count=result['tool_count'])}"
                ),
                text_color=_COLOUR_GREEN,
            )
            self._counts_label.grid()
            self._error_count_label.configure(
                text=self._text["error_count"].format(count=result["error_count"]),
                text_color=_COLOUR_RED,
            )
            self._error_count_label.grid()
            self._error_hint_label.grid()
            self.geometry("450x200")
            self._ok_btn.grid()
            self._report_bug_btn.grid()

        else:
            # ── Clean success ─────────────────────────────────────────────────
            self._status_label.configure(
                text=(
                    f"{self._text['success_message']}\n"
                    f"{self._text['handler_count'].format(count=result['handler_count'])}\n"
                    f"{self._text['tool_count'].format(count=result['tool_count'])}"
                ),
                text_color=_COLOUR_GREEN,
            )
            self.geometry("450x160")
            # Small delay so user sees the green success message before close
            self.after(800, self.__on_ok)

    def __show_total_failure(self, detail: str) -> None:
        # Progress bar already stopped in __render_result
        self._status_label.configure(
            text=self._text["fail_message"],
            text_color=_COLOUR_RED,
        )
        self.__populate_error_box(detail)
        self.geometry("450x330")
        self._report_bug_btn.grid()
        self._close_btn.grid()

    def __populate_error_box(self, text: str) -> None:
        self._error_label.grid()
        self._error_box.grid()
        self._error_box.configure(state="normal")
        self._error_box.delete("1.0", "end")
        self._error_box.insert("end", text)
        self._error_box.configure(state="disabled")

    # ── Button handlers ──────────────────────────────────────────────────────

    def __on_ok(self) -> None:
        """Restore the main window, fire the completion callback, and close."""
        self._ctrl["deiconify"]()
        self._on_complete()
        self.destroy()

    @staticmethod
    def __on_report_bug() -> None:
        """Open the bug-report email with logs attached via the exception handler."""
        send_bug_report()

    def __on_close(self) -> None:
        """Restore the main window and close without calling on_load_complete."""
        self._ctrl["deiconify"]()
        self.destroy()
