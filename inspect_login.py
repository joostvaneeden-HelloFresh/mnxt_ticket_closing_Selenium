"""Hulpscript: opent de loginpagina en laat zien welke velden en knoppen er staan.

Doel: de juiste selectors vinden voor het inloggen. Er wordt niets ingevuld of geklikt.
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

    print("Huidige URL:", driver.current_url)
    print("Titel:", driver.title)
    print("Aantal iframes:", len(driver.find_elements(By.TAG_NAME, "iframe")))

    print("\n--- Input-velden ---")
    for el in driver.find_elements(By.TAG_NAME, "input"):
        attrs = {a: el.get_attribute(a) for a in ("type", "name", "id", "placeholder", "autocomplete")}
        print(attrs, "| zichtbaar:", el.is_displayed())

    print("\n--- Knoppen en links met tekst ---")
    for el in driver.find_elements(By.CSS_SELECTOR, "button, a[href]"):
        tekst = el.text.strip()
        if tekst:
            print(el.tag_name, repr(tekst))

    input("\nDruk op Enter om de browser te sluiten...")
finally:
    driver.quit()
