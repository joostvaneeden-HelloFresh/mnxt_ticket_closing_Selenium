"""Browser automation for MobileNXT.

Credentials are passed in as parameters and are never stored.
The browser uses a temporary profile that is deleted when the session closes.
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
        # Stop Chrome from saving or offering to save passwords
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
        # TODO: fill in the login fields once we have the selectors (see inspect_login.py)
        raise NotImplementedError("Login selectors are not filled in yet")

    def close(self) -> None:
        try:
            self._driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)
