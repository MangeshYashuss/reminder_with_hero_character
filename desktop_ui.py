"""Rich native desktop dashboard; scheduling stays in the application controller."""

import tkinter as tk
from tkinter import ttk

from character_art import ARTWORK


THEME = {
    "background": "#0C1020", "surface": "#151B30", "raised": "#1D2540",
    "border": "#2B3553", "text": "#F2F4FF", "muted": "#A3AECD",
    "violet": "#9275FF", "cyan": "#63DFE9", "green": "#7DE4B0",
}


def blend(first, second, amount):
    a, b = [tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) for color in (first, second)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))


def rounded(canvas, bounds, radius=18, **options):
    x1, y1, x2, y2 = bounds
    return canvas.create_polygon(
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        smooth=True, **options,
    )


class Panel(tk.Frame):
    """Rounded surface with ordinary, keyboard-accessible native widgets inside."""

    def __init__(self, parent, padding=16):
        super().__init__(parent, bg=THEME["background"])
        self.backdrop = tk.Canvas(self, highlightthickness=0, bg=THEME["background"])
        self.backdrop.place(relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=THEME["surface"])
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)
        self.body.lift()
        self.bind("<Configure>", self._paint)

    def _paint(self, event):
        if event.widget is self:
            self.backdrop.delete("all")
            rounded(self.backdrop, (1, 1, event.width - 1, event.height - 1),
                    fill=THEME["surface"], outline=THEME["border"])


def label(parent, text, size=10, color="text", bold=False, **options):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=THEME.get(color, color),
                    font=("Segoe UI", size, "bold" if bold else "normal"), **options)


def configure_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Card.TFrame", background=THEME["surface"])
    style.configure("Body.TLabel", background=THEME["surface"], foreground=THEME["muted"], font=("Segoe UI", 10))
    style.configure("TEntry", fieldbackground=THEME["background"], foreground=THEME["text"],
                    insertcolor=THEME["cyan"], bordercolor=THEME["border"], lightcolor=THEME["border"],
                    darkcolor=THEME["border"], padding=9)
    style.map("TEntry", bordercolor=[("focus", THEME["violet"])])
    style.configure("TSpinbox", fieldbackground=THEME["background"], foreground=THEME["text"],
                    arrowcolor=THEME["cyan"], background=THEME["raised"], padding=8,
                    bordercolor=THEME["border"], insertcolor=THEME["cyan"])
    style.configure("TButton", background=THEME["raised"], foreground=THEME["text"],
                    font=("Segoe UI", 9, "bold"), padding=(12, 9), borderwidth=0)
    style.map("TButton", background=[("pressed", "#384364"), ("active", "#303B5C")],
              foreground=[("disabled", THEME["muted"])])
    style.configure("Primary.TButton", background=THEME["violet"], foreground="#101426", padding=(18, 13))
    style.map("Primary.TButton", background=[("pressed", "#A68EFF"), ("active", "#B29CFF")])
    style.configure("Secondary.TButton", padding=(14, 13))
    style.configure("TCheckbutton", background=THEME["surface"], foreground=THEME["text"],
                    font=("Segoe UI", 10), indicatorbackground=THEME["background"], indicatormargin=6)
    style.map("TCheckbutton", background=[("active", THEME["surface"])],
              indicatorbackground=[("selected", THEME["violet"])])
    style.configure("Vertical.TScrollbar", background=THEME["border"], troughcolor=THEME["background"],
                    arrowcolor=THEME["muted"], borderwidth=0, arrowsize=12)


class DesktopView:
    def __init__(self, app, characters, draw_character):
        self.app, self.characters, self.draw_character = app, characters, draw_character
        self.group = tk.StringVar(value="Marvel")
        self.tiles = {}
        self.tab_buttons = {}
        self.preset_buttons = {}
        self.mode_buttons = {}
        self._wheel_remainder = 0.0
        self._window_system = app.root.tk.call("tk", "windowingsystem")
        self._build()

    def _build(self):
        app = self.app
        app.root.configure(bg=THEME["background"])
        shell = tk.Frame(app.root, bg=THEME["background"])
        shell.pack(fill="both", expand=True, padx=24, pady=18)
        header = tk.Frame(shell, bg=THEME["background"])
        header.pack(fill="x", pady=(0, 12))
        logo = tk.Canvas(header, width=44, height=44, bg=THEME["background"], highlightthickness=0)
        logo.pack(side="left", padx=(0, 12))
        rounded(logo, (0, 0, 44, 44), 14, fill=THEME["violet"], outline="")
        logo.create_polygon(22, 8, 11, 26, 16, 35, 28, 35, 33, 26, smooth=True, fill="#F5F1FF", outline="")
        brand = tk.Frame(header, bg=THEME["background"])
        brand.pack(side="left")
        label(brand, "SipSidekick", 18, bold=True).pack(anchor="w")
        label(brand, "SMALL BREAKS. SUPER POWERS.", 8, "muted").pack(anchor="w")
        self.state_badge = label(header, "  REMINDERS PAUSED  ", 9, "muted", True, pady=8)
        self.state_badge.pack(side="right")

        # Footer is outside the scroll area: primary actions never disappear.
        footer = tk.Frame(shell, bg=THEME["background"])
        footer.pack(side="bottom", fill="x", pady=(14, 0))
        actions = tk.Frame(footer, bg=THEME["background"])
        actions.pack(side="right")
        self.save_button = ttk.Button(actions, text="Save", command=app._save_settings)
        self.save_button.pack(side="left", padx=(0, 8))
        self.save_feedback_job = None
        ttk.Button(actions, text="Test reminder", style="Secondary.TButton", command=app._test_reminder).pack(side="left", padx=(0, 8))
        app.start_button = ttk.Button(actions, text="Start reminders", style="Primary.TButton", command=app._toggle_reminders)
        app.start_button.pack(side="left")
        app.status_dot = tk.Canvas(footer, width=12, height=12, bg=THEME["background"], highlightthickness=0)
        app.status_dot.pack(side="left", padx=(0, 8))
        app.status_dot.create_oval(2, 2, 10, 10, fill=THEME["muted"], outline="", tags="dot")
        app.status_var = tk.StringVar(value="Reminders are paused")
        tk.Label(footer, textvariable=app.status_var, bg=THEME["background"], fg=THEME["muted"],
                 font=("Segoe UI", 9), anchor="w").pack(side="left")

        viewport = tk.Frame(shell, bg=THEME["background"])
        viewport.pack(fill="both", expand=True)
        self.scroll = tk.Canvas(viewport, bg=THEME["background"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=self.scroll.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll.pack(side="left", fill="both", expand=True)
        self.scroll.configure(yscrollcommand=self.scrollbar.set)
        self.content = tk.Frame(self.scroll, bg=THEME["background"])
        self.content_id = self.scroll.create_window(0, 0, window=self.content, anchor="nw")
        self.scroll.bind("<Configure>", lambda event: self.scroll.itemconfigure(self.content_id, width=event.width))
        self.content.bind("<Configure>", lambda _event: self.scroll.configure(scrollregion=self.scroll.bbox("all")))
        app.root.bind("<MouseWheel>", self._wheel, add="+")
        if self._window_system == "x11":
            app.root.bind("<Button-4>", self._wheel, add="+")
            app.root.bind("<Button-5>", self._wheel, add="+")
        app.root.bind("<FocusIn>", self._reveal_focus, add="+")
        self.content.columnconfigure(0, weight=5, uniform="dashboard")
        self.content.columnconfigure(1, weight=4, uniform="dashboard")

        intro = tk.Frame(self.content, bg=THEME["background"])
        intro.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        label(intro, "A little water. A lot of superpower.", 22, bold=True).pack(anchor="w")
        label(intro, "Your favorite hero. Your rhythm. A healthier everyday.", 10, "muted").pack(anchor="w", pady=(5, 0))

        left = tk.Frame(self.content, bg=THEME["background"])
        left.grid(row=1, column=0, sticky="new", padx=(0, 14))
        right = tk.Frame(self.content, bg=THEME["background"])
        right.grid(row=1, column=1, sticky="new", padx=(0, 4))
        self.spotlight = tk.Canvas(left, height=202, bg=THEME["background"], highlightthickness=0)
        self.spotlight.pack(fill="x", pady=(0, 12))
        self.spotlight.bind("<Configure>", lambda _event: self.refresh_hero())

        roster = Panel(left, padding=16)
        roster.pack(fill="x")
        title_row = tk.Frame(roster.body, bg=THEME["surface"])
        title_row.pack(fill="x")
        label(title_row, "Meet your sidekick", 13, bold=True).pack(side="left")
        label(title_row, "12 CHARACTERS", 8, "muted").pack(side="right")
        tabs = tk.Frame(roster.body, bg=THEME["surface"])
        tabs.pack(fill="x", pady=(8, 8))
        for group in ("Marvel", "DC", "Originals"):
            button = self._segment(tabs, group, self.group, group, self.change_group)
            button.pack(side="left", fill="x", expand=True, padx=2)
            self.tab_buttons[group] = button
        self.roster_grid = tk.Frame(roster.body, bg=THEME["surface"])
        self.roster_grid.pack(fill="x")
        app.character_var = tk.StringVar()
        for key, character in self.characters.items():
            tile = tk.Canvas(self.roster_grid, width=180, height=100, bg=THEME["surface"],
                             highlightthickness=0, takefocus=True, cursor="hand2")
            tile.bind("<Configure>", lambda _event, k=key: self._draw_tile(k))
            tile.bind("<Button-1>", lambda _event, k=key: app._select_character(k))
            tile.bind("<Return>", lambda _event, k=key: app._select_character(k))
            tile.bind("<space>", lambda _event, k=key: app._select_character(k))
            tile.bind("<Enter>", lambda _event, k=key: self._draw_tile(k, hover=True))
            tile.bind("<Leave>", lambda _event, k=key: self._draw_tile(k))
            tile.bind("<FocusIn>", lambda _event, k=key: self._draw_tile(k, hover=True))
            tile.bind("<FocusOut>", lambda _event, k=key: self._draw_tile(k))
            self.tiles[key] = tile
        self.roster_grid.columnconfigure((0, 1), weight=1, uniform="heroes")

        schedule = Panel(right)
        schedule.pack(fill="x", pady=(0, 14))
        label(schedule.body, "01  /  YOUR RHYTHM", 8, "cyan", True).pack(anchor="w")
        label(schedule.body, "Make time to recharge", 15, bold=True).pack(anchor="w", pady=(4, 3))
        label(schedule.body, "A regular nudge or your own daily routine.", 9, "muted").pack(anchor="w")
        modes = tk.Frame(schedule.body, bg=THEME["surface"])
        modes.pack(fill="x", pady=(10, 8))
        app.mode_var = tk.StringVar()
        for key, title in (("interval", "Repeat interval"), ("daily", "Daily times")):
            button = self._segment(modes, title, app.mode_var, key, app._update_schedule_mode)
            button.pack(side="left", fill="x", expand=True, padx=2)
            self.mode_buttons[key] = button
        app.interval_frame = ttk.Frame(schedule.body, style="Card.TFrame")
        app.interval_var = tk.IntVar()
        interval_row = tk.Frame(app.interval_frame, bg=THEME["surface"])
        interval_row.pack(fill="x")
        label(interval_row, "Every", 10, "muted").pack(side="left", padx=(0, 12))
        self.interval_input = ttk.Spinbox(interval_row, from_=1, to=720, textvariable=app.interval_var,
                                         width=5, justify="center", font=("Segoe UI", 20, "bold"))
        self.interval_input.pack(side="left")
        # Handle the wheel before the Spinbox class can change the saved interval.
        self.interval_input.bind("<MouseWheel>", self._wheel)
        if self._window_system == "x11":
            self.interval_input.bind("<Button-4>", self._wheel)
            self.interval_input.bind("<Button-5>", self._wheel)
        label(interval_row, "minutes", 10, "muted").pack(side="left", padx=12)
        presets = tk.Frame(app.interval_frame, bg=THEME["surface"])
        presets.pack(fill="x", pady=(8, 0))
        for value in (30, 45, 60, 90):
            button = tk.Button(presets, text=f"{value} min", command=lambda n=value: app.interval_var.set(n),
                               bg=THEME["raised"], fg=THEME["muted"], activebackground=THEME["violet"],
                               activeforeground=THEME["background"], relief="flat", bd=0, pady=5,
                               font=("Segoe UI", 9), cursor="hand2")
            button.pack(side="left", fill="x", expand=True, padx=2)
            self.preset_buttons[value] = button
        app.interval_var.trace_add("write", lambda *_args: self.refresh_presets())
        app.daily_frame = ttk.Frame(schedule.body, style="Card.TFrame")
        app.time_list = ttk.Frame(app.daily_frame, style="Card.TFrame")
        app.time_list.pack(fill="x")
        add_row = ttk.Frame(app.daily_frame, style="Card.TFrame")
        add_row.pack(fill="x", pady=(10, 0))
        app.new_time_var = tk.StringVar(value="10:00")
        entry = ttk.Entry(add_row, textvariable=app.new_time_var, width=8, justify="center")
        entry.pack(side="left")
        entry.bind("<Return>", lambda _event: app._add_time())
        ttk.Button(add_row, text="+ Add time", command=app._add_time).pack(side="left", padx=(8, 0))
        label(schedule.body, "LOCAL TIME  ·  24-HOUR FORMAT", 8, "muted").pack(side="bottom", anchor="w", pady=(8, 0))

        message = Panel(right)
        message.pack(fill="x", pady=(0, 14))
        label(message.body, "02  /  A PERSONAL TOUCH", 8, "violet", True).pack(anchor="w")
        label(message.body, "Words to keep you going", 14, bold=True).pack(anchor="w", pady=(4, 8))
        app.message_var = tk.StringVar()
        app.sound_var = tk.BooleanVar()
        self.message_entry = ttk.Entry(message.body, textvariable=app.message_var, font=("Segoe UI", 10))
        self.message_entry.pack(fill="x")
        label(message.body, "Leave blank for your hero's own message.", 9, "muted").pack(anchor="w", pady=(5, 6))
        ttk.Checkbutton(message.body, text="Play a gentle sound", variable=app.sound_var).pack(anchor="w")

        note = tk.Frame(right, bg=THEME["background"])
        note.pack(fill="x", padx=5, pady=3)
        label(note, "MADE FOR YOUR DESKTOP", 8, "cyan", True).pack(anchor="w")
        label(note, "Transparent arrivals. A personality with every sip.\nKeep the app running to receive reminders.",
              9, "muted", justify="left").pack(anchor="w", pady=(5, 0))
        self.feedback_var = tk.StringVar()
        tk.Label(note, textvariable=self.feedback_var, bg=THEME["background"], fg=THEME["green"],
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(8, 0))

    def _segment(self, parent, text, variable, value, command):
        return tk.Radiobutton(parent, text=text, variable=variable, value=value, command=command,
                              indicatoron=False, relief="flat", bd=0, pady=6, padx=7,
                              bg=THEME["raised"], fg=THEME["muted"], selectcolor=THEME["violet"],
                              activebackground="#AF97FF", activeforeground=THEME["background"],
                              font=("Segoe UI", 9, "bold"), cursor="hand2", highlightthickness=1,
                              highlightbackground=THEME["surface"], highlightcolor=THEME["cyan"])

    def _wheel(self, event):
        # Other windows are independent. Scrollbars already process their wheel
        # in a class binding; handling it again here would move the page twice.
        if event.widget.winfo_toplevel() is not self.app.root or event.widget is self.scrollbar:
            return
        if event.state & 0x5:  # Preserve Shift/horizontal and Ctrl gestures.
            return
        button = getattr(event, "num", None)
        if button in (4, 5):
            pixels = -48.0 if button == 4 else 48.0
        else:
            # Windows wheels use 120 per notch, but precision devices send
            # smaller deltas. Keep fractional pixels instead of losing events.
            factor = 12.0 if self._window_system == "aqua" else 48.0 / 120.0
            pixels = -event.delta * factor
        height = self.content.winfo_height()
        maximum = max(0, height - self.scroll.winfo_height())
        position = self.scroll.canvasy(0)
        if not maximum or (position <= 0 and pixels < 0) or (position >= maximum and pixels > 0):
            self._wheel_remainder = 0.0
            return "break"
        if pixels * self._wheel_remainder < 0:
            self._wheel_remainder = 0.0
        self._wheel_remainder += pixels
        distance = int(self._wheel_remainder)
        self._wheel_remainder -= distance
        if distance:
            target = max(0, min(maximum, position + distance))
            self.scroll.yview_moveto(target / height)
        return "break"

    def _reveal_focus(self, event):
        widget = event.widget
        if not str(widget).startswith(str(self.content) + "."):
            return
        total = max(1, self.content.winfo_height())
        y = widget.winfo_rooty() - self.content.winfo_rooty()
        top = self.scroll.canvasy(0)
        bottom = top + self.scroll.winfo_height()
        if y < top:
            self.scroll.yview_moveto(y / total)
        elif y + widget.winfo_height() > bottom:
            self.scroll.yview_moveto((y + widget.winfo_height() - self.scroll.winfo_height()) / total)

    def change_group(self):
        for tile in self.tiles.values():
            tile.grid_forget()
        index = 0
        for key, character in self.characters.items():
            if character.get("group", "Originals") == self.group.get():
                self.tiles[key].grid(row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
                index += 1
                self._draw_tile(key)
        for key, button in self.tab_buttons.items():
            button.configure(fg=THEME["background"] if key == self.group.get() else THEME["muted"])

    def refresh_selection(self):
        self.refresh_hero()
        for key in self.tiles:
            self._draw_tile(key)

    def refresh_presets(self):
        try:
            value = self.app.interval_var.get()
        except (ValueError, tk.TclError):
            value = None
        for number, button in self.preset_buttons.items():
            button.configure(bg=THEME["violet"] if value == number else THEME["raised"],
                             fg=THEME["background"] if value == number else THEME["muted"])

    def refresh_modes(self):
        for key, button in self.mode_buttons.items():
            button.configure(fg=THEME["background"] if key == self.app.mode_var.get() else THEME["muted"])

    def _draw_tile(self, key, hover=False):
        canvas = self.tiles[key]
        canvas.delete("all")
        w = max(180, canvas.winfo_width())
        selected = key == self.app.character_var.get()
        accent = blend(self.characters[key]["color"], "#FFFFFF", .4)
        fill = blend(THEME["raised"], accent, .14 if selected else .04)
        border = accent if selected else (THEME["violet"] if hover else THEME["border"])
        rounded(canvas, (1, 1, w - 2, 98), 14, fill=fill, outline=border, width=2 if selected or hover else 1)
        canvas.create_oval(w - 85, 10, w - 9, 88, fill=blend(fill, accent, .1), outline="")
        self._art(canvas, key, w - 48, 59, .40)
        canvas.create_text(13, 25, text=self.characters[key]["name"], width=w - 99, anchor="nw",
                           fill=THEME["text"], font=("Segoe UI", 10, "bold"))
        canvas.create_text(13, 82, text="● SELECTED" if selected else "CHOOSE HERO", anchor="w",
                           fill=accent if selected else THEME["muted"], font=("Segoe UI", 7, "bold"))

    def _art(self, canvas, key, x, y, scale):
        if not ARTWORK.draw(canvas, key, x, y, scale):
            self.draw_character(canvas, key, x, y, scale)

    def refresh_hero(self):
        key = self.app.character_var.get()
        if key not in self.characters:
            return
        c = self.spotlight
        c.delete("all")
        w = max(400, c.winfo_width())
        character = self.characters[key]
        accent = blend(character["color"], "#FFFFFF", .4)
        rounded(c, (1, 1, w - 1, 200), 24, fill="#222346", outline="#484373")
        # Layered orbit lines give depth without distracting perpetual animation.
        for radius in (50, 70, 90):
            c.create_oval(w - 99 - radius, 102 - radius, w - 99 + radius, 102 + radius,
                          outline=blend("#222346", accent, .2), width=1)
        c.create_oval(w - 154, 49, w - 42, 169, fill=blend("#222346", character["color"], .38), outline="")
        c.create_text(24, 27, anchor="w", text="YOUR HYDRATION HERO", fill=THEME["cyan"], font=("Segoe UI", 8, "bold"))
        c.create_text(24, 48, anchor="nw", text=character["name"], width=w - 205,
                      fill=THEME["text"], font=("Segoe UI", 21, "bold"))
        c.create_text(24, 115, anchor="nw", text=character["subtitle"], width=w - 205,
                      fill="#CDC9E8", font=("Segoe UI", 10))
        rounded(c, (24, 168, 148, 193), 10, fill="#3C345E", outline="")
        c.create_text(86, 180, text=f"{character.get('group', 'Original')} SIDEKICK".upper(),
                      fill="#DCD3FF", font=("Segoe UI", 8, "bold"))
        self._art(c, key, w - 92, 135, .87)

    def update_status(self, enabled):
        self.state_badge.configure(text="  ● REMINDERS ACTIVE  " if enabled else "  ● REMINDERS PAUSED  ",
                                   fg=THEME["green"] if enabled else THEME["muted"])

    def saved(self):
        self.feedback_var.set("Settings saved. You're all set.")
        self.save_button.configure(text="Saved")
        if self.save_feedback_job:
            self.app.root.after_cancel(self.save_feedback_job)
        self.save_feedback_job = self.app.root.after(2500, self._clear_save_feedback)

    def _clear_save_feedback(self):
        self.save_feedback_job = None
        self.save_button.configure(text="Save")
        self.feedback_var.set("")
