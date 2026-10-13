"""Keep packaged settings outside read-only bundles and temporary extraction paths."""

import os
from pathlib import Path
import sys


def settings_path():
    if not getattr(sys, "frozen", False):
        # Preserve existing developer settings when running from source.
        return Path(__file__).with_name("water_reminder_settings.json")
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "SipSidekick" / "settings.json"
