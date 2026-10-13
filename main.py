"""A friendly, transparent desktop water reminder."""

from __future__ import annotations

import json
import math
import sys
import time
import tkinter as tk
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

from heroes import HEROES, draw_hero
from character_art import ARTWORK
from app_paths import settings_path
from desktop_ui import DesktopView, configure_styles, THEME
from reminder_styles import PRESENTATIONS, draw_card, draw_effect, revealed_message
from choreography import (
    animation_phase, desktop_pose, draw_arrival_effect, draw_landing_effect,
    landing_transform,
)


APP_NAME = "SipSidekick"
SETTINGS_PATH = settings_path()
TRANSPARENT_COLOR = "#010203"
COLORS = {
    "ink": "#153244", "muted": "#66808F", "panel": "#F7FBFD",
    "line": "#DDECF2", "aqua": "#28B6C8", "aqua_dark": "#138798",
    "aqua_soft": "#DDF6F8", "white": "#FFFFFF", "coral": "#FF7A6E",
    "green": "#58B987",
}
CHARACTERS = {
    **HEROES,
    "drop": {"name": "Dewey", "subtitle": "Bright & bubbly", "color": "#36BFD0"},
    "robot": {"name": "Bloop", "subtitle": "Calm & precise", "color": "#8292E9"},
    "cat": {"name": "Mochi", "subtitle": "Soft & playful", "color": "#FF9B72"},
    "plant": {"name": "Sprig", "subtitle": "Gentle & grounded", "color": "#62BF8D"},
}


@dataclass
class ReminderSettings:
    character: str = "spiderman"
    schedule_mode: str = "interval"
    interval_minutes: int = 60
    daily_times: list[str] = field(default_factory=lambda: ["09:00", "11:00", "14:00", "16:00"])
    reminder_text: str = "Time for a water break!"
    sound: bool = True
    enabled: bool = False

    @classmethod
    def load(cls, path: Path = SETTINGS_PATH) -> "ReminderSettings":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return cls()
        settings = cls()
        for key in asdict(settings):
            if key in data:
                setattr(settings, key, data[key])
        settings.character = settings.character if settings.character in CHARACTERS else cls().character
        settings.schedule_mode = settings.schedule_mode if settings.schedule_mode in {"interval", "daily"} else "interval"
        settings.interval_minutes = max(1, min(720, int(settings.interval_minutes)))
        settings.daily_times = normalize_times(settings.daily_times) or cls().daily_times
        settings.reminder_text = str(settings.reminder_text).strip()[:80] or cls().reminder_text
        settings.sound = bool(settings.sound)
        settings.enabled = bool(settings.enabled)
        return settings

    def save(self, path: Path = SETTINGS_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


def normalize_time(value: str) -> str:
    """Return a strict HH:MM value or raise ValueError."""
    parsed = datetime.strptime(value.strip(), "%H:%M")
    return parsed.strftime("%H:%M")


def normalize_times(values: list[str]) -> list[str]:
    normalized = []
    for value in values:
        try:
            candidate = normalize_time(str(value))
        except ValueError:
            continue
        if candidate not in normalized:
            normalized.append(candidate)
    return sorted(normalized)


def next_daily_occurrence(now: datetime, daily_times: list[str]) -> datetime:
    """Return the next configured daily time strictly after ``now``."""
    valid_times = normalize_times(daily_times)
    if not valid_times:
        raise ValueError("At least one daily reminder time is required.")
    for value in valid_times:
        hour, minute = (int(part) for part in value.split(":"))
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate > now:
            return candidate
    hour, minute = (int(part) for part in valid_times[0].split(":"))
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)


def rounded_rectangle(canvas: tk.Canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_character(canvas: tk.Canvas, kind: str, x: float, y: float, scale: float = 1.0,
                   phase="idle", elapsed=0.0, stretch=(1, 1)) -> None:
    """Draw one of the built-in characters on a canvas."""
    def s(value: float) -> float:
        return value * scale

    color = CHARACTERS[kind]["color"]
    outline = COLORS["ink"]
    line = max(1, int(s(2)))
    canvas.create_oval(x - s(45), y + s(50), x + s(45), y + s(64), fill="#C7D8DE", outline="")
    if ARTWORK.draw(canvas, kind, x, y, scale, phase, elapsed, stretch):
        return
    if kind in HEROES:
        draw_hero(canvas, kind, x, y, scale)
    elif kind == "drop":
        points = [x, y - s(80), x - s(48), y - s(2), x - s(42), y + s(38), x, y + s(57), x + s(42), y + s(38), x + s(48), y - s(2)]
        canvas.create_polygon(points, smooth=True, fill=color, outline=outline, width=line)
        canvas.create_oval(x - s(24), y - s(15), x - s(13), y - s(3), fill=outline, outline="")
        canvas.create_oval(x + s(13), y - s(15), x + s(24), y - s(3), fill=outline, outline="")
        canvas.create_arc(x - s(22), y - s(3), x + s(22), y + s(28), start=200, extent=140, style="arc", outline=outline, width=max(1, int(s(3))))
        canvas.create_oval(x - s(28), y - s(51), x - s(13), y - s(30), fill="#9DEBF2", outline="")
    elif kind == "robot":
        canvas.create_line(x, y - s(75), x, y - s(57), fill=outline, width=max(1, int(s(3))))
        canvas.create_oval(x - s(7), y - s(84), x + s(7), y - s(70), fill=COLORS["coral"], outline=outline)
        canvas.create_rectangle(x - s(46), y - s(58), x + s(46), y + s(25), fill=color, outline=outline, width=line)
        canvas.create_rectangle(x - s(35), y + s(25), x + s(35), y + s(51), fill="#6575CA", outline=outline, width=line)
        for offset in (-20, 20):
            canvas.create_oval(x + s(offset - 9), y - s(30), x + s(offset + 9), y - s(11), fill="white", outline=outline)
            canvas.create_oval(x + s(offset - 3), y - s(24), x + s(offset + 3), y - s(17), fill=outline, outline="")
        canvas.create_line(x - s(20), y + s(5), x + s(20), y + s(5), fill=outline, width=max(1, int(s(3))))
    elif kind == "cat":
        canvas.create_polygon(x - s(46), y - s(44), x - s(34), y - s(80), x - s(10), y - s(54), fill=color, outline=outline, width=line)
        canvas.create_polygon(x + s(46), y - s(44), x + s(34), y - s(80), x + s(10), y - s(54), fill=color, outline=outline, width=line)
        canvas.create_oval(x - s(48), y - s(61), x + s(48), y + s(43), fill=color, outline=outline, width=line)
        canvas.create_oval(x - s(28), y - s(22), x - s(12), y - s(5), fill=outline, outline="")
        canvas.create_oval(x + s(12), y - s(22), x + s(28), y - s(5), fill=outline, outline="")
        canvas.create_polygon(x, y - s(2), x - s(8), y + s(7), x + s(8), y + s(7), fill="#E96C70", outline=outline)
        canvas.create_arc(x - s(19), y + s(2), x, y + s(24), start=200, extent=110, style="arc", outline=outline, width=line)
        canvas.create_arc(x, y + s(2), x + s(19), y + s(24), start=230, extent=110, style="arc", outline=outline, width=line)
        for offset in (-10, 2, 14):
            canvas.create_line(x - s(8), y + s(offset), x - s(48), y + s(offset - 5), fill=outline)
            canvas.create_line(x + s(8), y + s(offset), x + s(48), y + s(offset - 5), fill=outline)
    else:
        canvas.create_rectangle(x - s(34), y + s(1), x + s(34), y + s(51), fill="#E99B67", outline=outline, width=line)
        canvas.create_line(x, y + s(3), x, y - s(52), fill=outline, width=max(1, int(s(4))))
        canvas.create_oval(x - s(45), y - s(55), x, y - s(18), fill=color, outline=outline, width=line)
        canvas.create_oval(x, y - s(72), x + s(45), y - s(28), fill="#47A976", outline=outline, width=line)
        canvas.create_oval(x - s(20), y + s(14), x - s(8), y + s(27), fill=outline, outline="")
        canvas.create_oval(x + s(8), y + s(14), x + s(20), y + s(27), fill=outline, outline="")
        canvas.create_arc(x - s(17), y + s(21), x + s(17), y + s(42), start=200, extent=140, style="arc", outline=outline, width=line)


class ReminderPopup:
    WIDTH = 524
    HEIGHT = 340

    def __init__(self, root: tk.Tk, settings: ReminderSettings, on_done: Callable[[str], None]) -> None:
        self.root, self.settings, self.on_done = root, settings, on_done
        self.style = PRESENTATIONS[settings.character]
        self.message = settings.reminder_text.strip()
        if not self.message or self.message == ReminderSettings().reminder_text:
            self.message = self.style.message
        self.closed = False
        self.stage = "arrival"
        self.frame_elapsed = 0.0
        self.desktop_overlay = False
        self.arrival_seconds = 2.6 if settings.character == "spiderman" else self.style.duration
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.background = TRANSPARENT_COLOR
        self.window.configure(bg=TRANSPARENT_COLOR)
        try:
            if self.window.tk.call("tk", "windowingsystem") == "aqua":
                self.window.wm_attributes("-transparent", True)
                self.window.configure(bg="systemTransparent")
                self.background = "systemTransparent"
            else:
                self.window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
            self.supports_transparency = True
        except tk.TclError:
            self.supports_transparency = False
            self.window.attributes("-alpha", 0.96)
        self.final_x = max(12, self.window.winfo_screenwidth() - self.WIDTH - 28)
        self.final_y = max(12, self.window.winfo_screenheight() - self.HEIGHT - 72)
        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()
        self.canvas = tk.Canvas(self.window, width=self.WIDTH, height=self.HEIGHT, bg=self.background, highlightthickness=0)
        self.canvas.pack()
        self.window.bind("<Escape>", lambda _event: self.dismiss("dismiss"))
        self.window.bind("<Return>", lambda _event: self.dismiss("done"))
        self.window.bind("<s>", lambda _event: self.dismiss("snooze"))
        self.window.bind("<ButtonPress-1>", self._start_drag)
        self.window.bind("<B1-Motion>", self._drag)
        self.drag_x = self.drag_y = 0
        self.animation_job: str | None = None

    def show(self) -> None:
        self.desktop_overlay = self.supports_transparency
        if self.desktop_overlay:
            self.canvas.configure(width=self.screen_width, height=self.screen_height)
            self.window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        else:
            self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self.final_x}+{self.final_y}")
        self.started_at = time.monotonic()
        self._animate()
        self.window.deiconify()
        self.window.lift()
        if self.settings.sound:
            try:
                self.root.bell()
            except tk.TclError:
                pass

    def _draw(self, progress: float = 1.0) -> None:
        c = self.canvas
        c.delete("all")
        style = self.style
        draw_card(c, style, progress, rounded_rectangle)
        character = CHARACTERS[self.settings.character]
        c.create_text(170, 64, text=character["name"].upper(), anchor="w", fill=style.accent, font=("Segoe UI", 10, "bold"))
        c.create_text(170, 89, text=style.heading, anchor="nw", width=318, fill=style.accent, font=("Segoe UI", 8, "bold"))
        text = revealed_message(self.message, style, progress)
        font = "Consolas" if style.reveal in ("typewriter", "terminal", "signal") else "Segoe UI"
        # Fit the complete message first, keeping its position stable during reveal.
        title = c.create_text(170, 116, text=self.message, anchor="nw", width=310,
                              fill=style.foreground, font=(font, 16, "bold"), tags="message")
        size = 16
        while c.bbox(title)[3] > 214 and size > 8:
            size -= 1
            c.itemconfigure(title, font=(font, size, "bold"))
        c.itemconfigure(title, text=text)
        if style.reveal in ("banner", "ribbon", "speedlines", "bubble", "ripples"):
            offset = (1 - min(1.0, progress / 0.86)) * 16
            c.move(title, offset if style.reveal == "speedlines" else 0, offset if style.reveal != "speedlines" else 0)
        if progress > 0.5:
            c.create_text(170, 224, text=style.detail, anchor="nw", width=310, fill=style.foreground, font=("Segoe UI", 9))
        rounded_rectangle(c, 166, 277, 310, 313, 12, fill=style.accent, outline="", tags=("done",))
        c.create_text(238, 295, text="I drank water", fill=style.background, font=("Segoe UI", 9, "bold"), tags=("done",))
        rounded_rectangle(c, 320, 277, 492, 313, 12, fill=style.background, outline=style.accent, tags=("snooze",))
        c.create_text(406, 295, text="Snooze 10 min", fill=style.foreground, font=("Segoe UI", 9, "bold"), tags=("snooze",))
        c.tag_bind("done", "<Button-1>", lambda _event: self.dismiss("done"))
        c.tag_bind("snooze", "<Button-1>", lambda _event: self.dismiss("snooze"))
        c.create_text(495, 12, text="×", fill=style.accent, font=("Segoe UI", 16, "bold"), tags="close")
        c.tag_bind("close", "<Button-1>", lambda _event: self.dismiss("dismiss"))
        # Reveal the message surface only after the character has landed.
        c.addtag_all("card")
        growth = min(1.0, progress / .38)
        if style.reveal in ("bubble", "ripples", "pawprints", "leaves"):
            c.scale("card", 145, 260, .7 + .3 * growth, .7 + .3 * growth)
        elif style.reveal in ("typewriter", "terminal", "signal", "briefing", "runes"):
            c.scale("card", 145, 24, 1, .18 + .82 * growth)
        else:
            c.move("card", (1 - growth) * 48, 0)
        draw_character(c, self.settings.character, 73, 235, elapsed=self.frame_elapsed)

    def _draw_entrance(self, stage: str, progress: float) -> None:
        c = self.canvas
        c.delete("all")
        x = self.final_x + 73 if self.desktop_overlay else 73
        y = self.final_y + 235 if self.desktop_overlay else 235
        width = self.screen_width if self.desktop_overlay else self.WIDTH
        height = self.screen_height if self.desktop_overlay else self.HEIGHT
        if stage == "arrival":
            pose = desktop_pose(self.style.entrance, progress, x, y, width, height)
            use_art = ARTWORK.clip(self.settings.character, "arrival") is not None
            if not (use_art and self.style.entrance == "web"):
                draw_arrival_effect(c, self.style, progress, pose, x, y, width, draw_effect)
            before = set(c.find_all())
            phase = "landing" if self.settings.character == "spiderman" and progress >= .67 else "arrival"
            draw_character(c, self.settings.character, pose.x, pose.y, pose.scale,
                           phase=phase, elapsed=self.frame_elapsed)
            # Shadows stay at the landing spot while the character is airborne.
            added = [item for item in c.find_all() if item not in before]
            if added:
                c.delete(added[0])
            c.create_oval(x - 37, y + 53, x + 37, y + 64, fill="#C7D8DE", outline="")
            if use_art and self.style.entrance == "web":
                bounds = c.bbox("character_art")
                end_y = bounds[1] + 4 if progress < .67 else max(0, y - 245) * (1 - (progress - .67) / .33)
                c.create_line(x, 0, pose.x if progress < .67 else x, end_y, fill="#A5BAC9", width=2)
            if not use_art and self.style.entrance == "web" and progress < .67:
                # Raised arms meet the web above his head while hanging.
                for side in (-1, 1):
                    c.create_line(pose.x + side * 30, pose.y + 1,
                                  pose.x + side * 39, pose.y - 62,
                                  pose.x + side * 8, pose.y - 101,
                                  fill="#C83248", width=9, capstyle="round", joinstyle="round")
                c.create_oval(pose.x - 10, pose.y - 108, pose.x + 10, pose.y - 96,
                              fill="#C83248", outline="#172B40")
        else:
            draw_landing_effect(c, self.style, progress, x, y)
            before = set(c.find_all())
            sx, sy = landing_transform(self.style.entrance, progress)
            use_art = ARTWORK.clip(self.settings.character, "landing") is not None
            # A dedicated landing pose provides the crouch; apply a small settling motion.
            stretch = (1 + (sx - 1) * .3, 1 + (sy - 1) * .3) if use_art else (1, 1)
            phase = "landing" if progress < .85 else "idle"
            draw_character(c, self.settings.character, x, y, phase=phase,
                           elapsed=self.frame_elapsed, stretch=stretch)
            added = [item for item in c.find_all() if item not in before]
            for item in added[1:]:
                c.addtag_withtag("landing_character", item)
            if not use_art:
                c.scale("landing_character", x, y + 59, sx, sy)
        # A dismiss control stays available throughout the desktop entrance.
        close_x = self.final_x + 495 if self.desktop_overlay else 495
        close_y = self.final_y + 12 if self.desktop_overlay else 12
        c.create_text(close_x, close_y, text="×", fill=self.style.accent,
                      font=("Segoe UI", 16, "bold"), tags="close")
        c.tag_bind("close", "<Button-1>", lambda _event: self.dismiss("dismiss"))

    def _render_elapsed(self, elapsed: float) -> bool:
        self.frame_elapsed = elapsed
        self.stage, progress = animation_phase(elapsed, self.arrival_seconds)
        if self.stage != "message":
            self._draw_entrance(self.stage, progress)
        else:
            if self.desktop_overlay:
                # Shrink to the final card, keeping the character in the same desktop position.
                self.desktop_overlay = False
                self.canvas.configure(width=self.WIDTH, height=self.HEIGHT)
                self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self.final_x}+{self.final_y}")
            self._draw(progress)
        return self.stage != "message" or progress < 1 or ARTWORK.is_animated(self.settings.character)

    def _animate(self) -> None:
        self.animation_job = None
        if self.closed:
            return
        if self._render_elapsed(time.monotonic() - self.started_at):
            self.animation_job = self.window.after(25, self._animate)

    def _start_drag(self, event) -> None:
        if self.closed or self.stage != "message":
            return
        self.drag_x = event.x_root - self.window.winfo_x()
        self.drag_y = event.y_root - self.window.winfo_y()

    def _drag(self, event) -> None:
        if self.closed or self.stage != "message":
            return
        self.window.geometry(f"+{event.x_root - self.drag_x}+{event.y_root - self.drag_y}")

    def dismiss(self, action: str = "dismiss") -> None:
        if self.closed:
            return
        self.closed = True
        if self.animation_job:
            try:
                self.window.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            self.animation_job = None
        self.window.destroy()
        self.on_done(action)


class WaterReminderApp:
    CHECK_INTERVAL_MS = 1_000

    def __init__(self, root: tk.Tk, settings: ReminderSettings | None = None) -> None:
        self.root = root
        self.settings = settings if settings is not None else ReminderSettings.load()
        self.next_reminder: datetime | None = None
        self.popup: ReminderPopup | None = None
        self.root.title(APP_NAME)
        window_width = min(1120, max(920, self.root.winfo_screenwidth() - 80))
        window_height = min(880, max(620, self.root.winfo_screenheight() - 100))
        window_x = max(20, (self.root.winfo_screenwidth() - window_width) // 2)
        self.root.geometry(f"{window_width}x{window_height}+{window_x}+30")
        self.root.minsize(920, 600)
        self.root.configure(bg=COLORS["panel"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._configure_styles()
        self._build_ui()
        self._load_into_ui()
        if self.settings.enabled:
            self._schedule_next(reset_interval=True)
        self._tick()

    def _configure_styles(self) -> None:
        configure_styles(self.root)

    def _build_ui(self) -> None:
        self.view = DesktopView(self, CHARACTERS, draw_character)

    def _load_into_ui(self) -> None:
        self.character_var.set(self.settings.character)
        group = CHARACTERS[self.settings.character].get("group", "Originals")
        self.view.group.set(group)
        self.view.change_group()
        self.mode_var.set(self.settings.schedule_mode)
        self.interval_var.set(self.settings.interval_minutes)
        self.message_var.set("" if self.settings.reminder_text == ReminderSettings().reminder_text else self.settings.reminder_text)
        self.sound_var.set(self.settings.sound)
        self._render_times(self.settings.daily_times)
        self._refresh_character_selection()
        self._update_schedule_mode()
        self._update_status()

    def _select_character(self, value: str) -> None:
        self.character_var.set(value)
        self._refresh_character_selection()

    def _refresh_character_selection(self) -> None:
        self.view.refresh_selection()

    def _update_schedule_mode(self) -> None:
        self.view.refresh_modes()
        if self.mode_var.get() == "daily":
            self.interval_frame.pack_forget()
            self.daily_frame.pack(fill="x", pady=(8, 0))
        else:
            self.daily_frame.pack_forget()
            self.interval_frame.pack(fill="x", pady=(8, 0))

    def _render_times(self, values: list[str]) -> None:
        for child in self.time_list.winfo_children():
            child.destroy()
        self.time_vars: list[tk.StringVar] = []
        for value in values:
            row = ttk.Frame(self.time_list, style="Card.TFrame")
            row.pack(fill="x", pady=2)
            var = tk.StringVar(value=value)
            self.time_vars.append(var)
            ttk.Entry(row, textvariable=var, width=9, justify="center").pack(side="left")
            ttk.Button(row, text="Remove", command=lambda target=row: self._remove_time_row(target)).pack(side="right")

    def _remove_time_row(self, row: ttk.Frame) -> None:
        index = list(self.time_list.winfo_children()).index(row)
        self._render_times([var.get() for i, var in enumerate(self.time_vars) if i != index])

    def _add_time(self) -> None:
        try:
            value = normalize_time(self.new_time_var.get())
        except ValueError:
            messagebox.showerror("Invalid time", "Enter the time in 24-hour HH:MM format, for example 14:30.", parent=self.root)
            return
        self._render_times(normalize_times([var.get() for var in self.time_vars] + [value]))

    def _read_ui(self) -> ReminderSettings | None:
        try:
            interval = int(self.interval_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid interval", "Choose an interval from 1 to 720 minutes.", parent=self.root)
            return None
        if not 1 <= interval <= 720:
            messagebox.showerror("Invalid interval", "Choose an interval from 1 to 720 minutes.", parent=self.root)
            return None
        raw_times = [var.get() for var in self.time_vars]
        if any(value.strip() not in normalize_times([value]) for value in raw_times):
            messagebox.showerror("Invalid time", "Use 24-hour HH:MM format for each daily time.", parent=self.root)
            return None
        daily_times = normalize_times(raw_times)
        if self.mode_var.get() == "daily" and not daily_times:
            messagebox.showerror("No reminder times", "Add at least one daily reminder time.", parent=self.root)
            return None
        message = self.message_var.get().strip()
        return ReminderSettings(self.character_var.get(), self.mode_var.get(), interval, daily_times, message[:80], self.sound_var.get(), self.settings.enabled)

    def _toggle_reminders(self) -> None:
        candidate = self._read_ui()
        if candidate is None:
            return
        candidate.enabled = not self.settings.enabled
        self.settings = candidate
        self.settings.save()
        self.next_reminder = None
        if self.settings.enabled:
            self._schedule_next(reset_interval=True)
        self._update_status()

    def _save_settings(self) -> None:
        candidate = self._read_ui()
        if candidate is None:
            return
        self.settings = candidate
        self.settings.save()
        if self.settings.enabled:
            self._schedule_next(reset_interval=True)
        self.view.saved()
        self._update_status()

    def _schedule_next(self, reset_interval: bool = False) -> None:
        now = datetime.now()
        if self.settings.schedule_mode == "daily":
            self.next_reminder = next_daily_occurrence(now, self.settings.daily_times)
        elif reset_interval or self.next_reminder is None or self.next_reminder <= now:
            self.next_reminder = now + timedelta(minutes=self.settings.interval_minutes)

    def _tick(self) -> None:
        if self.settings.enabled and self.next_reminder and datetime.now() >= self.next_reminder:
            self._show_reminder()
            self._schedule_next(reset_interval=True)
        self._update_status()
        self.root.after(self.CHECK_INTERVAL_MS, self._tick)

    def _test_reminder(self) -> None:
        candidate = self._read_ui()
        if candidate is None:
            return
        candidate.enabled = self.settings.enabled
        self.settings = candidate
        self.settings.save()
        if self.popup and self.popup.window.winfo_exists():
            self.popup.dismiss("dismiss")
        self._show_reminder()

    def _show_reminder(self) -> None:
        if self.popup and self.popup.window.winfo_exists():
            self.popup.window.lift()
            return
        self.popup = ReminderPopup(self.root, self.settings, self._popup_done)
        self.popup.show()

    def _popup_done(self, action: str) -> None:
        self.popup = None
        if action == "snooze":
            self.next_reminder = datetime.now() + timedelta(minutes=10)
        self._update_status()

    def _update_status(self) -> None:
        self.view.update_status(self.settings.enabled)
        if self.settings.enabled and self.next_reminder:
            remaining = max(timedelta(0), self.next_reminder - datetime.now())
            total_seconds = math.ceil(remaining.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown = f"{hours}h {minutes}m" if hours else (f"{minutes}m {seconds}s" if minutes else f"{seconds}s")
            self.status_var.set(f"Next reminder in {countdown}  •  {self.next_reminder.strftime('%I:%M %p')}")
            self.status_dot.itemconfigure("dot", fill=THEME["green"])
            self.start_button.configure(text="Pause reminders")
        else:
            self.status_var.set("Reminders are paused")
            self.status_dot.itemconfigure("dot", fill=THEME["muted"])
            self.start_button.configure(text="Start reminders")

    def _on_close(self) -> None:
        candidate = self._read_ui()
        if candidate is not None:
            candidate.enabled = self.settings.enabled
            candidate.save()
        self.root.destroy()


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from runtime_smoke import run
        run(Path(sys.argv[2]), WaterReminderApp, ReminderSettings, ReminderPopup)
        return
    root = tk.Tk()
    icon_path = Path(__file__).with_name("assets") / "app-icon.png"
    if icon_path.exists():
        root._app_icon = tk.PhotoImage(file=icon_path)
        root.iconphoto(True, root._app_icon)
    WaterReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
