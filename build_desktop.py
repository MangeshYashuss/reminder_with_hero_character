"""Build a self-contained app on the target OS; refuses to overwrite a release."""

import argparse
from datetime import datetime
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent


def make_icons(folder):
    folder.mkdir(parents=True, exist_ok=True)
    # Render the app's existing code-native droplet logo at icon resolution.
    image = Image.new("RGBA", (1024, 1024))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((30, 30, 994, 994), radius=225, fill="#9275FF")
    draw.polygon([(512, 160), (314, 467), (288, 620), (349, 754), (512, 815),
                  (675, 754), (736, 620), (710, 467)], fill="#F5F1FF")
    image.save(folder / "app-icon.png")
    image.save(folder / "app-icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    image.save(folder / "app-icon.icns")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New release directory (must not exist)")
    args = parser.parse_args()
    if sys.platform not in ("win32", "darwin"):
        parser.error("Run this builder on Windows or macOS, matching the desired app.")
    target = "windows" if sys.platform == "win32" else "macos"
    arch = platform.machine().lower().replace("amd64", "x86_64")
    release = (args.output or ROOT / "dist" / f"{target}-{arch}").resolve()
    if release.exists():
        parser.error(f"Release already exists: {release}. Choose a new --output directory.")
    work = ROOT / "build" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    work.mkdir(parents=True)
    icons = work / "icons"
    make_icons(icons)
    command = [sys.executable, "-m", "PyInstaller", "--windowed", "--onedir", "--name", "SipSidekick",
               "--distpath", str(release), "--workpath", str(work / "cache"), "--specpath", str(work),
               "--add-data", f"{ROOT / 'assets' / 'characters'}:assets/characters",
               "--add-data", f"{icons / 'app-icon.png'}:assets",
               "--icon", str(icons / ("app-icon.ico" if target == "windows" else "app-icon.icns"))]
    if target == "macos":
        command += ["--osx-bundle-identifier", "com.sipsidekick.desktop"]
    subprocess.run(command + [str(ROOT / "main.py")], cwd=ROOT, check=True)
    shutil.copy2(ROOT / "PACKAGING.txt", release / "READ-ME.txt")
    shutil.copy2(ROOT / "assets" / "characters" / "CREDITS.txt", release / "ARTWORK-CREDITS.txt")
    archive = release / f"SipSidekick-{target}-{arch}.zip"
    if target == "macos":
        # ditto preserves app symlinks, executable modes, and bundle metadata.
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                        str(release / "SipSidekick.app"), str(archive)], check=True)
    else:
        with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted((release / "SipSidekick").rglob("*")):
                if path.is_file():
                    bundle.write(path, path.relative_to(release))
            bundle.write(release / "READ-ME.txt", "READ-ME.txt")
            bundle.write(release / "ARTWORK-CREDITS.txt", "ARTWORK-CREDITS.txt")
    print(f"Built: {archive}")


if __name__ == "__main__":
    main()
