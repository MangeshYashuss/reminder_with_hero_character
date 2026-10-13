"""Character personalities and finite, non-flashing reminder animations."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Presentation:
    heading: str
    message: str
    detail: str
    background: str
    accent: str
    foreground: str
    entrance: str
    reveal: str
    duration: float = 1.6


PRESENTATIONS = {
    "spiderman": Presentation("NEIGHBORHOOD WATER CHECK", "Hey, web-head! Swing by your water bottle.", "Even a busy hero needs a sip between swings.", "#FFF8F2", "#BE3049", "#243653", "web", "bubble"),
    "ironman": Presentation("HYDRATION SYSTEM // ONLINE", "Time to recharge the person inside the suit.", "Hydration check ready. Take a water break.", "#102839", "#75E4F3", "#ECFBFF", "thrusters", "typewriter", 2.0),
    "thor": Presentation("A MESSAGE FROM ASGARD", "Raise your water bottle, mighty friend!", "A small pause before your next mighty task.", "#18283F", "#F4D081", "#F8F1DF", "lightning", "runes", 1.8),
    "captain_america": Presentation("YOUR NEXT MISSION", "Team up with your water bottle.", "Mission briefing: pause, take a sip, carry on.", "#F0F5FC", "#285A9A", "#193655", "shield", "briefing"),
    "batman": Presentation("GOTHAM // PRIVATE TRANSMISSION", "A water break belongs in the plan.", "The next task can wait while you take a sip.", "#1B222D", "#F1D36F", "#F5F4E9", "glide", "signal", 1.9),
    "superman": Presentation("A LITTLE EVERYDAY SUPERPOWER", "Take a sip. Then get back to doing good.", "A moment for yourself, before helping the world.", "#EEF7FF", "#2364A9", "#203956", "flight", "banner"),
    "wonder_woman": Presentation("A MOMENT OF STRENGTH", "Care for yourself, brave one. Water break!", "Give yourself the same care you give others.", "#FFF7EB", "#9D3447", "#482C3B", "lasso", "ribbon", 1.9),
    "flash": Presentation("QUICK PIT STOP", "Fast day? Slow down for a sip.", "Your next task will still be there in a moment.", "#3B1926", "#FFDB70", "#FFF7E8", "speed", "speedlines", 1.1),
    "drop": Presentation("DEWEY'S SPLASH BREAK", "A little sip, a little refresh.", "Your water bottle would love a visit.", "#EEFCFD", "#117987", "#163B47", "splash", "ripples"),
    "robot": Presentation("BLOOP // FRIENDLY CHECK-IN", "Pause task. Pick up water. Enjoy sip.", "A tiny maintenance break for a busy human.", "#F2F1FF", "#6253AC", "#303253", "boot", "terminal", 1.8),
    "cat": Presentation("MOCHI'S PAW-SOME PAUSE", "Psst... time for a cozy water break.", "Stretch your paws and reach for your bottle.", "#FFF4EF", "#A54E3C", "#50372F", "pounce", "pawprints"),
    "plant": Presentation("SPRIG'S GENTLE NUDGE", "A little water. A little moment for you.", "Slow down, take a sip, and keep growing.", "#F0F9EF", "#39774B", "#294534", "grow", "leaves", 2.0),
}


def entrance_pose(kind: str, progress: float) -> tuple[float, float, float]:
    """Return local x/y offset and scale; every entrance ends at (0, 0, 1)."""
    p = max(0.0, min(1.0, progress))
    remaining = (1 - p) ** 3
    wave = math.sin(math.pi * p)
    if kind == "web":
        return 18 * math.sin(3 * math.pi * p) * (1 - p), -235 * remaining, 1
    if kind == "thrusters":
        return 0, 170 * remaining - 12 * wave, 1
    if kind == "lightning":
        return 0, -45 * remaining, 0.8 + 0.2 * p
    if kind == "shield":
        return -145 * remaining, -18 * abs(math.sin(2 * math.pi * p)) * (1 - p), 1
    if kind == "glide":
        return -90 * remaining, -125 * remaining, 1
    if kind == "flight":
        return 135 * remaining, 150 * remaining - 80 * wave, 1
    if kind == "lasso":
        return -32 * wave, -18 * wave, 0.75 + 0.25 * p
    if kind == "speed":
        return -230 * remaining + 18 * math.sin(2 * math.pi * p) * (1 - p), 0, 1
    if kind == "splash":
        return 0, -45 * abs(math.sin(2 * math.pi * p)) * (1 - p), 0.65 + 0.35 * p
    if kind == "boot":
        return 0, 70 * remaining, 1
    if kind == "pounce":
        return -140 * remaining, -85 * wave, 1
    if kind == "grow":
        size = 0.2 + 0.8 * p
        return 0, 60 * (1 - size), size
    return 0, 0, 1


def draw_effect(canvas, style: Presentation, p: float, x: float, y: float):
    """Draw a brief entrance effect behind the character; no repeated flashes."""
    color = style.accent
    kind = style.entrance
    if p >= 1:
        return
    if kind == "web":
        canvas.create_line(x, 0, x, y - 76, fill="#BDC9D8", width=2)
        for offset in (-12, 12):
            canvas.create_line(x, 16, x + offset, 0, fill="#BDC9D8")
    elif kind == "thrusters":
        for offset in (-14, 14):
            canvas.create_polygon(x + offset - 7, y + 53, x + offset + 7, y + 53,
                                 x + offset, y + 90 + 12 * math.sin(p * 18), fill=color, outline="")
    elif kind == "lightning":
        for offset in (-34, 34):
            canvas.create_line(x + offset, 0, x + offset - 12, 48, x + offset + 8, 45,
                               x + offset - 9, 106, fill=color, width=3)
    elif kind == "shield":
        radius = 22 + 30 * p
        canvas.create_arc(x - radius, y - radius, x + radius, y + radius,
                          start=360 * p, extent=260, outline=color, width=3, style="arc")
    elif kind == "glide":
        canvas.create_polygon(x, y - 35, x - 67, y + 28, x - 25, y + 17,
                              x, y + 38, x + 25, y + 17, x + 67, y + 28,
                              fill="#303C4D", outline="")
    elif kind in ("flight", "speed"):
        for row in range(4):
            cy = y - 42 + row * 24
            canvas.create_line(x - 90, cy + (30 if kind == "flight" else 0), x - 43, cy,
                               fill=color, width=2 + row % 2)
    elif kind == "lasso":
        canvas.create_arc(x - 62, y - 86, x + 64, y + 62, start=90,
                          extent=max(1, 359 * p), outline="#CC9A35", width=3, style="arc")
    elif kind == "splash":
        for offset in (-48, -30, 30, 48):
            cy = y + 40 - math.sin(p * math.pi) * abs(offset)
            canvas.create_oval(x + offset - 3, cy - 6, x + offset + 3, cy + 6, fill=color, outline="")
    elif kind == "boot":
        for row in range(3):
            canvas.create_line(x - 40, y + 69 + row * 6, x - 40 + 80 * p, y + 69 + row * 6,
                               fill=color, width=2)
    elif kind == "pounce":
        for index in range(3):
            px = 15 + index * 25
            canvas.create_oval(px, 296, px + 9, 302, fill=color, outline="")
    elif kind == "grow":
        for offset in (-42, 32):
            cy = y - 60 + 35 * p
            canvas.create_oval(x + offset, cy, x + offset + 12, cy + 6, fill=color, outline="")


def draw_card(canvas, style: Presentation, p: float, rounded):
    """Distinct comic, HUD, briefing, signal, and organic message surfaces."""
    bg, accent = style.background, style.accent
    motif = style.reveal
    radius = 5 if motif in ("typewriter", "briefing", "terminal", "signal") else 24
    rounded(canvas, 144, 24, 512, 325, radius, fill=bg, outline=accent, width=2)
    if motif == "bubble":
        canvas.create_polygon(146, 213, 111, 239, 158, 234, fill=bg, outline=accent, width=2)
        for offset in (0, 10, 20):
            canvas.create_line(482 - offset, 25, 511, 55 + offset, fill=accent)
    elif motif in ("typewriter", "terminal"):
        for x, direction in ((151, 1), (505, -1)):
            canvas.create_line(x, 45, x, 31, x + 28 * direction, 31, fill=accent, width=3)
        canvas.create_line(162, 78, 492, 78, fill=accent)
        if p < 1:
            canvas.create_line(154, 82 + 169 * p, 501, 82 + 169 * p, fill=accent)
    elif motif == "runes":
        for cx in range(165, 500, 28):
            canvas.create_line(cx, 40, cx + 6, 32, cx + 12, 40, cx + 6, 48, cx, 40, fill=accent)
    elif motif == "briefing":
        canvas.create_rectangle(145, 25, 157, 324, fill=accent, outline="")
        canvas.create_line(172, 79, 486, 79, fill=accent, dash=(5, 3))
    elif motif == "signal":
        canvas.create_oval(425, 35, 493, 72, outline=accent)
        canvas.create_polygon(435, 45, 450, 50, 458, 40, 464, 46, 472, 40, 478, 50,
                              487, 45, 478, 61, 469, 58, 461, 66, 452, 58, 444, 61, fill=accent)
    elif motif == "banner":
        canvas.create_polygon(147, 27, 508, 27, 508, 40, 160, 48, fill="#C83248", outline="")
    elif motif == "ribbon":
        canvas.create_line(159, 44, 176, 53, 190, 40, 204, 53, 221, 44, fill="#C49732", width=3)
        canvas.create_arc(446, 38, 497, 71, start=0, extent=max(1, p * 359), style="arc", outline="#C49732", width=2)
    elif motif == "speedlines":
        for offset in (0, 10, 20):
            canvas.create_line(465 + offset, 28, 431 + offset, 65, fill=accent, width=3)
    elif motif == "ripples":
        for radius in (10, 18, 26):
            canvas.create_oval(476 - radius, 50 - radius / 2, 476 + radius, 50 + radius / 2, outline=accent)
    elif motif == "pawprints":
        for cx in (455, 480):
            canvas.create_oval(cx, 43, cx + 12, 54, fill=accent, outline="")
            for dx in (-2, 4, 10):
                canvas.create_oval(cx + dx, 36, cx + dx + 5, 42, fill=accent, outline="")
    elif motif == "leaves":
        canvas.create_line(453, 61, 494, 35, fill=accent, width=2)
        for cx in (462, 478):
            canvas.create_oval(cx, 33, cx + 12, 46, fill=accent, outline="")


def revealed_message(message: str, style: Presentation, progress: float) -> str:
    """Finish revealing text before the entrance completes."""
    p = max(0.0, min(1.0, (progress - 0.12) / 0.74))
    if style.reveal in ("typewriter", "terminal", "signal"):
        return message[:int(len(message) * p)]
    if style.reveal in ("briefing", "runes", "leaves", "pawprints"):
        words = message.split()
        return " ".join(words[:math.ceil(len(words) * p)]) if p < 1 else message
    return message if p > 0 else ""
