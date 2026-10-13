"""Opt-in packaged GUI self-test. Never loads or saves personal settings."""

import json
import sys
import tempfile
import tkinter as tk
from pathlib import Path

from character_art import ARTWORK


def run(report_path, app_class, settings_class, popup_class):
    root = None
    result = {"ok": False, "platform": sys.platform, "frozen": bool(getattr(sys, "frozen", False))}
    try:
        root = tk.Tk()
        errors = []
        root.report_callback_exception = lambda *args: errors.append(str(args))
        app = app_class(root, settings=settings_class(sound=False, enabled=False))
        root.geometry("920x600")
        root.update()
        app.view.spotlight.event_generate("<MouseWheel>", delta=-30)
        root.update()
        assert app.view.scroll.yview()[0] > 0, "Wheel did not move the dashboard"
        for character in ARTWORK.manifest:
            for phase in ("arrival", "landing", "idle"):
                assert ARTWORK.clip(character, phase), f"Missing {character}/{phase}"
            popup = popup_class(root, settings_class(character=character, sound=False), lambda _action: None)
            for elapsed in (0.5, popup.arrival_seconds + .2, popup.arrival_seconds + 2):
                popup._render_elapsed(elapsed)
                assert popup.canvas.find_withtag("character_art"), f"Artwork did not render: {character}"
            popup.dismiss()
        with tempfile.TemporaryDirectory(prefix="sipsidekick-smoke-") as folder:
            path = Path(folder) / "nested" / "settings.json"
            expected = settings_class(character="batman")
            expected.save(path)
            assert settings_class.load(path) == expected
        root.update()
        assert not errors, errors
        result.update(ok=True, characters=len(ARTWORK.manifest), tk=root.tk.call("info", "patchlevel"))
    except Exception as error:
        result["error"] = repr(error)
        raise
    finally:
        if root is not None:
            root.destroy()
        report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
