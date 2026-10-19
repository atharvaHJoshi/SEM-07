# Mini Project : Digital Image Forensics Tool

**Subject:** Cyber Security and Digital Forensics (CSDF) — Mini Project

A command-line tool that examines a suspect image the way a digital forensics
examiner would: it records the chain of custody (hashes), reads the hidden
EXIF/GPS metadata, finds the parts of the picture whose **compression error**
or **local noise** does not match the rest of the image, compares images with a
perceptual hash, and writes a complete HTML + JSON report.

## Aim

Design and develop a tool for the digital forensics of images that can:

1. prove that the evidence file was not changed (cryptographic hashes),
2. recover hidden metadata (camera, software, timestamps, GPS),
3. detect and localise regions that were spliced, cloned or retouched, and
4. compare a suspect image with a known original.

## Mathematical formula used for the actual operation

The main operation of the tool is **Error Level Analysis (ELA)**. An image is
saved again as a JPEG at quality `q` and the difference between the original
pixels and the re-compressed pixels is the *error level*:

```
I_q(x, y) = JPEG( I(x, y), quality = q )          re-compressed image

E(x, y)   = | I(x, y) - I_q(x, y) | * s           error level at pixel (x, y)
```

`E` is computed for every pixel and amplified by `s` so that human eyes can see
it. A JPEG that was saved exactly once has a small, uniform `E`. A region that
was pasted, cloned or saved with a different quality has a different compression
history, so its `E` is clearly different from its neighbours.

The tool then tests every 16×16 block `B` with a **robust z-score**:

```
z_E(B) = 0.6745 * ( mean(E over B) - median(mean(E)) ) / MAD(mean(E))
```

where `MAD` is the median absolute deviation. `|z_E(B)| > threshold` means the
block is an anomaly.

To reduce false alarms, two independent tests are combined:

**1. Error Level Analysis (compression)** — given above.

**2. Noise inconsistency (Laplacian variance)**

```
L(x, y)  = I(x-1,y) + I(x+1,y) + I(x,y-1) + I(x,y+1) - 4*I(x, y)
Var(B)   = (1/n) * Σ over (x,y) in B of ( L(x,y) - mean_B )²
z_N(B)   = 0.6745 * ( Var(B) - median(Var) ) / MAD(Var)
```

A blurred/cloned region has less noise and a noisy spliced region has more
noise than the rest of the photo, so its `z_N` becomes large.

**3. Perceptual hash (dHash) for comparing images**

```
H(i, j) = 1  if  I(i, j) < I(i, j+1)  else  0
distance(H1, H2) = Σ ( H1(k) XOR H2(k) )
```

A distance of 0 means the two images are visually identical; small distances
mean the same picture was re-saved or resized.

**4. Final suspicion score**

```
S = 100 * ( 0.25*ELA + 0.25*Noise + 0.30*Localisation + 0.20*Metadata )
```

Each component is first normalised to the range 0…1. `Localisation` uses the
largest connected anomaly region (a real edit usually forms one compact region,
while random edge artefacts are scattered).

| Score    | Level  | Meaning |
|----------|--------|---------|
| 0 – 30   | LOW    | no strong forensic indicator |
| 31 – 60  | MEDIUM | some anomalies, closer inspection recommended |
| 61 – 100 | HIGH   | strong indicators of manipulation |

## Features

- **Chain of custody** — SHA-256 and MD5, size, format, dimensions, frames and
  Shannon byte entropy (`H = -Σ p·log₂p`) for every analysed file.
- **Metadata forensics** — EXIF camera make/model, software, timestamps, GPS
  latitude/longitude, plus a raw-byte scan for editor signatures hidden inside
  the file (Photoshop, GIMP, Lightroom, Snapseed, Canva, …).
- **Error Level Analysis** with an amplified heatmap and flagged-block overlay.
- **Noise inconsistency analysis** using the Laplacian variance per block.
- **Agreement map** — blocks flagged by *both* tests are highlighted as the
  strongest evidence.
- **Connected-region grouping** — nearby flagged blocks are merged into
  bounding boxes instead of showing isolated pixels.
- **dHash comparison** (`--compare`) to find re-saved or resized copies of an
  image even when hashes differ.
- **Reports** — a colour console report, a self-contained `report.html` with
  embedded images, and a machine-readable `report.json`.
- **Self-test demo** — `--demo` generates synthetic evidence images, analyses
  them and checks that the tool finds the known manipulated region.
- The original evidence file is **never modified**.

## Files

| File | Purpose |
|------|---------|
| `image_forensics.py` | the full tool: hashes, metadata, ELA, noise, dHash, reports, CLI |
| `make_samples.py` | generates the synthetic evidence images and `ground_truth.json` |
| `run_demo.sh` | convenience wrapper that finds a Python with Pillow and runs the demo |
| `requirements.txt` | Python dependency (Pillow) |
| `sample_images/` | ready-made demo images (original / tampered / re-saved copy) |
| `output/` | reports produced by each run (created automatically) |

## Installation

```bash
python3 -m pip install -r requirements.txt      # installs Pillow
```

On Arch Linux the system package can be used instead:
`sudo pacman -S python-pillow`.

## Usage

```bash
# 1. Generate the sample evidence images once
python3 make_samples.py

# 2. Analyse an image
python3 image_forensics.py sample_images/tampered.jpg

# 3. Analyse and compare with a known original
python3 image_forensics.py sample_images/tampered.jpg --compare sample_images/original.jpg

# 4. Full self-test: creates samples, analyses original + tampered, compares
#    the re-saved copy and checks that the tampered region is localised
python3 image_forensics.py --demo

#    Same, but the wrapper finds Python with Pillow (and sets up .venv if needed)
./run_demo.sh

# 5. Print the report as JSON as well
python3 image_forensics.py my_photo.jpg --json
```

| Option | Meaning |
|--------|---------|
| `IMAGE` | image to analyse (default: `sample_images/tampered.jpg` if present) |
| `-o, --output DIR` | output directory (default: `output/<name>_forensics_<time>`) |
| `-q, --quality Q` | JPEG quality for ELA re-compression (default 90) |
| `-s, --scale S` | ELA amplification (default 15) |
| `-b, --block B` | block size in pixels (default 16) |
| `-z, --z-threshold Z` | robust z-score threshold (default 3.5) |
| `--max-side N` | downscale preview for very large images (default 1400) |
| `--compare IMAGE2` | compare with a second image using dHash |
| `--demo` | generate samples and run the self-test |
| `--json` | also print the full report as JSON |
| `--version`, `--help` | version / help |

## Demo / self-test

```bash
python3 image_forensics.py --demo
```

The demo creates three synthetic images (`original.jpg`, `tampered.jpg`,
`copy_resized.jpg`), analyses them and runs five checks:

1. exact SHA-256 of original and tampered file differ,
2. the tampered copy has metadata anomalies (GIMP software, no camera info),
3. the tampered copy gets a higher suspicion score,
4. the re-saved copy is still recognised by dHash (≥ 85 % similarity),
5. the manipulated region is localised as a connected anomaly region.

Expected result:

```
  [PASS] Exact hashes differ between original and tampered
  [PASS] Metadata flags appear on tampered copy
  [PASS] Tampered copy has a higher risk score
  [PASS] Re-saved copy still matches the original (dHash >= 85%)
  [PASS] Tampered region localised by ELA/noise region analysis

  Checks passed : 5 / 5
```

## Sample output (abridged)

```
======================================================================
  CSDF Digital Image Forensics Tool  v1.0
======================================================================
  Evidence file : tampered.jpg
  SHA-256       : 48df93d7703735502395ff1dd90447fd83bea7e777faaa7a40dda2d911d4c609
  MD5           : 5d2bf0addab61d3d40f4cd06a0a25df3
  Size          : 161.5 KB (165348 bytes)
  Format        : JPEG  RGB  900x600  (0.54 MP)

-- Metadata ------------------------------------------------------
  Camera        : (not present)
  Software      : GIMP 2.10.36
  GPS           : (not present)
  Findings      :
    [!] editing-software: editor signature found in file/metadata: gimp
    [!] missing-camera-info: EXIF exists but has no camera Make/Model

-- Error Level Analysis (ELA) ------------------------------------
  E(x,y) = | I(x,y) - JPEG_q(I(x,y))(x,y) | * s
  Flagged blocks: 49 / 2072 (2.365%)    Regions: 12

-- Noise Inconsistency -------------------------------------------
  Flagged blocks: 148 / 2072 (7.143%)    Regions: 29

-- Agreement map (ELA AND Noise) ---------------------------------
  Flagged blocks: 19 / 2072 (0.917%)    Regions: 13

-- Tamper suspicion (heuristic) ----------------------------------
  Score         : 64 / 100   [HIGH]
```

## How it works (summary)

1. The original file is hashed (SHA-256 + MD5) and its basic properties are read.
2. EXIF/GPS tags are decoded and the first 2 MB of the file are scanned for
   editor signatures; camera/software/timestamp anomalies become findings.
3. A preview (max 1400 px) is re-compressed to JPEG at quality `q` and the
   absolute difference is the ELA map (`E`).
4. Every 16×16 block gets its mean `E` and its Laplacian variance; both are
   tested with the robust z-score and flagged when `|z| > threshold`.
5. Adjacent flagged blocks are merged into regions; the largest region feeds
   the localisation part of the score.
6. An 8×8 dHash is computed for fast comparison with other images.
7. Console, HTML and JSON reports are written to the output directory.

## Limitations (important for a forensic report)

- ELA and noise analysis are **heuristic**: they show where an edit *probably*
  happened. They are not proof that an image is forged.
- A high suspicion score is a reason to examine the image more closely, not a
  verdict.
- ELA is weaker for PNG/BMP/TIFF files because they are not JPEG-compressed.
- Social media platforms re-compress images, which can hide or create ELA
  artefacts.
- Always work on a **copy**, keep the original file untouched, and record its
  SHA-256 hash before and after analysis (chain of custody).
- Use this tool together with other evidence; never rely on one test alone.

## Future scope

- Copy–move (clone) detection using block matching / DCT features.
- JPEG ghost analysis (two different re-compression qualities).
- Local (neighbourhood) z-scores instead of one global threshold.
- GUI or web dashboard, batch processing of a folder, PDF report export.
- Support for RAW camera formats and extraction of embedded thumbnails.
