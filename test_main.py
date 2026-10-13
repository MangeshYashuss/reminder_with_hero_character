import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from main import CHARACTERS, ReminderSettings, next_daily_occurrence, normalize_time, normalize_times
from reminder_styles import PRESENTATIONS, entrance_pose, revealed_message
from choreography import animation_phase, desktop_pose, landing_transform, LANDING_SECONDS, MESSAGE_SECONDS


class CharacterPresentationTests(unittest.TestCase):
    def test_message_waits_for_arrival_and_landing(self):
        arrival = 2.6
        self.assertEqual(animation_phase(arrival - .01, arrival)[0], "arrival")
        self.assertEqual(animation_phase(arrival, arrival), ("landing", 0))
        self.assertEqual(animation_phase(arrival + LANDING_SECONDS - .01, arrival)[0], "landing")
        self.assertEqual(animation_phase(arrival + LANDING_SECONDS, arrival), ("message", 0))
        self.assertEqual(animation_phase(arrival + LANDING_SECONDS + MESSAGE_SECONDS + .1, arrival), ("message", 1))

    def test_spiderman_enters_from_screen_top_hangs_then_lands(self):
        start = desktop_pose("web", 0, 1100, 700, 1920, 1080)
        hanging = desktop_pose("web", .5, 1100, 700, 1920, 1080)
        fall = desktop_pose("web", .85, 1100, 700, 1920, 1080)
        end = desktop_pose("web", 1, 1100, 700, 1920, 1080)
        self.assertLess(start.y, 0)
        self.assertLess(hanging.y, fall.y)
        self.assertLess(fall.y, end.y)
        self.assertEqual((end.x, end.y), (1100, 700))

    def test_desktop_paths_finish_at_same_position_and_landing_recovers(self):
        for style in PRESENTATIONS.values():
            with self.subTest(character=style.entrance):
                pose = desktop_pose(style.entrance, 1, 1000, 600, 1536, 864)
                self.assertAlmostEqual(pose.x, 1000)
                self.assertAlmostEqual(pose.y, 600)
                self.assertEqual(pose.scale, 1)
                self.assertEqual(landing_transform(style.entrance, 1), (1, 1))
                self.assertLess(landing_transform(style.entrance, .4)[1], 1)

    def test_every_selectable_character_has_a_distinct_presentation(self):
        self.assertEqual(set(CHARACTERS), set(PRESENTATIONS))
        for field in ("message", "entrance", "reveal"):
            self.assertEqual(len({getattr(style, field) for style in PRESENTATIONS.values()}), len(CHARACTERS))

    def test_all_entrances_settle_and_clamp_at_the_resting_pose(self):
        for style in PRESENTATIONS.values():
            with self.subTest(style=style.entrance):
                for progress in (1.0, 2.0):
                    x, y, scale = entrance_pose(style.entrance, progress)
                    self.assertAlmostEqual(x, 0)
                    self.assertAlmostEqual(y, 0)
                    self.assertAlmostEqual(scale, 1)

    def test_custom_text_is_complete_after_reveal(self):
        message = "My custom reminder: take  a sip!"
        for style in PRESENTATIONS.values():
            with self.subTest(style=style.reveal):
                self.assertEqual(revealed_message(message, style, 0), "")
                self.assertEqual(revealed_message(message, style, 1), message)


class SchedulingTests(unittest.TestCase):
    def test_normalize_time(self):
        self.assertEqual(normalize_time(" 09:05 "), "09:05")
        with self.assertRaises(ValueError):
            normalize_time("25:00")

    def test_normalize_times_sorts_and_removes_duplicates(self):
        self.assertEqual(normalize_times(["14:00", "09:00", "14:00", "bad"]), ["09:00", "14:00"])

    def test_next_daily_occurrence_same_day(self):
        now = datetime(2026, 10, 13, 10, 30)
        self.assertEqual(next_daily_occurrence(now, ["09:00", "14:00"]), datetime(2026, 10, 13, 14, 0))

    def test_next_daily_occurrence_rolls_to_tomorrow(self):
        now = datetime(2026, 10, 13, 18, 0)
        self.assertEqual(next_daily_occurrence(now, ["09:00", "14:00"]), datetime(2026, 10, 14, 9, 0))

    def test_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.json"
            expected = ReminderSettings(character="cat", schedule_mode="daily", daily_times=["09:00", "15:30"], enabled=True)
            expected.save(path)
            self.assertEqual(ReminderSettings.load(path), expected)


if __name__ == "__main__":
    unittest.main()
