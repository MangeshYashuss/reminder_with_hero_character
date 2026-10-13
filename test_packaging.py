import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app_paths import settings_path
from main import ReminderSettings


class PackagingTests(unittest.TestCase):
    def test_developer_settings_stay_in_workspace(self):
        with patch("sys.frozen", False, create=True):
            self.assertEqual(settings_path(), Path(__file__).with_name("water_reminder_settings.json"))

    def test_windows_bundle_uses_local_app_data(self):
        with patch("sys.frozen", True, create=True), patch("sys.platform", "win32"):
            with patch.dict(os.environ, {"LOCALAPPDATA": str(Path(tempfile.gettempdir()) / "test-user")}):
                self.assertEqual(settings_path(), Path(os.environ["LOCALAPPDATA"]) / "SipSidekick" / "settings.json")

    def test_mac_bundle_uses_application_support(self):
        with patch("sys.frozen", True, create=True), patch("sys.platform", "darwin"):
            self.assertEqual(settings_path(), Path.home() / "Library" / "Application Support" / "SipSidekick" / "settings.json")

    def test_first_save_creates_settings_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "new-profile" / "settings.json"
            settings = ReminderSettings()
            settings.save(path)
            self.assertEqual(ReminderSettings.load(path), settings)
