"""Download the curated artwork manifest; never overwrite an existing asset."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
import io
import json

from PIL import Image


ROOT = Path(__file__).resolve().parents[1] / "assets" / "characters"


def download(item):
    target = (ROOT / item["file"]).resolve()
    if not target.is_relative_to(ROOT.resolve()):
        raise ValueError("Asset path must stay in the characters directory")
    if target.exists():
        return f"Kept existing {item['file']}"
    with urlopen(Request(item["url"], headers={"User-Agent": "SipSidekick asset downloader"}), timeout=45) as response:
        data = response.read(20 * 1024 * 1024)
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        if "A" not in image.getbands() or image.getchannel("A").getextrema()[0] == 255:
            raise ValueError(f"Asset is not transparent: {item['file']}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as file:
        file.write(data)
    return f"Saved {item['file']} ({len(data):,} bytes)"


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(download, [item for poses in manifest.values() for item in poses.values()]):
            print(result, flush=True)


if __name__ == "__main__":
    main()
