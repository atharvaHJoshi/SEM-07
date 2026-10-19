#!/usr/bin/env python3
"""
Mini Project : Digital Image Forensics Tool
===========================================
A command-line tool that examines a suspect image the way a digital
forensics examiner would:

  1. Chain of custody   - SHA-256 / MD5 hashes, size, format, dimensions.
  2. Metadata analysis  - EXIF camera data, timestamps, GPS, editor
                          signatures hidden inside the file bytes.
  3. Error Level Analysis (ELA)
  4. Noise inconsistency analysis (Laplacian variance per block)
  5. Perceptual hash (dHash)  - detects re-saved / resized copies.
  6. A heuristic tamper-suspicion score + HTML / JSON reports.

Primary mathematical formula (Error Level Analysis)
--------------------------------------------------
    I_q(x, y) = JPEG( I(x, y), quality = q )        re-compressed image
    E(x, y)   = | I(x, y) - I_q(x, y) | * s         error level

A JPEG image that was saved once has a smooth, low error level.  A region
that was pasted, cloned or re-saved has a different compression history and
therefore shows a different error level.  Blocks whose error level deviates
strongly from the median are marked as anomalies.

Noise inconsistency formula (Laplacian variance)
------------------------------------------------
    L(x, y) = I(x-1,y) + I(x+1,y) + I(x,y-1) + I(x,y+1) - 4*I(x, y)
    Var(B)  = (1 / n) * sum over (x,y) in B of ( L(x,y) - mean_B )^2
    z(B)    = 0.6745 * ( Var(B) - median(Var) ) / MAD

where MAD is the median absolute deviation of all block variances.  A pasted
or blurred region has a different noise level, so |z(B)| becomes large.

Perceptual hash formula (dHash)
-------------------------------
    H(i, j) = 1 if I(i, j) < I(i, j+1) else 0
    distance(H1, H2) = population count of (H1 XOR H2)

Run "python3 image_forensics.py --help" to see all options.
Run "python3 image_forensics.py --demo" to generate sample evidence images
and let the tool analyse them automatically (self-test).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import io
import json
import math
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from PIL import ExifTags, Image, ImageChops, ImageDraw, ImageFilter, ImageOps
except ImportError:  # friendly message instead of a long traceback
    print("=" * 66)
    print("  Pillow is not installed, so image processing cannot start.")
    print("=" * 66)
    print("Install it with one of these commands:")
    print()
    print("    python3 -m pip install -r requirements.txt")
    print("    python3 -m pip install Pillow")
    print()
    sys.exit(1)

# Pillow 9 renamed the resampling constants; this keeps old versions working.
LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

APP_NAME = "CSDF Digital Image Forensics Tool"
VERSION = "1.0"

PROJECT_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = PROJECT_DIR / "sample_images"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "output"

DEFAULT_ELA_QUALITY = 90
DEFAULT_ELA_SCALE = 15
DEFAULT_BLOCK = 16
DEFAULT_Z = 3.5
DEFAULT_MAX_SIDE = 1400

# Signatures of image editors / social-media save pipelines.  They are
# searched in the raw file bytes, so they also find hidden XMP or thumbnails.
EDITOR_MARKERS = (
    "photoshop", "gimp", "lightroom", "snapseed", "picsart", "canva",
    "facetune", "faceapp", "paint.net", "pixelmator", "affinity photo",
    "acdsee", "picasa", "inkscape", "krita", "photopea", "meitu",
    "youcam", "vsco",
)
# Words that are only trusted when they appear in the Software tag (they are
# too generic for a raw byte scan).
EDITOR_WORDS = ("editor", "retouch", "remake")

LAPLACIAN_KERNEL = (0, -1, 0, -1, 4, -1, 0, -1, 0)


# ----------------------------------------------------------------------
#  Small helpers
# ----------------------------------------------------------------------

def human_bytes(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def unique_directory(path: Path) -> Path:
    """Return path, or path_2 / path_3 ... if it already exists."""
    if not path.exists():
        return path
    counter = 2
    while (candidate := path.with_name(f"{path.name}_{counter}")).exists():
        counter += 1
    return candidate


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def byte_entropy(path: Path, limit: int = 4_000_000) -> float:
    """Shannon entropy of the file bytes: H = -sum p(i) * log2(p(i))."""
    counts = [0] * 256
    total = 0
    with open(path, "rb") as handle:
        data = handle.read(limit)
    for byte in data:
        counts[byte] += 1
        total += 1
    if not total:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts if c)


def _to_text(value) -> str:
    """Render an EXIF value as readable text (never crash on odd types)."""
    if isinstance(value, bytes):
        text = value.decode("utf-8", "replace").strip("\x00")
        return text[:200] if text else f"<{len(value)} bytes>"
    if isinstance(value, (tuple, list)):
        if len(value) > 8:
            return f"<{len(value)} values>"
        return ", ".join(_to_text(v) for v in value)
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _read_ifd(exif, tag_id: int) -> dict:
    """Read a sub-IFD (Exif / GPS) from a Pillow Exif object."""
    try:
        if exif is not None and hasattr(exif, "get_ifd"):
            data = exif.get_ifd(tag_id)
            if data:
                return dict(data)
    except Exception:
        pass
    return {}


def _rational_to_float(value) -> float:
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return float(value[0]) / float(value[1]) if value[1] else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _gps_component(value):
    """GPS values are either one number or (degrees, minutes, seconds)."""
    if isinstance(value, (tuple, list)):
        if len(value) >= 3:
            degrees, minutes, seconds = (_rational_to_float(v) for v in value[:3])
            return degrees + minutes / 60.0 + seconds / 3600.0
        if len(value) == 2:
            return _rational_to_float(value)
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------
#  File identity / chain of custody
# ----------------------------------------------------------------------

def describe_file(path: Path, image: Image.Image) -> dict:
    size = path.stat().st_size
    width, height = image.size
    return {
        "path": str(path.resolve()),
        "name": path.name,
        "sha256": sha256_file(path),
        "md5": md5_file(path),
        "size_bytes": size,
        "size_human": human_bytes(size),
        "format": image.format or path.suffix.lstrip(".").upper(),
        "mode": image.mode,
        "width": width,
        "height": height,
        "megapixels": round(width * height / 1_000_000, 2),
        "frames": getattr(image, "n_frames", 1),
        "byte_entropy_bits": round(byte_entropy(path), 4),
    }


# ----------------------------------------------------------------------
#  Metadata forensics
# ----------------------------------------------------------------------

def scan_editor_signatures(path: Path, limit: int = 2_000_000) -> list:
    """Search the first part of the file for editor names (EXIF/XMP/JPEG)."""
    try:
        data = path.read_bytes()[:limit].lower()
    except OSError:
        return []
    found = []
    for marker in EDITOR_MARKERS:
        if marker.encode("ascii", "ignore") in data:
            found.append(marker)
    return found


def extract_metadata(image: Image.Image, path: Path) -> dict:
    exif = None
    try:
        exif = image.getexif()
    except Exception:
        exif = None

    exif_present = bool(exif)
    exif_data = {}
    if exif:
        for tag_id, value in exif.items():
            name = ExifTags.TAGS.get(tag_id, str(tag_id))
            exif_data[name] = _to_text(value)

    # DateTimeOriginal etc. live in the Exif sub-IFD.
    exif_ifd = _read_ifd(exif, 0x8769)
    for tag_id, value in exif_ifd.items():
        name = ExifTags.TAGS.get(tag_id, str(tag_id))
        if name not in exif_data:
            exif_data[name] = _to_text(value)

    def first(*names):
        for name in names:
            value = exif_data.get(name)
            if value not in (None, "", "0"):
                return value
        return None

    make = first("Make")
    model = first("Model")
    software = first("Software")
    artist = first("Artist")
    copyright_text = first("Copyright")
    datetime_value = first("DateTime")
    datetime_original = first("DateTimeOriginal")
    datetime_digitized = first("DateTimeDigitized")
    orientation = first("Orientation")

    # ---- GPS -------------------------------------------------------
    gps = {}
    gps_ifd = _read_ifd(exif, 0x8825)
    if gps_ifd:
        latitude = _gps_component(gps_ifd.get(2))
        longitude = _gps_component(gps_ifd.get(4))
        if latitude is not None and str(gps_ifd.get(1, "N")).upper().startswith("S"):
            latitude = -latitude
        if longitude is not None and str(gps_ifd.get(3, "E")).upper().startswith("W"):
            longitude = -longitude
        altitude = _gps_component(gps_ifd.get(6))
        if latitude is not None or longitude is not None:
            gps = {
                "latitude": round(latitude, 6) if latitude is not None else None,
                "longitude": round(longitude, 6) if longitude is not None else None,
                "altitude_m": round(altitude, 2) if altitude is not None else None,
            }

    # ---- editor signatures in the raw bytes ------------------------
    markers = set(scan_editor_signatures(path))
    for text in (software, make, model):
        if text:
            lowered = str(text).lower()
            for marker in EDITOR_MARKERS + EDITOR_WORDS:
                if marker in lowered:
                    markers.add(marker)
    markers = sorted(markers)

    # ---- findings --------------------------------------------------
    flags = []
    notes = []

    if markers:
        flags.append({
            "code": "editing-software",
            "detail": "editor signature found in file/metadata: " + ", ".join(markers),
        })
    if exif_present and not make and not model:
        flags.append({
            "code": "missing-camera-info",
            "detail": "EXIF exists but has no camera Make/Model (possible re-save)",
        })
    if not exif_present:
        flags.append({
            "code": "missing-exif",
            "detail": "no EXIF metadata (stripped, screenshot or re-encoded image)",
        })
    if datetime_original and datetime_value and datetime_original != datetime_value:
        flags.append({
            "code": "timestamp-mismatch",
            "detail": f"DateTime ({datetime_value}) != DateTimeOriginal ({datetime_original})",
        })
    if gps:
        notes.append(
            f"GPS location embedded: {gps['latitude']}, {gps['longitude']}"
            + (f" (altitude {gps['altitude_m']} m)" if gps.get("altitude_m") is not None else "")
        )
    if software:
        notes.append(f"Software tag: {software}")

    info = {}
    for key in ("dpi", "jfif", "jfif_unit", "jfif_density", "progressive",
                "progression", "compression", "comment", "icc_profile",
                "transparency", "gamma", "dpi"):
        if key in image.info:
            value = image.info[key]
            if key == "icc_profile" and isinstance(value, bytes):
                info[key] = f"<{len(value)} bytes>"
            else:
                info[key] = _to_text(value)

    return {
        "has_exif": exif_present,
        "make": make,
        "model": model,
        "software": software,
        "artist": artist,
        "copyright": copyright_text,
        "datetime": datetime_value,
        "datetime_original": datetime_original,
        "datetime_digitized": datetime_digitized,
        "orientation": orientation,
        "gps": gps,
        "gps_text": f"{gps.get('latitude')}, {gps.get('longitude')}" if gps else None,
        "editing_signatures": markers,
        "flags": flags,
        "notes": notes,
        "exif": dict(sorted(exif_data.items())),
        "container_info": info,
    }


# ----------------------------------------------------------------------
#  Error Level Analysis
# ----------------------------------------------------------------------

def error_level_analysis(rgb: Image.Image, quality: int, scale: int):
    """Return (error-level image, amplified heatmap, statistics)."""
    buffer = io.BytesIO()
    rgb.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    with Image.open(buffer) as recompressed:
        recompressed = recompressed.convert("RGB")

    difference = ImageChops.difference(rgb, recompressed).convert("L")
    histogram = difference.histogram()
    total = sum(histogram) or 1

    mean = sum(i * count for i, count in enumerate(histogram)) / total
    variance = sum(count * (i - mean) ** 2 for i, count in enumerate(histogram)) / total
    std = math.sqrt(variance)
    maximum = max(i for i, count in enumerate(histogram) if count)
    threshold = mean + 3.0 * std
    hot_pixels = sum(count for i, count in enumerate(histogram) if i > threshold)

    cumulative = 0
    p95 = maximum
    for i, count in enumerate(histogram):
        cumulative += count
        if cumulative >= 0.95 * total:
            p95 = i
            break

    amplified = difference.point(lambda value: min(255, int(value * scale)))
    stats = {
        "quality": quality,
        "scale": scale,
        "mean_residual": round(mean, 3),
        "std_residual": round(std, 3),
        "max_residual": maximum,
        "p95_residual": p95,
        "hot_threshold": round(threshold, 2),
        "hot_fraction": round(hot_pixels / total, 5),
        "hot_percent": round(100 * hot_pixels / total, 3),
    }
    return difference, amplified, stats


# ----------------------------------------------------------------------
#  Block analysis (ELA + Laplacian noise variance)
# ----------------------------------------------------------------------

def block_stats(data: bytes, width: int, height: int, block: int) -> list:
    """Mean and variance of every non-overlapping block of an 8-bit image."""
    stats = []
    block = max(2, int(block))
    for y0 in range(0, height - block + 1, block):
        for x0 in range(0, width - block + 1, block):
            total = 0
            total_square = 0
            for y in range(y0, y0 + block):
                row = data[y * width + x0: y * width + x0 + block]
                total += sum(row)
                total_square += sum(value * value for value in row)
            count = block * block
            mean = total / count
            variance = total_square / count - mean * mean
            stats.append({
                "x": x0,
                "y": y0,
                "mean": mean,
                "var": variance if variance > 0 else 0.0,
            })
    return stats


def robust_outliers(values: list, threshold: float):
    """Robust z-scores using median and MAD.

    z_i = 0.6745 * (x_i - median) / MAD
    A block is an outlier when |z_i| > threshold.
    """
    if not values:
        return [], [], 0.0, 0.0
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)

    if mad > 1e-9:
        scores = [0.6745 * (value - median) / mad for value in values]
    else:
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        scores = [(value - median) / std for value in values] if std > 1e-9 else [0.0] * len(values)

    flags = [abs(score) > threshold for score in scores]
    return flags, scores, median, mad


def merge_regions(blocks: list, block_size: int) -> list:
    """Group adjacent flagged blocks into connected regions (8-neighbourhood)."""
    cells = {(b["x"] // block_size, b["y"] // block_size): b for b in blocks}
    visited = set()
    regions = []

    for start in cells:
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        min_x = min_y = None
        max_x = max_y = None
        count = 0
        while stack:
            cell_x, cell_y = stack.pop()
            count += 1
            x0, y0 = cell_x * block_size, cell_y * block_size
            min_x = x0 if min_x is None else min(min_x, x0)
            min_y = y0 if min_y is None else min(min_y, y0)
            max_x = x0 if max_x is None else max(max_x, x0)
            max_y = y0 if max_y is None else max(max_y, y0)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbour = (cell_x + dx, cell_y + dy)
                    if neighbour in cells and neighbour not in visited:
                        visited.add(neighbour)
                        stack.append(neighbour)
        regions.append({
            "x0": min_x,
            "y0": min_y,
            "x1": max_x + block_size,
            "y1": max_y + block_size,
            "blocks": count,
            "area_px": count * block_size * block_size,
        })

    regions.sort(key=lambda region: region["blocks"], reverse=True)
    return regions


def evaluate_blocks(blocks: list, key: str, block_size: int, threshold: float) -> dict:
    """Flag outlier blocks, merge them into regions and rank the strongest."""
    values = [block[key] for block in blocks]
    flags, scores, median, mad = robust_outliers(values, threshold)

    flagged = []
    for block, flag, score in zip(blocks, flags, scores):
        block["flagged"] = bool(flag)
        block["z"] = round(score, 2)
        if flag:
            flagged.append(block)

    regions = merge_regions(flagged, block_size)
    ranked = sorted(blocks, key=lambda b: abs(b["z"]), reverse=True)[:10]

    return {
        "block_count": len(blocks),
        "flag_count": len(flagged),
        "anomaly_fraction": len(flagged) / len(blocks) if blocks else 0.0,
        "median": median,
        "mad": mad,
        "regions": regions,
        "top_blocks": [
            {"x": b["x"], "y": b["y"], "z": b["z"], "flagged": b["flagged"]}
            for b in ranked
        ],
    }


def fuse_anomalies(ela_blocks: list, noise_blocks: list, block_size: int) -> dict:
    """Agreement map: a block is strongly suspicious only when BOTH the ELA
    test and the noise test flag it.

        A(B) = ELA_flag(B) AND Noise_flag(B)

    Random flags caused by ordinary image edges usually appear in only one
    map; a real splice/clone region usually disturbs both compression and
    noise, so the agreement map greatly reduces false positives.
    """
    ela_by_position = {(b["x"], b["y"]): b for b in ela_blocks}
    fused = []
    for block in noise_blocks:
        other = ela_by_position.get((block["x"], block["y"]))
        if block.get("flagged") and other is not None and other.get("flagged"):
            ela_z = abs(other.get("z", 0.0))
            noise_z = abs(block.get("z", 0.0))
            fused.append({
                "x": block["x"],
                "y": block["y"],
                "z": round(min(ela_z, noise_z), 2),
                "strength": round(ela_z + noise_z, 2),
                "flagged": True,
            })

    regions = merge_regions(fused, block_size)
    ranked = sorted(fused, key=lambda b: b["strength"], reverse=True)[:10]
    total = len(noise_blocks) or 1
    return {
        "flag_count": len(fused),
        "block_count": total,
        "anomaly_fraction": len(fused) / total,
        "regions": regions,
        "blocks": fused,
        "top_blocks": [
            {"x": b["x"], "y": b["y"], "z": b["z"], "flagged": True}
            for b in ranked
        ],
    }


def create_overlay(base: Image.Image, blocks: list, block_size: int) -> Image.Image:
    """Draw flagged blocks on a copy of the image."""
    base_rgba = base.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for block in blocks:
        if not block.get("flagged"):
            continue
        x0, y0 = block["x"], block["y"]
        draw.rectangle(
            [x0, y0, x0 + block_size - 1, y0 + block_size - 1],
            fill=(255, 0, 0, 55),
            outline=(255, 45, 45, 225),
        )
    return Image.alpha_composite(base_rgba, overlay).convert("RGB")


def colorize_heatmap(gray: Image.Image) -> Image.Image:
    """Turn a grayscale error/noise map into a dark-red-yellow heatmap."""
    return ImageOps.colorize(
        gray,
        black=(5, 5, 5),
        white=(255, 255, 0),
        mid=(255, 70, 0),
        midpoint=48,
    )


# ----------------------------------------------------------------------
#  Perceptual hash (dHash)
# ----------------------------------------------------------------------

def dhash(image: Image.Image, hash_size: int = 8) -> int:
    """Difference hash: compare each pixel with its right neighbour."""
    gray = image.convert("L").resize((hash_size + 1, hash_size), LANCZOS)
    pixels = gray.tobytes()          # 8-bit grayscale: one byte per pixel
    bits = 0
    for row in range(hash_size):
        for column in range(hash_size):
            left = pixels[row * (hash_size + 1) + column]
            right = pixels[row * (hash_size + 1) + column + 1]
            bits = (bits << 1) | (1 if left < right else 0)
    return bits


def hamming_distance(first: int, second: int) -> int:
    return bin(first ^ second).count("1")


def hash_hex(value: int) -> str:
    return f"{value:016x}"


# ----------------------------------------------------------------------
#  Suspicion score
# ----------------------------------------------------------------------

def tamper_suspicion_score(ela: dict, noise: dict, localization: dict, metadata: dict) -> dict:
    """Heuristic score.

        S = 100 * ( 0.25*ELA + 0.25*Noise + 0.30*Localisation + 0.20*Metadata )

    Every component is normalized to 0..1 with min(1, value / reference).
    The localisation component uses the largest connected anomaly region,
    because random edge artefacts are scattered while a real edit usually
    forms one compact region.
    """
    ela_component = min(1.0, ela["anomaly_fraction"] / 0.10)
    noise_component = min(1.0, noise["anomaly_fraction"] / 0.10)
    localisation_component = min(
        1.0,
        localization["largest_region_blocks"] / localization["reference_blocks"],
    )
    metadata_component = min(1.0, len(metadata["flags"]) / 3.0)

    score = round(100 * (0.25 * ela_component + 0.25 * noise_component +
                         0.30 * localisation_component + 0.20 * metadata_component))
    if score <= 30:
        level = "LOW"
    elif score <= 60:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "score": score,
        "level": level,
        "components": {
            "ela": round(ela_component, 4),
            "noise": round(noise_component, 4),
            "localisation": round(localisation_component, 4),
            "metadata": round(metadata_component, 4),
        },
        "weights": {"ela": 0.25, "noise": 0.25, "localisation": 0.30, "metadata": 0.20},
        "note": "Heuristic indicator, not proof of tampering. Verify with the original evidence.",
    }


# ----------------------------------------------------------------------
#  Main analysis
# ----------------------------------------------------------------------

def fit_for_analysis(image: Image.Image, max_side: int):
    """Keep the analysis fast: work on a copy whose longest side <= max_side."""
    width, height = image.size
    longest = max(width, height)
    if longest <= max_side:
        return image, 1.0, None
    factor = max_side / longest
    new_size = (max(1, round(width * factor)), max(1, round(height * factor)))
    resized = image.resize(new_size, LANCZOS)
    note = (f"analysis performed on a {new_size[0]}x{new_size[1]} preview "
            f"(scale {factor:.3f}) of the {width}x{height} original")
    return resized, new_size[0] / width, note


def analyze(image_path, output_dir=None, quality=DEFAULT_ELA_QUALITY,
            scale=DEFAULT_ELA_SCALE, block=DEFAULT_BLOCK,
            z_threshold=DEFAULT_Z, max_side=DEFAULT_MAX_SIDE) -> dict:
    start_time = time.time()
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"image not found: {path}")

    if output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = DEFAULT_OUTPUT_DIR / f"{path.stem}_forensics_{stamp}"
    output_dir = unique_directory(Path(output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(path) as image:
        image.load()
        file_info = describe_file(path, image)
        metadata = extract_metadata(image, path)
        rgb_full = image.convert("RGB")
        perceptual_hash = dhash(rgb_full)
        analysis_rgb, preview_factor, preview_note = fit_for_analysis(rgb_full, max_side)

    width, height = analysis_rgb.size

    # ----- Error Level Analysis ------------------------------------
    ela_image, ela_amplified, ela_numbers = error_level_analysis(analysis_rgb, quality, scale)
    ela_blocks = block_stats(ela_image.tobytes(), width, height, block)
    ela_details = evaluate_blocks(ela_blocks, "mean", block, z_threshold)
    ela_stats = {**ela_numbers, **{
        "block_size": block,
        "flag_count": ela_details["flag_count"],
        "block_count": ela_details["block_count"],
        "anomaly_fraction": ela_details["anomaly_fraction"],
        "anomaly_percent": round(100 * ela_details["anomaly_fraction"], 3),
        "regions": ela_details["regions"],
        "top_blocks": ela_details["top_blocks"],
        "median_block_residual": round(ela_details["median"], 3),
        "mad_block_residual": round(ela_details["mad"], 3),
    }}

    # ----- Noise inconsistency (Laplacian variance) ----------------
    gray = analysis_rgb.convert("L")
    laplacian = gray.filter(ImageFilter.Kernel((3, 3), LAPLACIAN_KERNEL, scale=1, offset=128))
    noise_blocks = block_stats(laplacian.tobytes(), width, height, block)
    noise_details = evaluate_blocks(noise_blocks, "var", block, z_threshold)
    noise_stats = {
        "block_size": block,
        "flag_count": noise_details["flag_count"],
        "block_count": noise_details["block_count"],
        "anomaly_fraction": noise_details["anomaly_fraction"],
        "anomaly_percent": round(100 * noise_details["anomaly_fraction"], 3),
        "regions": noise_details["regions"],
        "top_blocks": noise_details["top_blocks"],
        "median_block_variance": round(noise_details["median"], 3),
        "mad_block_variance": round(noise_details["mad"], 3),
    }

    # ----- Agreement between the two independent tests -------------
    agreement_details = fuse_anomalies(ela_blocks, noise_blocks, block)
    agreement_stats = {
        "rule": "a block is strongly suspicious when flagged by BOTH ELA and noise",
        "block_size": block,
        "flag_count": agreement_details["flag_count"],
        "block_count": agreement_details["block_count"],
        "anomaly_fraction": agreement_details["anomaly_fraction"],
        "anomaly_percent": round(100 * agreement_details["anomaly_fraction"], 3),
        "regions": agreement_details["regions"],
        "top_blocks": agreement_details["top_blocks"],
    }

    # ----- Score ---------------------------------------------------
    largest_region_blocks = max(
        [region["blocks"] for region in ela_details["regions"]] +
        [region["blocks"] for region in noise_details["regions"]] +
        [0]
    )
    localization = {
        "largest_region_blocks": largest_region_blocks,
        "reference_blocks": max(10, round(0.04 * ela_details["block_count"])),
        "block_size": block,
        "method": "a connected anomaly region is significant when it covers "
                  "about 4% of the image blocks",
    }
    score = tamper_suspicion_score(ela_stats, noise_stats, localization, metadata)

    # ----- Artefacts ----------------------------------------------
    original_view = analysis_rgb.copy()
    original_view.thumbnail((900, 900), LANCZOS)
    original_view.save(output_dir / "original_view.jpg", quality=88)

    colorize_heatmap(ela_amplified).save(output_dir / "ela_heatmap.png")
    create_overlay(analysis_rgb, ela_blocks, block).save(output_dir / "ela_overlay.jpg", quality=90)

    noise_view = laplacian.copy()
    noise_view = ImageOps.autocontrast(noise_view, cutoff=1)
    colorize_heatmap(noise_view).save(output_dir / "noise_heatmap.png")
    create_overlay(analysis_rgb, noise_blocks, block).save(output_dir / "noise_overlay.jpg", quality=90)

    # draw every agreement block (not only the top ten)
    create_overlay(analysis_rgb, agreement_details["blocks"], block).save(
        output_dir / "agreement_overlay.jpg", quality=90)

    artifacts = {
        "directory": str(output_dir.resolve()),
        "original_view": "original_view.jpg",
        "ela_heatmap": "ela_heatmap.png",
        "ela_overlay": "ela_overlay.jpg",
        "noise_heatmap": "noise_heatmap.png",
        "noise_overlay": "noise_overlay.jpg",
        "agreement_overlay": "agreement_overlay.jpg",
        "report_json": "report.json",
        "report_html": "report.html",
    }

    notes = []
    if preview_note:
        notes.append(preview_note)
    if file_info["format"].upper() != "JPEG":
        notes.append("the source is not a JPEG; ELA interpretation is weaker for "
                     "PNG/BMP/TIFF sources because they are not block-compressed")
    notes.append("ELA and noise maps are heuristic indicators - they show where an "
                 "edit probably happened, not proof that the image is fake.")

    return {
        "tool": {"name": APP_NAME, "version": VERSION},
        "analysed_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.time() - start_time, 2),
        "parameters": {
            "ela_quality": quality,
            "ela_scale": scale,
            "block_size": block,
            "z_threshold": z_threshold,
            "max_side": max_side,
        },
        "file": file_info,
        "preview": {
            "width": width,
            "height": height,
            "scale": round(preview_factor, 4),
            "note": preview_note,
        },
        "metadata": metadata,
        "ela": ela_stats,
        "noise": noise_stats,
        "agreement": agreement_stats,
        "localization": localization,
        "perceptual_hash": {
            "algorithm": "dHash 8x8 (64 bit)",
            "dhash": hash_hex(perceptual_hash),
        },
        "tamper_score": score,
        "artifacts": artifacts,
        "comparison": None,
        "notes": notes,
    }


# ----------------------------------------------------------------------
#  Compare two images (perceptual hash)
# ----------------------------------------------------------------------

def compare_images(first_path, second_path) -> dict:
    first = Path(first_path).expanduser()
    second = Path(second_path).expanduser()
    if not first.is_file():
        raise FileNotFoundError(f"image not found: {first}")
    if not second.is_file():
        raise FileNotFoundError(f"image not found: {second}")

    with Image.open(first) as handle:
        first_rgb = handle.convert("RGB")
        first_size = handle.size
        first_format = handle.format
    with Image.open(second) as handle:
        second_rgb = handle.convert("RGB")
        second_size = handle.size
        second_format = handle.format

    hash_first = dhash(first_rgb)
    hash_second = dhash(second_rgb)
    distance = hamming_distance(hash_first, hash_second)
    similarity = round(100 * (1 - distance / 64), 2)

    if sha256_file(first) == sha256_file(second):
        verdict = "IDENTICAL FILE (same SHA-256)"
    elif similarity >= 95:
        verdict = "VERY LIKELY THE SAME IMAGE (re-saved or resized)"
    elif similarity >= 85:
        verdict = "SIMILAR IMAGE (possible edit, crop or compression)"
    else:
        verdict = "DIFFERENT IMAGES"

    return {
        "first": str(first.resolve()),
        "second": str(second.resolve()),
        "first_size": list(first_size),
        "second_size": list(second_size),
        "first_format": first_format,
        "second_format": second_format,
        "same_sha256": sha256_file(first) == sha256_file(second),
        "dhash_first": hash_hex(hash_first),
        "dhash_second": hash_hex(hash_second),
        "hamming_distance": distance,
        "similarity_percent": similarity,
        "verdict": verdict,
    }


# ----------------------------------------------------------------------
#  Reports (console, JSON, HTML)
# ----------------------------------------------------------------------

def _metadata_line(value) -> str:
    return value if value not in (None, "", "0") else "(not present)"


def print_console(result: dict) -> None:
    file_info = result["file"]
    metadata = result["metadata"]
    ela = result["ela"]
    noise = result["noise"]
    agreement = result["agreement"]
    score = result["tamper_score"]

    print()
    print("=" * 70)
    print(f"  {result['tool']['name']}  v{result['tool']['version']}")
    print("=" * 70)
    print(f"  Evidence file : {file_info['name']}")
    print(f"  Analysed at   : {result['analysed_at']}")
    print(f"  SHA-256       : {file_info['sha256']}")
    print(f"  MD5           : {file_info['md5']}")
    print(f"  Size          : {file_info['size_human']} ({file_info['size_bytes']} bytes)")
    print(f"  Format        : {file_info['format']}  {file_info['mode']}  "
          f"{file_info['width']}x{file_info['height']}  ({file_info['megapixels']} MP)")
    print(f"  Byte entropy  : {file_info['byte_entropy_bits']} bits/byte")

    print()
    print("-- Metadata ------------------------------------------------------")
    print(f"  Camera        : {_metadata_line(metadata['make'])} "
          f"{'' if metadata['model'] in (None, '', '0') else metadata['model']}")
    print(f"  Software      : {_metadata_line(metadata['software'])}")
    print(f"  Date/Time     : {_metadata_line(metadata['datetime'])}")
    print(f"  Original time : {_metadata_line(metadata['datetime_original'])}")
    print(f"  GPS           : {metadata['gps_text'] or '(not present)'}")
    print(f"  EXIF present  : {'yes' if metadata['has_exif'] else 'no'}")
    if metadata["flags"]:
        print("  Findings      :")
        for flag in metadata["flags"]:
            print(f"    [!] {flag['code']}: {flag['detail']}")
    else:
        print("  Findings      : none")

    print()
    print("-- Error Level Analysis (ELA) ------------------------------------")
    print("  Formula       : E(x,y) = | I(x,y) - JPEG_q(I(x,y))(x,y) | * s")
    print(f"  Quality       : {ela['quality']}    Amplification: {ela['scale']}x")
    print(f"  Mean residual : {ela['mean_residual']}    "
          f"Std: {ela['std_residual']}    Max: {ela['max_residual']}")
    print(f"  95th pct      : {ela['p95_residual']}    "
          f"Hot pixels: {ela['hot_percent']}% (above mean + 3*std)")
    print(f"  Flagged blocks: {ela['flag_count']} / {ela['block_count']} "
          f"({ela['anomaly_percent']}%)    Regions: {len(ela['regions'])}")

    print()
    print("-- Noise Inconsistency -------------------------------------------")
    print("  Formula       : Var(B) of Laplacian L = I(x-1,y)+I(x+1,y)+I(x,y-1)+I(x,y+1)-4I(x,y)")
    print(f"  Robust test   : |0.6745 * (Var(B) - median) / MAD| > "
          f"{result['parameters']['z_threshold']}")
    print(f"  Flagged blocks: {noise['flag_count']} / {noise['block_count']} "
          f"({noise['anomaly_percent']}%)    Regions: {len(noise['regions'])}")

    print()
    print("-- Agreement map (ELA AND Noise) ---------------------------------")
    print("  Rule          : block is strongly suspicious if BOTH tests flag it")
    print(f"  Flagged blocks: {agreement['flag_count']} / {agreement['block_count']} "
          f"({agreement['anomaly_percent']}%)    Regions: {len(agreement['regions'])}")
    if agreement["regions"]:
        largest = agreement["regions"][0]
        print(f"  Largest region: x={largest['x0']}-{largest['x1']}  "
              f"y={largest['y0']}-{largest['y1']}  blocks={largest['blocks']}")

    if agreement["regions"] or ela["regions"] or noise["regions"]:
        print()
        print("-- Suspected regions (top 5) -------------------------------------")
        regions = [("Agree", region) for region in agreement["regions"]] + \
                  [("ELA", region) for region in ela["regions"]] + \
                  [("Noise", region) for region in noise["regions"]]
        for kind, region in regions[:5]:
            print(f"  {kind:5s}  x={region['x0']}-{region['x1']}  "
                  f"y={region['y0']}-{region['y1']}  "
                  f"blocks={region['blocks']}  area={region['area_px']} px")

    print()
    print("-- Tamper suspicion (heuristic) ----------------------------------")
    print(f"  Score         : {score['score']} / 100   [{score['level']}]")
    print(f"  Components    : ELA={score['components']['ela']}  "
          f"Noise={score['components']['noise']}  "
          f"Loc={score['components']['localisation']}  "
          f"Metadata={score['components']['metadata']}")
    print("  Weights       : 0.25*ELA + 0.25*Noise + 0.30*Localisation + 0.20*Metadata")
    print(f"  dHash         : {result['perceptual_hash']['dhash']}")

    comparison = result.get("comparison")
    if comparison:
        print()
        print("-- Comparison with another image ----------------------------------")
        print(f"  Other file    : {comparison['second']}")
        print(f"  Same SHA-256  : {'yes' if comparison['same_sha256'] else 'no'}")
        print(f"  dHash distance: {comparison['hamming_distance']} / 64 bits")
        print(f"  Similarity    : {comparison['similarity_percent']}%")
        print(f"  Verdict       : {comparison['verdict']}")

    print()
    print("-- Outputs -------------------------------------------------------")
    artifacts = result["artifacts"]
    directory = Path(artifacts["directory"])
    print(f"  Directory     : {directory}")
    for key in ("report_html", "report_json", "original_view",
                "ela_heatmap", "ela_overlay", "noise_heatmap", "noise_overlay",
                "agreement_overlay"):
        print(f"  {key:14s}: {artifacts[key]}")

    for note in result["notes"]:
        print()
        print(f"  Note: {note}")
    print()


def write_json_report(result: dict) -> Path:
    directory = Path(result["artifacts"]["directory"])
    path = directory / result["artifacts"]["report_json"]
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return path


def _html_table(rows) -> str:
    body = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in rows
    )
    return f'<table class="kv">{body}</table>'


def _html_image(path: Path, alt: str) -> str:
    try:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return f'<p class="missing">image missing: {html.escape(path.name)}</p>'
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return (f'<img src="data:{mime};base64,{payload}" alt="{html.escape(alt)}" '
            f'loading="lazy">')


def write_html_report(result: dict) -> Path:
    artifacts = result["artifacts"]
    directory = Path(artifacts["directory"])
    file_info = result["file"]
    metadata = result["metadata"]
    ela = result["ela"]
    noise = result["noise"]
    agreement = result["agreement"]
    score = result["tamper_score"]

    level_class = score["level"].lower()

    flag_rows = "".join(
        f"<li><b>{html.escape(flag['code'])}</b> &mdash; {html.escape(flag['detail'])}</li>"
        for flag in metadata["flags"]
    ) or "<li>No metadata anomalies found.</li>"

    region_rows = []
    for kind, regions in (("Agreement", agreement["regions"]),
                          ("ELA", ela["regions"]),
                          ("Noise", noise["regions"])):
        for region in regions[:10]:
            region_rows.append(
                f"<tr><td>{kind}</td><td>{region['x0']} &ndash; {region['x1']}</td>"
                f"<td>{region['y0']} &ndash; {region['y1']}</td>"
                f"<td>{region['blocks']}</td><td>{region['area_px']}</td></tr>"
            )
    if not region_rows:
        region_rows.append('<tr><td colspan="5">No connected anomaly regions.</td></tr>')

    comparison_html = ""
    comparison = result.get("comparison")
    if comparison:
        comparison_html = f"""
        <h2>7. Comparison</h2>
        {_html_table([
            ("Other file", comparison["second"]),
            ("Same SHA-256", "yes" if comparison["same_sha256"] else "no"),
            ("dHash distance", f"{comparison['hamming_distance']} / 64 bits"),
            ("Similarity", f"{comparison['similarity_percent']}%"),
            ("Verdict", comparison["verdict"]),
        ])}
        """

    html_text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Image Forensics Report - {html.escape(file_info['name'])}</title>
<style>
  body {{ font-family: system-ui, "Segoe UI", sans-serif; margin: 0; background: #11151c; color: #e8edf5; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 60px; }}
  h1 {{ margin-bottom: 4px; }}
  h2 {{ margin-top: 34px; border-bottom: 1px solid #2b3648; padding-bottom: 6px; }}
  .sub {{ color: #9fb0c7; }}
  .banner {{ padding: 14px 18px; border-radius: 10px; font-size: 1.15rem; font-weight: 700; margin: 18px 0; }}
  .banner.low {{ background: #123524; color: #7ff0a8; }}
  .banner.medium {{ background: #3a2c10; color: #ffd166; }}
  .banner.high {{ background: #3d1418; color: #ff7b7b; }}
  table.kv {{ border-collapse: collapse; width: 100%; }}
  table.kv th {{ text-align: left; width: 240px; color: #9fb0c7; font-weight: 600; }}
  table.kv th, table.kv td {{ border-bottom: 1px solid #232d3d; padding: 7px 6px; vertical-align: top; }}
  table.data {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
  table.data th, table.data td {{ border: 1px solid #2b3648; padding: 6px 8px; text-align: left; }}
  .formula {{ background: #0b0f15; border-left: 3px solid #4f8cff; padding: 12px 14px;
              font-family: ui-monospace, monospace; white-space: pre-wrap; margin: 10px 0 16px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  .card {{ background: #161c26; border: 1px solid #263043; border-radius: 10px; padding: 12px; }}
  .card h3 {{ margin: 0 0 8px; font-size: 1rem; color: #c8d6ea; }}
  img {{ max-width: 100%; border-radius: 6px; display: block; }}
  ul {{ line-height: 1.6; }}
  .small {{ color: #8fa1b8; font-size: .88rem; }}
  @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<main>
  <h1>Digital Image Forensics Report</h1>
  <p class="sub">{html.escape(result['tool']['name'])} v{result['tool']['version']}
     &middot; analysed {html.escape(result['analysed_at'])}
     &middot; took {result['elapsed_seconds']} s</p>

  <div class="banner {level_class}">
    Tamper suspicion score: {score['score']} / 100 &mdash; {score['level']}
  </div>

  <h2>1. Evidence file &amp; chain of custody</h2>
  {_html_table([
      ("File name", file_info["name"]),
      ("Full path", file_info["path"]),
      ("SHA-256", file_info["sha256"]),
      ("MD5", file_info["md5"]),
      ("Size", f"{file_info['size_human']} ({file_info['size_bytes']} bytes)"),
      ("Format / mode", f"{file_info['format']} / {file_info['mode']}"),
      ("Dimensions", f"{file_info['width']} x {file_info['height']} ({file_info['megapixels']} MP)"),
      ("Frames", file_info["frames"]),
      ("Byte entropy", f"{file_info['byte_entropy_bits']} bits/byte"),
  ])}

  <h2>2. Metadata analysis</h2>
  {_html_table([
      ("Camera make", metadata["make"] or "(not present)"),
      ("Camera model", metadata["model"] or "(not present)"),
      ("Software", metadata["software"] or "(not present)"),
      ("Date/Time", metadata["datetime"] or "(not present)"),
      ("DateTimeOriginal", metadata["datetime_original"] or "(not present)"),
      ("GPS", metadata["gps_text"] or "(not present)"),
      ("EXIF present", "yes" if metadata["has_exif"] else "no"),
      ("Editor signatures", ", ".join(metadata["editing_signatures"]) or "(none)"),
  ])}
  <h3>Findings</h3>
  <ul>{flag_rows}</ul>

  <h2>3. Error Level Analysis (ELA)</h2>
  <div class="formula">I_q(x,y) = JPEG( I(x,y), q = {ela['quality']} )
E(x,y)   = | I(x,y) - I_q(x,y) | * s,  s = {ela['scale']}
A block B is flagged when |0.6745 * (mean_E(B) - median) / MAD| &gt; {result['parameters']['z_threshold']}</div>
  {_html_table([
      ("Mean residual", ela["mean_residual"]),
      ("Std residual", ela["std_residual"]),
      ("Max residual", ela["max_residual"]),
      ("95th percentile", ela["p95_residual"]),
      ("Hot pixels", f"{ela['hot_percent']}% (above mean + 3*std)"),
      ("Flagged blocks", f"{ela['flag_count']} / {ela['block_count']} ({ela['anomaly_percent']}%)"),
      ("Connected regions", len(ela["regions"])),
  ])}
  <div class="grid">
    <div class="card"><h3>Amplified ELA heatmap</h3>{_html_image(directory / artifacts['ela_heatmap'], 'ELA heatmap')}</div>
    <div class="card"><h3>Flagged ELA blocks</h3>{_html_image(directory / artifacts['ela_overlay'], 'ELA overlay')}</div>
  </div>

  <h2>4. Noise inconsistency (Laplacian variance)</h2>
  <div class="formula">L(x,y) = I(x-1,y) + I(x+1,y) + I(x,y-1) + I(x,y+1) - 4*I(x,y)
Var(B) = (1/n) * sum_{{ (x,y) in B }} ( L(x,y) - mean_B )^2
z(B)   = 0.6745 * ( Var(B) - median(Var) ) / MAD</div>
  {_html_table([
      ("Flagged blocks", f"{noise['flag_count']} / {noise['block_count']} ({noise['anomaly_percent']}%)"),
      ("Median block variance", noise["median_block_variance"]),
      ("MAD", noise["mad_block_variance"]),
      ("Connected regions", len(noise["regions"])),
  ])}
  <div class="grid">
    <div class="card"><h3>Laplacian noise heatmap</h3>{_html_image(directory / artifacts['noise_heatmap'], 'Noise heatmap')}</div>
    <div class="card"><h3>Flagged noise blocks</h3>{_html_image(directory / artifacts['noise_overlay'], 'Noise overlay')}</div>
  </div>

  <h2>5. Agreement map (ELA AND Noise)</h2>
  <div class="formula">ELA_flag(B)  = |0.6745 * (mean_E(B) - median) / MAD| &gt; {result['parameters']['z_threshold']}
Noise_flag(B)= |0.6745 * (Var(B)   - median) / MAD| &gt; {result['parameters']['z_threshold']}
A(B)         = ELA_flag(B) AND Noise_flag(B)</div>
  {_html_table([
      ("Flagged blocks", f"{agreement['flag_count']} / {agreement['block_count']} ({agreement['anomaly_percent']}%)"),
      ("Connected regions", len(agreement["regions"])),
      ("Largest region", (f"x={agreement['regions'][0]['x0']}-{agreement['regions'][0]['x1']}, "
                          f"y={agreement['regions'][0]['y0']}-{agreement['regions'][0]['y1']}, "
                          f"{agreement['regions'][0]['blocks']} blocks")
                         if agreement["regions"] else "(none)"),
  ])}
  <div class="card"><h3>Blocks flagged by both tests (strongest evidence)</h3>
    {_html_image(directory / artifacts['agreement_overlay'], 'Agreement overlay')}</div>

  <h2>6. Suspicion score and suspected regions</h2>
  {_html_table([
      ("Score", f"{score['score']} / 100 ({score['level']})"),
      ("ELA component", score["components"]["ela"]),
      ("Noise component", score["components"]["noise"]),
      ("Localisation component", score["components"]["localisation"]),
      ("Metadata component", score["components"]["metadata"]),
      ("Formula", "100 * (0.25*ELA + 0.25*Noise + 0.30*Localisation + 0.20*Metadata)"),
  ])}
  <table class="data">
    <tr><th>Map</th><th>x range</th><th>y range</th><th>Blocks</th><th>Area (px)</th></tr>
    {''.join(region_rows)}
  </table>
  {comparison_html}

  <h2>Notes and limitations</h2>
  <ul>
    {''.join(f"<li>{html.escape(note)}</li>" for note in result['notes'])}
    <li>ELA and noise analysis are heuristic. A high score means the image
        deserves a closer look, not that it is definitely forged.</li>
    <li>Always preserve the original file and record its SHA-256 hash before
        analysis (chain of custody).</li>
  </ul>
</main>
</body>
</html>
"""
    path = directory / artifacts["report_html"]
    path.write_text(html_text, encoding="utf-8")
    return path


def write_reports(result: dict) -> tuple:
    json_path = write_json_report(result)
    html_path = write_html_report(result)
    return json_path, html_path


# ----------------------------------------------------------------------
#  Demo / self-test
# ----------------------------------------------------------------------

def _boxes_overlap(first, second) -> bool:
    return not (first[2] < second[0] or second[2] < first[0] or
                first[3] < second[1] or second[3] < first[1])


def run_demo(args) -> int:
    try:
        import make_samples
    except ImportError as exc:
        print("Demo needs make_samples.py in the same folder:", exc)
        return 1

    sample_dir = Path(args.sample_dir).expanduser() if args.sample_dir else SAMPLE_DIR
    print("=" * 70)
    print("  DEMO / SELF-TEST : Digital Image Forensics Tool")
    print("=" * 70)
    print(f"  [1/5] Generating sample evidence images in: {sample_dir}")
    samples = make_samples.generate_samples(sample_dir, force=True, verbose=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_output = DEFAULT_OUTPUT_DIR / f"demo_{stamp}"

    print("  [2/5] Analysing original.jpg ...")
    original = analyze(samples["original"], output_dir=demo_output / "original",
                       quality=args.quality, scale=args.scale, block=args.block,
                       z_threshold=args.z)
    print(f"        risk = {original['tamper_score']['score']}/100 "
          f"({original['tamper_score']['level']}), "
          f"metadata flags = {len(original['metadata']['flags'])}")

    print("  [3/5] Analysing tampered.jpg ...")
    tampered = analyze(samples["tampered"], output_dir=demo_output / "tampered",
                       quality=args.quality, scale=args.scale, block=args.block,
                       z_threshold=args.z)
    print(f"        risk = {tampered['tamper_score']['score']}/100 "
          f"({tampered['tamper_score']['level']}), "
          f"metadata flags = {len(tampered['metadata']['flags'])}")

    print("  [4/5] Comparing original.jpg with copy_resized.jpg ...")
    comparison = compare_images(samples["original"], samples["copy_resized"])
    print(f"        dHash distance = {comparison['hamming_distance']}/64, "
          f"similarity = {comparison['similarity_percent']}%")
    print(f"        verdict = {comparison['verdict']}")

    print("  [5/5] Checking that the tampered region was localised ...")
    ground_truth = make_samples.TAMPER_BOX
    preview_scale = tampered["preview"]["scale"]
    scaled_box = tuple(round(value * preview_scale) for value in ground_truth)
    regions = tampered["noise"]["regions"] + tampered["ela"]["regions"]
    localised = any(
        region["blocks"] >= 8 and _boxes_overlap(
            (region["x0"], region["y0"], region["x1"], region["y1"]),
            scaled_box,
        )
        for region in regions
    )

    checks = [
        ("Exact hashes differ between original and tampered",
         original["file"]["sha256"] != tampered["file"]["sha256"]),
        ("Metadata flags appear on tampered copy",
         len(tampered["metadata"]["flags"]) >= 2),
        ("Tampered copy has a higher risk score",
         tampered["tamper_score"]["score"] > original["tamper_score"]["score"]),
        ("Re-saved copy still matches the original (dHash >= 85%)",
         comparison["similarity_percent"] >= 85.0),
        ("Tampered region localised by ELA/noise region analysis", localised),
    ]

    print()
    print("-" * 70)
    print("  SELF-TEST RESULT")
    print("-" * 70)
    passed = 0
    for label, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        passed += 1 if ok else 0

    # reports for both analysed images
    original["comparison"] = comparison
    write_reports(original)
    write_reports(tampered)

    print()
    print(f"  Checks passed : {passed} / {len(checks)}")
    print(f"  Reports       : {demo_output}")
    print(f"                  - original/report.html")
    print(f"                  - tampered/report.html")
    print()
    return 0 if passed == len(checks) else 1


# ----------------------------------------------------------------------
#  Command line
# ----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_forensics.py",
        description="Digital image forensics tool: hashes, EXIF/GPS metadata, "
                    "Error Level Analysis, noise inconsistency, dHash comparison.",
        epilog="Example: python3 image_forensics.py photos/suspect.jpg --compare photos/original.jpg",
    )
    parser.add_argument("image", nargs="?", help="image file to analyse")
    parser.add_argument("-o", "--output", help="output directory (default: output/<name>_forensics_<time>)")
    parser.add_argument("-q", "--quality", type=int, default=DEFAULT_ELA_QUALITY,
                        help=f"JPEG quality for ELA re-compression (default: {DEFAULT_ELA_QUALITY})")
    parser.add_argument("-s", "--scale", type=int, default=DEFAULT_ELA_SCALE,
                        help=f"ELA amplification factor (default: {DEFAULT_ELA_SCALE})")
    parser.add_argument("-b", "--block", type=int, default=DEFAULT_BLOCK,
                        help=f"block size in pixels for anomaly maps (default: {DEFAULT_BLOCK})")
    parser.add_argument("-z", "--z-threshold", type=float, default=DEFAULT_Z,
                        dest="z", help=f"robust z-score threshold for flagging blocks (default: {DEFAULT_Z})")
    parser.add_argument("--max-side", type=int, default=DEFAULT_MAX_SIDE,
                        help=f"downscale analysis above this side length (default: {DEFAULT_MAX_SIDE})")
    parser.add_argument("--compare", metavar="IMAGE2",
                        help="compare the analysed image with a second image (dHash)")
    parser.add_argument("--demo", action="store_true",
                        help="generate sample images and run a self-test demo")
    parser.add_argument("--sample-dir", help="where --demo should create sample images")
    parser.add_argument("--json", action="store_true", help="also print the full report as JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.demo:
        return run_demo(args)

    if args.image is None:
        default_sample = SAMPLE_DIR / "tampered.jpg"
        if default_sample.exists():
            args.image = str(default_sample)
            print(f"No image given, using the sample: {default_sample}")
        else:
            parser.print_help()
            print()
            print("Tip: run 'python3 image_forensics.py --demo' to create and test sample images.")
            return 1

    try:
        result = analyze(args.image, output_dir=args.output, quality=args.quality,
                         scale=args.scale, block=args.block, z_threshold=args.z,
                         max_side=args.max_side)
    except Exception as exc:
        print(f"Could not analyse the image: {exc}")
        return 1

    if args.compare:
        try:
            result["comparison"] = compare_images(args.image, args.compare)
        except Exception as exc:
            print(f"Comparison failed: {exc}")

    write_reports(result)
    print_console(result)

    if args.json:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
