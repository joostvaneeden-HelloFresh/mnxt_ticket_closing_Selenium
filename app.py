"""GUI for MobileNXT. Credentials are kept in memory only."""
import datetime
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk

from mnxt_client import MnxtClient

ERROR_SCREENSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_screenshot.png")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MobileNXT - ticket closing")
        self.geometry("560x420")
        self.minsize(480, 360)

        self._client = None
        self._busy = False
        self._queue = queue.Queue()

        self._build_widgets()
        self._update_buttons()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_queue)

    # ----- layout -------------------------------------------------------

    def _build_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(7, weight=1)

        ttk.Label(frame, text="Log in to MobileNXT", font=("", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        ttk.Label(frame, text="Username").grid(row=1, column=0, sticky="w", pady=(12, 0))
        self._user_entry = ttk.Entry(frame)
        self._user_entry.grid(row=2, column=0, sticky="ew")

        ttk.Label(frame, text="Password").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self._pass_entry = ttk.Entry(frame, show="*")
        self._pass_entry.grid(row=4, column=0, sticky="ew")
        self._pass_entry.bind("<Return>", lambda _event: self._on_login())

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, sticky="w", pady=12)
        self._login_btn = ttk.Button(buttons, text="Log in", command=self._on_login)
        self._login_btn.pack(side="left")
        self._logout_btn = ttk.Button(buttons, text="Log out", command=self._on_logout)
        self._logout_btn.pack(side="left", padx=8)

        ttk.Label(frame, text="Log").grid(row=6, column=0, sticky="w")
        self._log = tk.Text(frame, height=10, wrap="word", state="disabled")
        self._log.grid(row=7, column=0, sticky="nsew")

    # ----- buttons and log ----------------------------------------------

    def _update_buttons(self):
        logged_in = self._client is not None
        self._login_btn.config(state="normal" if (not self._busy and not logged_in) else "disabled")
        self._logout_btn.config(state="normal" if (not self._busy and logged_in) else "disabled")

    def _log_line(self, text):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self._log.config(state="normal")
        self._log.insert("end", f"[{timestamp}] {text}\n")
        self._log.see("end")
        self._log.config(state="disabled")

    # ----- login and navigation -----------------------------------------

    def _on_login(self):
        if self._busy or self._client is not None:
            return

        username = self._user_entry.get().strip()
        password = self._pass_entry.get()
        # Remove the password from the field right away; it only lives in local variables now
        self._pass_entry.delete(0, "end")

        if not username or not password:
            self._log_line("Please enter a username and password.")
            return

        self._busy = True
        self._update_buttons()
        self._log_line("Logging in...")
        threading.Thread(
            target=self._login_worker, args=(username, password), daemon=True
        ).start()

    def _login_worker(self, username, password):
        # Runs on a background thread: do not touch Tk widgets, only use the queue
        client = None
        try:
            client = MnxtClient()
            client.login(username, password)
            self._queue.put(("step", "Logged in. Opening Customer Ticketing System..."))
            client.open_customer_ticketing()
            self._queue.put(("step", "Opening tab 'Other Department'..."))
            client.open_other_department_tab()
            self._queue.put(("step", "Switching on 'Include future mutations'..."))
            client.enable_include_future_mutations()
            self._queue.put(("step", "Sorting by 'Duration' (oldest first)..."))
            client.sort_by_duration_oldest_first()
            self._queue.put(("step", "Opening the top ticket..."))
            ticket_id = client.open_first_ticket()
            self._queue.put(("step", f"Opened ticket {ticket_id}."))
        except Exception as exc:
            if client is not None:
                try:
                    client.save_screenshot(ERROR_SCREENSHOT)
                except Exception:
                    pass
                client.close()
            # Only the first line of the message: Selenium adds a long stacktrace after it
            details = (str(exc).strip().splitlines() or [""])[0]
            self._queue.put(("error", f"Failed: {details}"))
        else:
            self._queue.put(("ready", client))
        finally:
            password = None

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "step":
                    self._log_line(payload)
                elif kind == "ready":
                    self._client = payload
                    self._busy = False
                    self._update_buttons()
                    self._log_line("Ready: the oldest ticket is open. Session is active.")
                elif kind == "error":
                    self._busy = False
                    self._update_buttons()
                    self._log_line(payload)
                    self._log_line(f"Screenshot saved to: {ERROR_SCREENSHOT}")
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # ----- logout and close ---------------------------------------------

    def _close_client(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def _on_logout(self):
        self._close_client()
        self._update_buttons()
        self._log_line("Logged out. Browser and temporary session data have been removed.")

    def _on_close(self):
        self._close_client()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
