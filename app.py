"""GUI voor MobileNXT. Inloggegevens worden alleen in het geheugen gehouden."""
import datetime
import queue
import threading
import tkinter as tk
from tkinter import ttk

from mnxt_client import MnxtClient


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MobileNXT - tickets sluiten")
        self.geometry("560x420")
        self.minsize(480, 360)

        self._client = None
        self._busy = False
        self._queue = queue.Queue()

        self._build_widgets()
        self._update_buttons()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_queue)

    # ----- opbouw -------------------------------------------------------

    def _build_widgets(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(7, weight=1)

        ttk.Label(frame, text="Inloggen MobileNXT", font=("", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )

        ttk.Label(frame, text="Gebruikersnaam").grid(row=1, column=0, sticky="w", pady=(12, 0))
        self._user_entry = ttk.Entry(frame)
        self._user_entry.grid(row=2, column=0, sticky="ew")

        ttk.Label(frame, text="Wachtwoord").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self._pass_entry = ttk.Entry(frame, show="*")
        self._pass_entry.grid(row=4, column=0, sticky="ew")
        self._pass_entry.bind("<Return>", lambda _event: self._on_login())

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, sticky="w", pady=12)
        self._login_btn = ttk.Button(buttons, text="Inloggen", command=self._on_login)
        self._login_btn.pack(side="left")
        self._logout_btn = ttk.Button(buttons, text="Uitloggen", command=self._on_logout)
        self._logout_btn.pack(side="left", padx=8)

        ttk.Label(frame, text="Log").grid(row=6, column=0, sticky="w")
        self._log = tk.Text(frame, height=10, wrap="word", state="disabled")
        self._log.grid(row=7, column=0, sticky="nsew")

    # ----- knoppen en log ----------------------------------------------

    def _update_buttons(self):
        logged_in = self._client is not None
        self._login_btn.config(state="disabled" if (self._busy or logged_in) else "normal")
        self._logout_btn.config(state="normal" if (logged_in and not self._busy) else "disabled")

    def _log_line(self, text):
        tijd = datetime.datetime.now().strftime("%H:%M:%S")
        self._log.config(state="normal")
        self._log.insert("end", f"[{tijd}] {text}\n")
        self._log.see("end")
        self._log.config(state="disabled")

    # ----- inloggen -----------------------------------------------------

    def _on_login(self):
        if self._busy or self._client is not None:
            return

        username = self._user_entry.get().strip()
        password = self._pass_entry.get()
        # Wachtwoord meteen uit het veld halen; het leeft daarna alleen in deze functie
        self._pass_entry.delete(0, "end")

        if not username or not password:
            self._log_line("Vul gebruikersnaam en wachtwoord in.")
            return

        self._busy = True
        self._update_buttons()
        self._log_line("Bezig met inloggen...")
        threading.Thread(
            target=self._login_worker, args=(username, password), daemon=True
        ).start()

    def _login_worker(self, username, password):
        # Draait op een achtergrondthread: geen Tk-widgets aanraken, alleen de queue gebruiken
        client = None
        try:
            client = MnxtClient()
            client.login(username, password)
        except Exception as exc:
            if client is not None:
                client.close()
            self._queue.put(("error", f"Inloggen mislukt ({type(exc).__name__}: {exc})"))
        else:
            self._queue.put(("logged_in", client))
        finally:
            password = None

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "logged_in":
                    self._client = payload
                    self._busy = False
                    self._update_buttons()
                    self._log_line("Ingelogd. De sessie is actief.")
                elif kind == "error":
                    self._busy = False
                    self._update_buttons()
                    self._log_line(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # ----- uitloggen en sluiten ----------------------------------------

    def _close_client(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def _on_logout(self):
        self._close_client()
        self._update_buttons()
        self._log_line("Uitgelogd. Browser en tijdelijke sessiedata zijn verwijderd.")

    def _on_close(self):
        self._close_client()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
