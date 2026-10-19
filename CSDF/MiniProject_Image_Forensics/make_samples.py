#!/usr/bin/env python3
"""
Sample evidence generator for the Digital Image Forensics mini project.
=======================================================================
Creates three synthetic images so that the tool can be demonstrated and
tested without using a real photograph:

    original.jpg       - a clean "camera" JPEG with EXIF + GPS metadata
    tampered.jpg       - the same scene after a region was blurred and
                         re-compressed at a low quality (object removal /
                         retouching), with editor EXIF (GIMP) and no camera
                         information
    copy_resized.jpg   - the original image resized and re-saved, used to
                         show that dHash still finds the same picture
    ground_truth.json  - coordinates of the manipulated region

Run directly:
    python3 make_samples.py               # create files in ./sample_images
    python3 make_samples.py -o my_dir     # choose another folder
"""

from __future__ import annotations

import argparse
import io
import json
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageEnhance
except ImportError:
    print("This script needs Pillow:  python3 -m pip install -r requirements.txt")
    sys.exit(1)

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

WIDTH, HEIGHT = 900, 600
HORIZON = 390
# The region that will be smoothed / re-compressed (a classic "object
# removal" retouch).  Coordinates are (x0, y0, x1, y1) of the original image.
TAMPER_BOX = (560, 445, 760, 560)
TAMPER_DESCRIPTION = (
    "A patch of grass was replaced with a region taken from a different "
    "(noisier) source, re-compressed at quality 55 and pasted back; the file "
    "was then saved with GIMP metadata and no camera information."
)


# ----------------------------------------------------------------------
#  Drawing
# ----------------------------------------------------------------------

def _draw_scene() -> Image.Image:
    """Draw a simple outdoor scene: sky, sun, clouds, house, tree, grass."""
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    # sky gradient
    for y in range(HORIZON):
        t = y / HORIZON
        draw.line((0, y, WIDTH, y),
                  fill=(int(120 + 80 * t), int(175 + 50 * t), int(235 + 15 * t)))

    # ground gradient
    for y in range(HORIZON, HEIGHT):
        t = (y - HORIZON) / (HEIGHT - HORIZON)
        draw.line((0, y, WIDTH, y),
                  fill=(int(95 - 55 * t), int(150 - 70 * t), int(70 - 35 * t)))

    # sun with a soft double edge
    draw.ellipse((700, 50, 820, 170), fill=(255, 224, 105))
    draw.ellipse((712, 62, 808, 158), fill=(255, 240, 160))

    # clouds
    for cx, cy, radius in ((180, 100, 40), (225, 116, 30), (138, 118, 28),
                           (560, 88, 34), (602, 104, 26), (620, 120, 22)):
        draw.ellipse((cx - radius, cy - radius // 2, cx + radius, cy + radius // 2),
                     fill=(248, 250, 253))

    # distant hills
    draw.polygon(((0, HORIZON), (160, 330), (320, HORIZON)), fill=(110, 155, 105))
    draw.polygon(((430, HORIZON), (640, 315), (900, HORIZON)), fill=(100, 145, 96))

    # house body and roof
    draw.rectangle((175, 250, 430, 410), fill=(212, 186, 152))
    draw.polygon(((150, 256), (302, 162), (458, 256)), fill=(150, 78, 62))
    draw.rectangle((286, 336, 342, 410), fill=(112, 70, 44))            # door
    draw.ellipse((332, 370, 340, 380), fill=(230, 210, 120))            # knob
    draw.rectangle((196, 272, 252, 316), fill=(122, 168, 198))          # window 1
    draw.rectangle((356, 272, 412, 316), fill=(122, 168, 198))          # window 2
    for window_x in (196, 356):
        draw.rectangle((window_x, 272, window_x + 56, 316), outline=(90, 65, 45), width=4)
        draw.line((window_x + 28, 272, window_x + 28, 316), fill=(90, 65, 45), width=4)
        draw.line((window_x, 294, window_x + 56, 294), fill=(90, 65, 45), width=4)
    draw.rectangle((300, 180, 330, 230), fill=(140, 75, 60))            # chimney

    # tree
    draw.rectangle((505, 320, 532, 425), fill=(110, 74, 45))
    draw.ellipse((462, 250, 575, 345), fill=(70, 135, 62))
    draw.ellipse((480, 215, 560, 300), fill=(88, 158, 72))

    # grass texture (random small blades)
    rng = random.Random(20261019)
    for _ in range(4200):
        x = rng.randrange(WIDTH)
        y = rng.randrange(HORIZON + 10, HEIGHT)
        depth = (y - HORIZON) / (HEIGHT - HORIZON)
        green = (int(120 - 55 * depth + rng.randint(-18, 18)),
                 int(165 - 65 * depth + rng.randint(-18, 18)),
                 int(80 - 30 * depth + rng.randint(-15, 15)))
        draw.line((x, y, x + rng.randint(-1, 2), y - rng.randint(2, 6)),
                  fill=green, width=1)

    # simulate sensor noise over the whole scene so that local noise level
    # is roughly uniform (this is what the noise-inconsistency test uses)
    noise = Image.effect_noise((WIDTH, HEIGHT), 6.0).convert("RGB")
    image = ImageChops.add(image, noise, 1.0, -128)
    return image


# ----------------------------------------------------------------------
#  EXIF helpers
# ----------------------------------------------------------------------

def _camera_exif() -> Image.Exif:
    exif = Image.Exif()
    exif[0x010F] = "Canon"                      # Make
    exif[0x0110] = "EOS 200D"                   # Model
    exif[0x0132] = "2026:10:19 10:30:00"        # DateTime
    exif[0x9003] = "2026:10:19 10:30:00"        # DateTimeOriginal
    exif[0x9004] = "2026:10:19 10:30:01"        # DateTimeDigitized
    exif[0x0131] = "Canon Firmware 1.0.2"       # Software
    try:
        # GPS: 19.0741 N, 72.8777 E (Mumbai)
        exif[0x8825] = {1: "N", 2: 19.0741, 3: "E", 4: 72.8777}
    except Exception:
        pass
    return exif


def _editor_exif() -> Image.Exif:
    exif = Image.Exif()
    exif[0x0132] = "2026:10:19 11:45:00"        # DateTime
    exif[0x0131] = "GIMP 2.10.36"               # Software
    return exif


def _portable_exif(exif: Image.Exif) -> bytes:
    """Convert an Exif object to bytes (some Pillow builds need this)."""
    try:
        return exif.tobytes()
    except Exception:
        return b""


# ----------------------------------------------------------------------
#  Public API
# ----------------------------------------------------------------------

def generate_samples(directory, force: bool = False, verbose: bool = True) -> dict:
    """Create original.jpg, tampered.jpg and copy_resized.jpg in *directory*."""
    directory = Path(directory).expanduser()
    directory.mkdir(parents=True, exist_ok=True)

    original_path = directory / "original.jpg"
    tampered_path = directory / "tampered.jpg"
    copy_path = directory / "copy_resized.jpg"
    truth_path = directory / "ground_truth.json"

    paths = {
        "original": original_path,
        "tampered": tampered_path,
        "copy_resized": copy_path,
        "ground_truth": truth_path,
    }
    if not force and all(path.exists() for path in paths.values()):
        if verbose:
            print("        sample images already exist (use --force to regenerate)")
        return paths

    scene = _draw_scene()
    scene.save(original_path, format="JPEG", quality=90, exif=_camera_exif())

    # ---- tampered version -----------------------------------------
    tampered = scene.copy()
    patch = scene.crop(TAMPER_BOX)

    # The patch comes from a "different camera": it is brighter, less
    # colourful and much noisier than the rest of the scene, and it has a
    # different compression history (quality 55).  Pasting it back is a
    # classic splice, and it disturbs both the compression error level and
    # the local noise variance.
    patch = ImageEnhance.Brightness(patch).enhance(1.15)
    patch = ImageEnhance.Color(patch).enhance(0.55)
    noise = Image.effect_noise(patch.size, 14.0).convert("RGB")
    patch = ImageChops.add(patch, noise, 1.0, -128)

    buffer = io.BytesIO()
    patch.save(buffer, format="JPEG", quality=55)
    buffer.seek(0)
    with Image.open(buffer) as compressed_patch:
        patch = compressed_patch.convert("RGB")

    tampered.paste(patch, TAMPER_BOX[:2])
    tampered.save(tampered_path, format="JPEG", quality=90, exif=_editor_exif())

    # ---- resized / re-saved copy ----------------------------------
    small = scene.resize((int(WIDTH * 0.55), int(HEIGHT * 0.55)), LANCZOS)
    small = ImageEnhance.Brightness(small).enhance(1.04)
    small.save(copy_path, format="JPEG", quality=72)

    ground_truth = {
        "original": original_path.name,
        "tampered": tampered_path.name,
        "copy_resized": copy_path.name,
        "tamper_box": list(TAMPER_BOX),
        "description": TAMPER_DESCRIPTION,
    }
    truth_path.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")

    if verbose:
        print(f"        created {original_path.name:16s} {WIDTH}x{HEIGHT}  "
              f"camera EXIF + GPS")
        print(f"        created {tampered_path.name:16s} {WIDTH}x{HEIGHT}  "
              f"noisy spliced patch + GIMP EXIF")
        print(f"        created {copy_path.name:16s} {small.width}x{small.height}  "
              f"re-saved smaller copy")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate sample evidence images "
                                                 "for the image forensics demo.")
    parser.add_argument("-o", "--output", default=str(Path(__file__).resolve().parent / "sample_images"),
                        help="output directory (default: ./sample_images)")
    parser.add_argument("--force", action="store_true", help="overwrite existing samples")
    args = parser.parse_args()

    print("Generating sample images in:", args.output)
    generate_samples(args.output, force=args.force)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
