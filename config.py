import os

# URL van MobileNXT. Kan overschreven worden met de environment variable MNXT_URL.
# Inloggegevens worden niet hier opgeslagen; de GUI vraagt ze bij het inloggen.
BASE_URL = os.environ.get("MNXT_URL", "https://hellofresh.mobilenext.eu/")
