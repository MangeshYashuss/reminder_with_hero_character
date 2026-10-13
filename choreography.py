"""Desktop-space entrance, landing, and message phases for each sidekick."""

import math
from dataclasses import dataclass


LANDING_SECONDS = 0.65
MESSAGE_SECONDS = 1.15


def clamp(value):
    return max(0.0, min(1.0, value))


def smooth(value):
    p = clamp(value)
    return p * p * (3 - 2 * p)


def animation_phase(elapsed, arrival_seconds):
    if elapsed < arrival_seconds:
        return "arrival", clamp(elapsed / arrival_seconds)
    if elapsed < arrival_seconds + LANDING_SECONDS:
        return "landing", clamp((elapsed - arrival_seconds) / LANDING_SECONDS)
    return "message", clamp((elapsed - arrival_seconds - LANDING_SECONDS) / MESSAGE_SECONDS)


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    scale: float = 1.0


def desktop_pose(kind, p, target_x, target_y, screen_width, screen_height):
    """Coordinates use desktop space; the web always starts above its top edge."""
    p = clamp(p)
    ease = smooth(p)
    remaining = 1 - ease
    if kind == "web":
        # Lower on the web, hang for a beat, then release into a short fall.
        hanging_y = target_y - 145
        if p < 0.47:
            y = -95 + (hanging_y + 95) * smooth(p / 0.47)
        elif p < 0.67:
            y = hanging_y + 4 * math.sin((p - 0.47) / 0.2 * math.pi)
        else:
            fall = (p - 0.67) / 0.33
            y = hanging_y + 145 * fall * fall
        return Pose(target_x + 15 * math.sin(p * math.pi * 3) * remaining, y)
    if kind == "thrusters":
        return Pose(target_x + 95 * remaining, target_y - (target_y + 100) * remaining - 24 * math.sin(math.pi * p))
    if kind == "lightning":
        return Pose(target_x, -100 + (target_y + 100) * p * p)
    if kind == "shield":
        return Pose(-70 + (target_x + 70) * ease, target_y - abs(math.sin(p * math.pi * 6)) * 12 * remaining)
    if kind == "glide":
        return Pose(target_x - (target_x + 90) * remaining, target_y - (target_y + 130) * remaining)
    if kind == "flight":
        return Pose(screen_width + 80 + (target_x - screen_width - 80) * ease,
                    -100 + (target_y + 100) * ease - 100 * math.sin(math.pi * p))
    if kind == "lasso":
        return Pose(target_x - 260 * remaining, target_y - 180 * math.sin(math.pi * p))
    if kind == "speed":
        return Pose(-100 + (target_x + 100) * (1 - (1 - p) ** 2), target_y)
    if kind == "splash":
        return Pose(target_x, target_y + 110 * remaining - 120 * math.sin(math.pi * p), 0.65 + 0.35 * ease)
    if kind == "boot":
        return Pose(target_x, screen_height + 100 + (target_y - screen_height - 100) * ease)
    if kind == "pounce":
        return Pose(target_x - (target_x + 60) * remaining, target_y - 220 * math.sin(math.pi * p))
    if kind == "grow":
        size = 0.05 + 0.95 * ease
        return Pose(target_x, target_y + 60 * (1 - size), size)
    return Pose(target_x, target_y)


def landing_transform(kind, p):
    """Squash and settle about the feet, with a different rhythm per character."""
    p = clamp(p)
    pulse = math.sin(math.pi * p) * (1 - p)
    strength = {"web": .60, "thrusters": .22, "lightning": .75, "shield": .32,
                "glide": .42, "flight": .28, "lasso": .35, "speed": .20,
                "splash": .85, "boot": .15, "pounce": .65, "grow": .10}[kind]
    return 1 + strength * pulse * .5, 1 - strength * pulse


def draw_arrival_effect(canvas, style, p, pose, target_x, target_y, screen_width, draw_effect):
    kind, x, y = style.entrance, pose.x, pose.y
    if kind == "web":
        if p < .67:
            canvas.create_line(target_x, 0, x, y - 101, fill="#E4EDF6", width=2)
            for dx in (-12, 12):
                canvas.create_line(target_x, 22, target_x + dx, 0, fill="#E4EDF6")
        else:
            # The released web retracts before the landing.
            length = max(0, target_y - 245) * (1 - (p - .67) / .33)
            canvas.create_line(target_x, 0, target_x, length, fill="#E4EDF6", width=2)
    elif kind == "lightning":
        canvas.create_line(x, 0, x - 22, max(0, y * .3), x + 12, max(0, y * .3 - 15),
                           x - 12, max(0, y - 65), fill=style.accent, width=3)
    else:
        draw_effect(canvas, style, min(.99, p), x, y)
    if kind == "speed":
        for offset in (-33, 0, 33):
            canvas.create_line(max(0, x - screen_width * .35), y + offset,
                               x - 48, y + offset, fill=style.accent, width=3)
    if kind == "shield":
        # A shield leads the run, then returns to the hand.
        shield_x = x + 28 + 125 * math.sin(math.pi * p)
        shield_y = y + 30 - 75 * math.sin(math.pi * p)
        for radius, color in ((23, "#C83248"), (17, "#FFFFFF"), (11, "#285A9A")):
            canvas.create_oval(shield_x - radius, shield_y - radius, shield_x + radius,
                               shield_y + radius, fill=color, outline="")


def draw_landing_effect(canvas, style, p, x, y):
    kind = style.entrance
    if kind in ("web", "lightning", "splash", "pounce"):
        radius = 18 + p * (76 if kind == "lightning" else 48)
        canvas.create_arc(x - radius, y + 53 - 9 * p, x + radius, y + 64 + 9 * p,
                          start=0, extent=180, style="arc", outline=style.accent, width=max(1, 3 * (1 - p)))
    elif kind in ("thrusters", "flight"):
        for dx in (-16, 16):
            canvas.create_line(x + dx, y + 52, x + dx * (1 + p), y + 68,
                               fill=style.accent, width=max(1, 4 * (1 - p)))
    elif kind == "speed":
        for i in range(3):
            canvas.create_line(x - 75 - i * 15 * p, y + 54 + i * 3, x - 24, y + 54 + i * 3,
                               fill=style.accent, width=2)
    elif kind == "lasso":
        canvas.create_arc(x - 60, y - 90, x + 60, y + 60, start=360 * p, extent=359 * (1 - p),
                          style="arc", outline="#CC9A35", width=2)
    elif kind == "glide":
        canvas.create_polygon(x - 25, y - 5, x - 65 * (1 - p) - 25, y + 44,
                              x, y + 32, x + 65 * (1 - p) + 25, y + 44, x + 25, y - 5,
                              fill="#303C4D", outline="")
