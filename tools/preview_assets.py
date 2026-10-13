"""Make local review contact sheets from PNGimg gallery thumbnails."""

import concurrent.futures
import io
import json
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import sys

from PIL import Image, ImageDraw


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.link = ""
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.link = attrs.get("href", "")
        if tag == "img" and (attrs.get("itemprop") == "thumbnail" or attrs.get("src", "").startswith("/thumb/")):
            self.images.append({"url": attrs["src"], "page": self.link})


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "SipSidekick asset review"}), timeout=25) as response:
        return response.read()


def main():
    folder = Path(tempfile.gettempdir()) / "sipsidekick-asset-review"
    folder.mkdir(exist_ok=True)
    categories = {"spider_man": 98, "ironman": 16, "captain_america": 12,
                  "batman": 16, "superman": 16, "wonder_woman": 12}
    if "--extras" in sys.argv:
        categories = {"the-flash": 14, "thor": 24}
    for category, limit in categories.items():
        gallery = Gallery()
        url = f"https://freepngimg.com/movies/{category}" if "--extras" in sys.argv else f"https://pngimg.com/images/heroes/{category}"
        gallery.feed(fetch(url).decode())
        images = gallery.images[:limit]
        for item in images:
            item["url"] = urljoin(url, item["url"])
            item["page"] = urljoin(url, item["page"])
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(fetch, item["url"]): item for item in images}
            for future, item in futures.items():
                try:
                    data = future.result()
                    image = Image.open(io.BytesIO(data)).convert("RGBA")
                    image.thumbnail((136, 140))
                    results.append((item, image))
                except Exception as error:
                    print(item["url"], error)
        sheet = Image.new("RGB", (800, ((len(results) + 4) // 5) * 170), "#DDE6EE")
        draw = ImageDraw.Draw(sheet)
        for index, (item, image) in enumerate(results):
            x, y = (index % 5) * 160, (index // 5) * 170
            sheet.paste(image, (x + (160 - image.width) // 2, y), image)
            draw.text((x + 3, y + 142), Path(item["url"]).stem.replace(category, ""), fill="black")
        sheet.save(folder / f"{category}.jpg")
        (folder / f"{category}.json").write_text(json.dumps([item for item, _ in results], indent=2))
        print(category, len(results), str(folder / f"{category}.jpg"), flush=True)


if __name__ == "__main__":
    main()
