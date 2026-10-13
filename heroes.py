"""Scalable superhero artwork drawn directly on a Tk canvas."""

HEROES = {
    "spiderman": {"name": "Spider-Man", "subtitle": "Friendly neighborhood", "color": "#C83248", "group": "Marvel"},
    "ironman": {"name": "Iron Man", "subtitle": "Suit up & recharge", "color": "#AC303B", "group": "Marvel"},
    "thor": {"name": "Thor", "subtitle": "A mighty water break", "color": "#416C96", "group": "Marvel"},
    "captain_america": {"name": "Captain America", "subtitle": "Ready for the next mission", "color": "#285A9A", "group": "Marvel"},
    "batman": {"name": "Batman", "subtitle": "Gotham can wait a minute", "color": "#374151", "group": "DC"},
    "superman": {"name": "Superman", "subtitle": "Recharge your superpowers", "color": "#2165AC", "group": "DC"},
    "wonder_woman": {"name": "Wonder Woman", "subtitle": "Strength in every sip", "color": "#B93244", "group": "DC"},
    "flash": {"name": "The Flash", "subtitle": "Make a quick water stop", "color": "#BE3545", "group": "DC"},
}


def draw_hero(canvas, kind, x, y, scale=1.0):
    """Render a chibi hero within the same bounds as the original sidekicks."""
    ink, skin, gold, white = "#172B40", "#F1C59F", "#F3C857", "#FFFFFF"
    red, blue = "#C83248", "#285A9A"

    def coords(values):
        return [((x if i % 2 == 0 else y) + v * scale) for i, v in enumerate(values)]

    def oval(values, fill, outline=ink):
        return canvas.create_oval(*coords(values), fill=fill, outline=outline, width=max(1, 1.6 * scale))

    def poly(values, fill, outline=ink):
        return canvas.create_polygon(*coords(values), fill=fill, outline=outline, width=max(1, 1.6 * scale), joinstyle="round")

    def line(values, fill=ink, width=2):
        return canvas.create_line(*coords(values), fill=fill, width=max(0.6, width * scale), capstyle="round", joinstyle="round")

    def label(px, py, value, color, size):
        canvas.create_text(x + px * scale, y + py * scale, text=value, fill=color,
                           font=("Segoe UI", max(5, round(size * scale)), "bold"))

    def star(cx, cy, radius, fill):
        import math
        points = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            r = radius if i % 2 == 0 else radius * 0.43
            points.extend((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        poly(points, fill, fill)

    suit = {"spiderman": blue, "ironman": red, "thor": "#55677B",
            "captain_america": blue, "batman": "#778291", "superman": blue,
            "wonder_woman": red, "flash": red}[kind]
    cape = {"thor": red, "batman": "#283345", "superman": red, "wonder_woman": "#243653"}
    if kind in cape:
        poly([-25, -7, -43, 48, -21, 43, 0, 53, 21, 43, 43, 48, 25, -7], cape[kind])
    # Boots, body, and short arms.
    for side in (-1, 1):
        oval([side * 14 - 11, 35, side * 14 + 11, 59], red if kind != "batman" else "#283345")
    poly([-24, -9, 24, -9, 28, 30, 18, 44, -18, 44, -28, 30], suit)
    oval([-37, -2, -22, 31], suit)
    oval([22, -2, 37, 31], suit)
    if kind in ("batman", "superman", "wonder_woman"):
        poly([-25, 27, 25, 27, 24, 33, -24, 33], gold)
    if kind in ("thor", "wonder_woman"):
        oval([-34, -68, 34, 7], gold if kind == "thor" else "#243653")
    face = red if kind in ("spiderman", "ironman", "flash") else (blue if kind == "captain_america" else ("#283345" if kind == "batman" else skin))
    oval([-32, -69, 32, -3], face)

    if kind == "spiderman":
        for end_x, end_y in [(-29, -54), (0, -68), (29, -54), (-31, -28), (31, -28), (-20, -9), (20, -9), (0, -4)]:
            line([0, -35, end_x, end_y], width=1)
        for points in ([-25, -55, -13, -51, 0, -54, 13, -51, 25, -55], [-31, -24, -15, -19, 0, -22, 15, -19, 31, -24], [-24, -13, 0, -11, 24, -13]):
            line(points, width=1)
        poly([-27, -47, -5, -36, -11, -26, -22, -29], white)
        poly([27, -47, 5, -36, 11, -26, 22, -29], white)
        poly([-16, -4, 16, -4, 14, 26, -14, 26], red)
        oval([-4, 5, 4, 18], ink)
        for side in (-1, 1):
            for offset in (0, 5):
                line([0, 10 + offset, side * 10, 4 + offset, side * 13, offset])
                line([0, 12 + offset, side * 10, 17 + offset, side * 13, 23 + offset])
    elif kind == "ironman":
        poly([-22, -61, -7, -55, 7, -55, 22, -61, 26, -32, 17, -12, -17, -12, -26, -32], gold)
        poly([-23, -39, -5, -36, -6, -30, -20, -32], "#C4F6FF")
        poly([23, -39, 5, -36, 6, -30, 20, -32], "#C4F6FF")
        line([-11, -20, 11, -20])
        oval([-11, 1, 11, 23], "#9BE8F6")
        oval([-6, 6, 6, 18], white, white)
        line([-20, 30, -11, 25, 11, 25, 20, 30], gold, 3)
    elif kind == "thor":
        oval([-25, -55, 25, -7], skin)
        poly([-33, -42, -29, -68, 0, -76, 29, -68, 33, -42, 20, -53, -20, -53], "#C4D5E5")
        poly([-29, -58, -46, -74, -40, -51, -29, -42], "#E1ECF5")
        poly([29, -58, 46, -74, 40, -51, 29, -42], "#E1ECF5")
        for px in (-12, 12):
            oval([px - 3, -36, px + 3, -29], ink)
            for py in (4, 21):
                oval([px - 6, py - 5, px + 6, py + 5], "#CFDFEC")
        line([-8, -19, 8, -19])
        line([39, 9, 39, 40], "#8E6041", 6)
        poly([24, -3, 53, -3, 53, 17, 24, 17], "#C4D5E5")
    elif kind == "captain_america":
        oval([-22, -31, 22, -6], skin)
        poly([-25, -44, 25, -44, 23, -25, 8, -29, 0, -22, -8, -29, -23, -25], blue)
        line([-20, -35, -10, -35], white, 3)
        line([10, -35, 20, -35], white, 3)
        label(0, -56, "A", white, 15)
        star(0, 9, 11, white)
        for px in (-14, 0, 14):
            poly([px - 3, 23, px + 3, 23, px + 3, 36, px - 3, 36], white, white)
        for radius, fill in [(23, red), (17, white), (12, red), (8, blue)]:
            oval([28 - radius, 30 - radius, 28 + radius, 30 + radius], fill, fill)
        star(28, 30, 7, white)
    elif kind == "batman":
        poly([-31, -44, -30, -81, -13, -63, 13, -63, 30, -81, 31, -44], "#283345")
        poly([-20, -26, 20, -26, 17, -11, 0, -5, -17, -11], skin)
        poly([-25, -41, -7, -35, -22, -33], white)
        poly([25, -41, 7, -35, 22, -33], white)
        line([-7, -17, 7, -17])
        oval([-20, 0, 20, 20], gold)
        poly([-18, 5, -10, 8, -5, 4, -3, 0, 0, 4, 3, 0, 5, 4, 10, 8, 18, 5, 13, 14, 6, 12, 0, 19, -6, 12, -13, 14], "#283345", "#283345")
    elif kind == "superman":
        poly([-32, -37, -32, -58, -18, -70, 15, -70, 31, -57, 30, -40, 19, -54, 3, -51, 6, -41, -5, -46, -9, -55, -24, -51], "#243653")
        for px in (-13, 13):
            oval([px - 3, -37, px + 3, -29], ink)
        line([-8, -17, 0, -14, 8, -17])
        poly([-19, 4, -11, -2, 11, -2, 19, 4, 0, 23], gold, red)
        label(0, 8, "S", red, 16)
    elif kind == "wonder_woman":
        oval([-24, -58, 24, -7], skin)
        poly([-25, -50, 0, -58, 25, -50, 24, -42, 0, -49, -24, -42], gold)
        star(0, -51, 5, red)
        for px in (-12, 12):
            oval([px - 3, -35, px + 3, -28], ink)
        line([-8, -17, 0, -14, 8, -17], red)
        line([-22, 1, -11, 12, 0, 4, 11, 12, 22, 1], gold, 4)
        poly([-23, 33, 23, 33, 18, 44, -18, 44], blue)
        line([-33, 17, -27, 18], "#CCD9E5", 7)
        line([27, 18, 33, 17], "#CCD9E5", 7)
        oval([29, 22, 44, 49], "", gold)
    elif kind == "flash":
        oval([-21, -28, 21, -7], skin)
        poly([-26, -46, 26, -46, 23, -26, 9, -31, 0, -24, -9, -31, -23, -26], red)
        line([-20, -36, -10, -35], white, 3)
        line([10, -35, 20, -36], white, 3)
        for side in (-1, 1):
            poly([side * 30, -47, side * 42, -60, side * 37, -43, side * 43, -44, side * 30, -26], gold)
        oval([-13, -1, 13, 25], white)
        poly([4, -3, -9, 13, 0, 12, -4, 28, 11, 8, 2, 9], gold, gold)
