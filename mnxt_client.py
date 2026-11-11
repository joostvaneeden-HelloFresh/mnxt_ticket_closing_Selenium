"""Browser automation for MobileNXT.

Credentials are passed in as parameters and are never stored.
The browser uses a temporary profile that is deleted when the session closes.
"""
import re
import shutil
import tempfile
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import BASE_URL

# The app loads its menus and tabs after the login, so wait generously for them
WAIT_SECONDS = 30
# Only buttons with one of these words are clicked to close a popup.
# Buttons that change the password are never clicked.
DISMISS_WORDS = ("later", "remind", "skip", "not now", "close", "dismiss")

# Durations in the ticket list look like "146d 3h 52m", "42m" or "6m"
DURATION_PART = re.compile(r"(\d+)\s*([dhm])\b")
UNIT_MINUTES = {"d": 1440, "h": 60, "m": 1}
TICKET_ROWS = "(//mat-row | //tbody/tr)"


def duration_minutes(text: str) -> int:
    """Convert a duration such as '146d 3h 52m' to minutes."""
    return sum(int(number) * UNIT_MINUTES[unit] for number, unit in DURATION_PART.findall(text))


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
                # Stop Chrome from checking passwords against known data breaches
                # (this is what shows the "Change your password" popup)
                "profile.password_manager_leak_detection": False,
            },
        )
        self._driver = webdriver.Chrome(options=options)

    def _click_when_ready(self, locator, description: str) -> None:
        """Wait until the element is visible and clickable, then click it."""
        self._dismiss_popups()
        wait = WebDriverWait(self._driver, WAIT_SECONDS)
        try:
            element = wait.until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            raise RuntimeError(
                f"Could not find {description} within {WAIT_SECONDS} seconds"
            ) from None
        element.click()

    def login(self, username: str, password: str) -> None:
        wait = WebDriverWait(self._driver, WAIT_SECONDS)
        self._driver.get(BASE_URL)

        try:
            username_field = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[autocomplete='email']"))
            )
        except TimeoutException:
            raise RuntimeError(
                f"The login page did not show the username field within {WAIT_SECONDS} seconds"
            ) from None
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

        # Close the popup that can appear right after login, if there is one
        self._dismiss_popups()

    def open_customer_ticketing(self) -> None:
        self._click_when_ready(
            (By.XPATH, "//*[normalize-space()='Customer Ticketing System']"),
            "the 'Customer Ticketing System' menu item",
        )

    def open_other_department_tab(self) -> None:
        self._click_when_ready(
            (
                By.XPATH,
                "//*[@role='tab' or self::a or self::button]"
                "[contains(normalize-space(.), 'Other Department')]",
            ),
            "the 'Other Department' tab",
        )

    def enable_include_future_mutations(self) -> None:
        # The toggle is found by its label text; clicking the label switches it
        self._click_when_ready(
            (By.XPATH, "//label[contains(normalize-space(.), 'Include future mutations')]"),
            "the 'Include future mutations' toggle",
        )

    def sort_by_duration_oldest_first(self) -> None:
        # The first click sorts ascending, the second descending, so the oldest tickets come first
        header = (
            By.XPATH,
            "//th[contains(normalize-space(.), 'Duration')]"
            " | //*[@role='columnheader'][contains(normalize-space(.), 'Duration')]",
        )
        self._click_when_ready(header, "the 'Duration' column header")
        self._click_when_ready(header, "the 'Duration' column header")

    def _wait_for_settled_list(self) -> None:
        """Wait until the ticket list is sorted oldest first and has stopped changing.

        Raises an error if that does not happen in time, so we never act on a
        list that may still be reordering.
        """
        end = time.monotonic() + WAIT_SECONDS
        previous = None
        while time.monotonic() < end:
            try:
                rows = self._driver.find_elements(By.XPATH, TICKET_ROWS)
                snapshot = [row.text for row in rows]
            except StaleElementReferenceException:
                snapshot = None

            if snapshot:
                durations = [duration_minutes(text) for text in snapshot]
                sorted_oldest_first = all(a >= b for a, b in zip(durations, durations[1:]))
                if sorted_oldest_first and snapshot == previous:
                    return
            previous = snapshot
            time.sleep(1)

        raise RuntimeError(
            f"The ticket list did not settle in oldest-first order within {WAIT_SECONDS} seconds"
        )

    def open_first_ticket(self) -> str:
        """Open the top ticket in the list and return its ID (for the log)."""
        self._dismiss_popups()
        self._wait_for_settled_list()

        row = self._driver.find_element(By.XPATH, f"{TICKET_ROWS}[1]")
        match = re.search(r"HF-\d+", row.text)
        ticket_id = match.group(0) if match else "unknown ID"
        row.click()
        return ticket_id

    def _dismiss_popups(self) -> None:
        """Close a popup that covers the page, such as a password breach notice.

        Does nothing if no popup appears. Only buttons whose text clearly closes
        the popup are clicked. If none is found, the error lists the button texts.
        """
        # Check once, without waiting: most of the time there is no popup
        dialogs = [
            d
            for d in self._driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], mat-dialog-container")
            if d.is_displayed()
        ]
        if not dialogs:
            return
        dialog = dialogs[0]

        buttons = dialog.find_elements(By.CSS_SELECTOR, "button")
        for button in buttons:
            label = button.text.strip().lower()
            if any(word in label for word in DISMISS_WORDS):
                button.click()
                WebDriverWait(self._driver, WAIT_SECONDS).until(EC.invisibility_of_element(dialog))
                return

        labels = [b.text.strip() for b in buttons if b.text.strip()]
        raise RuntimeError(f"A popup appeared without a close button. Its buttons: {labels}")

    def save_screenshot(self, path: str) -> None:
        self._driver.save_screenshot(path)

    def close(self) -> None:
        try:
            self._driver.quit()
        finally:
            shutil.rmtree(self._profile_dir, ignore_errors=True)
