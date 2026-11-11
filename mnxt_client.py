"""Browserbesturing voor MobileNXT.

Inloggegevens worden alleen als parameter doorgegeven en nergens opgeslagen.
De browser gebruikt een tijdelijk profiel dat we bij sluiten weer verwijderen.
"""
import shutil
import tempfile

from selenium import webdriver

from config import BASE_URL


class MnxtClient:
    def __init__(self):
        self._profile_dir = tempfile.mkdtemp(prefix="mnxt_")
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={self._profile_dir}")
        # Chrome mag geen wachtwoorden onthouden of aanbieden om op te slaan
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            },
        )
        self._driver = webdriver.Chrome(options=options)

    def login(self, username: str, password: str) -> None:
        self._driver.get(BASE_URL)
        # TODO: inlogvelden invullen zodra we de selectors hebben (via inspect_login.py)
        raise NotImplementedError("Login-selectors zijn nog niet ingevuld")

    def close(self) -> None:
        try:
            self._driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)
