import os

# MobileNXT base URL. Can be overridden with the MNXT_URL environment variable.
# Login credentials are not stored here; the GUI asks for them at login.
BASE_URL = os.environ.get("MNXT_URL", "https://hellofresh.mobilenext.eu/")
