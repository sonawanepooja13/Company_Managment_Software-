"""Local configuration for the shared Supabase service.

The configuration file is intentionally kept beside the executable, not in
source control.  It contains only the Supabase publishable client key; never
put a Supabase service-role key in a desktop application.
"""

import json
import os


PROJECT_URL = "https://xiidlqtjirkruojpymax.supabase.co"
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_settings.json")


def load_cloud_settings():
    settings = {"supabase_url": PROJECT_URL, "supabase_publishable_key": ""}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, encoding="utf-8") as file:
            settings.update(json.load(file))
    return settings


def cloud_is_configured():
    return bool(load_cloud_settings().get("supabase_publishable_key", "").strip())
