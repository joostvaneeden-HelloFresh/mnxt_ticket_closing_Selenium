"""Helper script: opens the login page and lists its input fields and buttons.

Purpose: find the right selectors for logging in. Nothing is filled in or clicked.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from config import BASE_URL

driver = webdriver.Chrome()
try:
    driver.get(BASE_URL)
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    print("Current URL:", driver.current_url)
    print("Title:", driver.title)
    print("Number of iframes:", len(driver.find_elements(By.TAG_NAME, "iframe")))

    print("\n--- Input fields ---")
    for el in driver.find_elements(By.TAG_NAME, "input"):
        attrs = {a: el.get_attribute(a) for a in ("type", "name", "id", "placeholder", "autocomplete")}
        print(attrs, "| visible:", el.is_displayed())

    print("\n--- Buttons and links with text ---")
    for el in driver.find_elements(By.CSS_SELECTOR, "button, a[href]"):
        text = el.text.strip()
        if text:
            print(el.tag_name, repr(text))

    input("\nPress Enter to close the browser...")
finally:
    driver.quit()
