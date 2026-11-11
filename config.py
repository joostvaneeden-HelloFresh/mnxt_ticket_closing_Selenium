import os

# URL van MobileNXT. Kan overschreven worden met de environment variable MNXT_URL.
BASE_URL = os.environ.get("MNXT_URL", "https://hellofresh.mobilenext.eu/")

# Inloggegevens komen uit environment variables, nooit uit de code.
USERNAME = os.environ.get("MNXT_USERNAME")
PASSWORD = os.environ.get("MNXT_PASSWORD")
