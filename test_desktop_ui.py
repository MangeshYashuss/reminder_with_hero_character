"""Native-widget regression tests; never read or write the user's settings."""

import tkinter as tk
import unittest
from datetime import datetime
from unittest.mock import patch

from main import CHARACTERS, ReminderSettings, WaterReminderApp


class DesktopUITests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"A desktop display is required: {error}")
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.save_patch = patch.object(ReminderSettings, "save")
        self.save_mock = self.save_patch.start()
        self.addCleanup(self.save_patch.stop)
        with patch.object(ReminderSettings, "load", return_value=ReminderSettings()):
            self.app = WaterReminderApp(self.root)
        self.root.update()

    def tearDown(self):
        if hasattr(self, "app"):
            if self.app.popup:
                self.app.popup.dismiss()
            for job in self.root.tk.call("after", "info"):
                self.root.after_cancel(job)
            self.root.destroy()
            self.assertEqual(self.errors, [])

    def test_all_groups_select_heroes_and_update_spotlight(self):
        for group in ("Marvel", "DC", "Originals"):
            self.app.view.tab_buttons[group].invoke()
            self.root.update()
            visible = [key for key, tile in self.app.view.tiles.items() if tile.winfo_ismapped()]
            self.assertEqual(len(visible), 4)
            for key in visible:
                tile = self.app.view.tiles[key]
                tile.event_generate("<Button-1>", x=20, y=20)
                self.assertEqual(self.app.character_var.get(), key)
                texts = [self.app.view.spotlight.itemcget(item, "text")
                         for item in self.app.view.spotlight.find_all()
                         if self.app.view.spotlight.type(item) == "text"]
                self.assertIn(CHARACTERS[key]["name"], texts)

    def test_presets_modes_and_daily_time_editing(self):
        self.app.view.preset_buttons[45].invoke()
        self.assertEqual(self.app.interval_var.get(), 45)
        self.app.view.mode_buttons["daily"].invoke()
        self.root.update()
        self.assertTrue(self.app.daily_frame.winfo_ismapped())
        self.assertFalse(self.app.interval_frame.winfo_ismapped())
        self.app.new_time_var.set("20:30")
        self.app._add_time()
        self.assertIn("20:30", [var.get() for var in self.app.time_vars])
        self.app._remove_time_row(self.app.time_list.winfo_children()[-1])
        self.assertNotIn("20:30", [var.get() for var in self.app.time_vars])
        self.app.view.mode_buttons["interval"].invoke()
        self.root.update()
        self.assertTrue(self.app.interval_frame.winfo_ismapped())

    def test_save_and_start_pause_update_controller(self):
        self.app.interval_var.set(30)
        self.app.message_var.set("A quick water break")
        self.app._save_settings()
        self.save_mock.assert_called_once()
        self.assertEqual(self.app.settings.interval_minutes, 30)
        self.assertEqual(self.app.settings.reminder_text, "A quick water break")
        self.app._toggle_reminders()
        self.assertTrue(self.app.settings.enabled)
        self.assertGreater(self.app.next_reminder, datetime.now())
        self.assertIn("ACTIVE", self.app.view.state_badge.cget("text"))
        self.app._toggle_reminders()
        self.assertFalse(self.app.settings.enabled)
        self.assertIsNone(self.app.next_reminder)

    def test_invalid_input_does_not_save(self):
        self.app.interval_var.set(0)
        with patch("main.messagebox.showerror") as error:
            self.app._save_settings()
        error.assert_called_once()
        self.save_mock.assert_not_called()

    def test_small_window_scrolls_but_actions_stay_visible(self):
        self.root.geometry("920x600")
        self.app.view.mode_buttons["daily"].invoke()
        self.root.update()
        self.assertGreater(self.app.view.content.winfo_height(), self.app.view.scroll.winfo_height())
        self.app.view.scroll.yview_moveto(1)
        self.root.update()
        button = self.app.start_button
        self.assertTrue(button.winfo_ismapped())
        self.assertLessEqual(button.winfo_rootx() + button.winfo_width(),
                             self.root.winfo_rootx() + self.root.winfo_width())
        self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                             self.root.winfo_rooty() + self.root.winfo_height())

    def test_preview_still_uses_selected_hero_and_animated_popup(self):
        self.app._select_character("spiderman")
        self.app.sound_var.set(False)
        self.app._test_reminder()
        popup = self.app.popup
        self.assertEqual(popup.settings.character, "spiderman")
        for seconds, phase in ((1, "arrival"), (2.8, "landing"), (5, "message")):
            popup._render_elapsed(seconds)
            self.assertEqual(popup.stage, phase)
            self.assertTrue(popup.canvas.find_withtag("character_art"))
        popup.dismiss("done")
        self.assertIsNone(self.app.popup)

    def test_wheel_moves_over_cards_fields_buttons_and_interval_input(self):
        self.root.geometry("920x600")
        self.root.update()
        view = self.app.view
        for widget in (view.spotlight, view.tiles["spiderman"], view.message_entry,
                       view.mode_buttons["daily"], view.interval_input, view.scroll):
            with self.subTest(widget=widget.winfo_class()):
                view.scroll.yview_moveto(0)
                interval = self.app.interval_var.get()
                widget.event_generate("<MouseWheel>", delta=-120)
                self.root.update()
                self.assertGreater(view.scroll.yview()[0], 0)
                widget.event_generate("<MouseWheel>", delta=120)
                self.root.update()
                self.assertEqual(view.scroll.yview()[0], 0)
                self.assertEqual(self.app.interval_var.get(), interval)

    def test_precision_wheel_preserves_small_deltas(self):
        self.root.geometry("920x600")
        self.root.update()
        view = self.app.view
        for delta, count in ((-30, 1), (-1, 10)):
            with self.subTest(delta=delta):
                view.scroll.yview_moveto(0)
                view._wheel_remainder = 0
                for _ in range(count):
                    view.spotlight.event_generate("<MouseWheel>", delta=delta)
                self.root.update()
                self.assertGreater(view.scroll.yview()[0], 0)

    def test_scrollbar_drag_command_and_popup_isolation(self):
        self.root.geometry("920x600")
        self.root.update()
        view = self.app.view
        self.root.tk.call(view.scrollbar.cget("command"), "moveto", 1)
        self.root.update()
        self.assertAlmostEqual(view.scroll.yview()[1], 1)
        popup = tk.Toplevel(self.root)
        field = tk.Entry(popup)
        field.pack()
        self.root.update()
        before = view.scroll.yview()
        field.event_generate("<MouseWheel>", delta=120)
        self.root.update()
        self.assertEqual(view.scroll.yview(), before)
        popup.destroy()

    def test_scroll_clamps_and_reverses_at_bottom(self):
        self.root.geometry("920x600")
        self.root.update()
        view = self.app.view
        for _ in range(30):
            view.spotlight.event_generate("<MouseWheel>", delta=-120)
        self.root.update()
        self.assertAlmostEqual(view.scroll.yview()[1], 1)
        previous = view.scroll.yview()[0]
        view.spotlight.event_generate("<MouseWheel>", delta=30)
        self.root.update()
        self.assertLess(view.scroll.yview()[0], previous)


if __name__ == "__main__":
    unittest.main()
