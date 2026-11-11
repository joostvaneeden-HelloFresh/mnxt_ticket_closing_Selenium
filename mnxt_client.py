"""Browser automation for MobileNXT.

Credentials are passed in as parameters and are never stored.
The browser uses a temporary profile that is deleted when the session closes.
"""
import shutil
import tempfile

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import BASE_URL

WAIT_SECONDS = 20


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
        wait = WebDriverWait(self._driver, WAIT_SECONDS)
        self._driver.get(BASE_URL)

        username_field = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[autocomplete='email']"))
        )
        username_field.clear()
        username_field.send_keys(username)

        password_field = self._driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.clear()
        password_field.send_keys(password)

        self._driver.find_element(By.XPATH, "//button[normalize-space()='Sign in']").click()

        # The login form disappears once the login has succeeded
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
        except TimeoutException:
            raise RuntimeError("Login did not complete. Check the username and password.") from None

    def open_customer_ticketing(self) -> None:
        wait = WebDriverWait(self._driver, WAIT_SECONDS)
        menu_item = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space()='Customer Ticketing System']")
            )
        )
        menu_item.click()

    def close(self) -> None:
        try:
            self._driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)
