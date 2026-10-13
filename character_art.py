"""Local, cached PNG/WebP/GIF character artwork for Tkinter canvases."""

from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
import json
import logging
from pathlib import Path

from PIL import Image, ImageTk, UnidentifiedImageError


ASSET_ROOT = Path(__file__).with_name("assets") / "characters"
LOG = logging.getLogger(__name__)


@dataclass
class Clip:
    frames: list
    durations: list[int]

    def frame_index(self, elapsed):
        position = max(0, int(elapsed * 1000)) % sum(self.durations)
        for index, duration in enumerate(self.durations):
            if position < duration:
                return index
            position -= duration
        return len(self.frames) - 1


@lru_cache(maxsize=32)
def load_clip(path):
    """Decode once, preserving transparency and GIF frame timing/disposal."""
    frames, durations = [], []
    with Image.open(path) as image:
        if image.width * image.height > 24_000_000:
            raise ValueError("Character image is too large")
        for index in range(min(getattr(image, "n_frames", 1), 120)):
            image.seek(index)
            frame = image.convert("RGBA")
            frame.thumbnail((512, 512), Image.Resampling.LANCZOS)
            frames.append(frame)
            durations.append(max(20, min(5000, int(image.info.get("duration", 100)))))
    # Use a common crop for the whole clip, preventing frame-to-frame jitter.
    boxes = [frame.getchannel("A").getbbox() for frame in frames]
    boxes = [box for box in boxes if box]
    if not boxes:
        raise ValueError("Character image is fully transparent")
    crop = (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))
    return Clip([frame.crop(crop) for frame in frames], durations)


class CharacterArt:
    def __init__(self, folder=ASSET_ROOT):
        self.folder = Path(folder).resolve()
        try:
            self.manifest = json.loads((self.folder / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.manifest = {}
        self.failed = set()

    def clip(self, character, phase="idle"):
        poses = self.manifest.get(character, {})
        entry = poses.get(phase, poses.get("idle", {}))
        if not entry.get("file"):
            return None
        path = (self.folder / entry["file"]).resolve()
        if not path.is_relative_to(self.folder) or path in self.failed:
            return None
        try:
            return load_clip(path)
        except (OSError, ValueError, UnidentifiedImageError) as error:
            self.failed.add(path)
            LOG.warning("Character artwork unavailable for %s: %s", character, error)
            return None

    def is_animated(self, character, phase="idle"):
        clip = self.clip(character, phase)
        return bool(clip and len(clip.frames) > 1)

    def draw(self, canvas, character, x, y, scale=1.0, phase="idle", elapsed=0.0, stretch=(1, 1)):
        clip = self.clip(character, phase)
        if not clip:
            return False
        frame_index = clip.frame_index(elapsed)
        frame = clip.frames[frame_index]
        fit = min(132 / frame.width, 200 / frame.height) * scale
        width = max(1, round(frame.width * fit * stretch[0]))
        height = max(1, round(frame.height * fit * stretch[1]))
        # Tk doesn't scale image pixels with canvas.scale; resize the raster itself.
        key = (id(clip), frame_index, width, height)
        cache = getattr(canvas, "_character_image_cache", None)
        if cache is None:
            cache = canvas._character_image_cache = OrderedDict()
        if key not in cache:
            rendered = frame.resize((width, height), Image.Resampling.LANCZOS)
            # Windows color-key transparency has no partial-alpha compositor.
            # Clean the soft outer edge at display size to avoid a dark fringe.
            if str(canvas.cget("background")).lower() == "#010203":
                rendered.putalpha(rendered.getchannel("A").point(lambda a: 255 if a >= 100 else 0))
            cache[key] = ImageTk.PhotoImage(rendered, master=canvas)
        cache.move_to_end(key)
        while len(cache) > 48:
            cache.popitem(last=False)
        canvas.create_image(x, y + 59 * scale, image=cache[key], anchor="s", tags="character_art")
        return True


ARTWORK = CharacterArt()
