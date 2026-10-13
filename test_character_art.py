"""Artwork loading and animation timing regressions."""

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from character_art import ARTWORK, ASSET_ROOT, CharacterArt, load_clip
from heroes import HEROES


class ArtworkTests(unittest.TestCase):
    def test_bundled_hero_artwork_and_pose_transparency(self):
        for hero in HEROES:
            for phase in ("arrival", "landing", "idle"):
                with self.subTest(hero=hero, phase=phase):
                    clip = ARTWORK.clip(hero, phase)
                    self.assertIsNotNone(clip)
                    self.assertLess(clip.frames[0].getchannel("A").getextrema()[0], 255)

    def test_downloaded_assets_have_source_attribution(self):
        for poses in ARTWORK.manifest.values():
            for entry in poses.values():
                self.assertTrue((ASSET_ROOT / entry["file"]).is_file())
                self.assertTrue(entry["page"].startswith("https://"))

    def test_animated_clip_honors_frame_durations_and_loops(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip.gif"
            first = Image.new("RGBA", (12, 12), "red")
            second = Image.new("RGBA", (12, 12), "blue")
            first.save(path, save_all=True, append_images=[second], duration=[100, 200], loop=0)
            clip = load_clip(path)
            self.assertEqual(len(clip.frames), 2)
            self.assertEqual(clip.frame_index(.05), 0)
            self.assertEqual(clip.frame_index(.15), 1)
            self.assertEqual(clip.frame_index(.35), 0)

    def test_missing_and_corrupt_images_allow_canvas_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "bad.png").write_bytes(b"not an image")
            (folder / "manifest.json").write_text(json.dumps({
                "missing": {"idle": {"file": "missing.png"}},
                "corrupt": {"idle": {"file": "bad.png"}},
                "escape": {"idle": {"file": "../outside.png"}},
            }))
            bank = CharacterArt(folder)
            with self.assertLogs("character_art", level="WARNING"):
                self.assertIsNone(bank.clip("missing"))
                self.assertIsNone(bank.clip("corrupt"))
            self.assertIsNone(bank.clip("escape"))


if __name__ == "__main__":
    unittest.main()
