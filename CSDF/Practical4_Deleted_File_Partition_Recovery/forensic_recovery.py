"""
Practical 4 : Recover permanently deleted files and deleted partitions
Aim         : Write a computer forensic application that recovers deleted
              files from a disk image and reconstructs a deleted partition.

How it works:
  1. A realistic FAT16 disk image (disk_image.dd) is generated the first
     time the program runs.  It contains two FAT16 partitions; the second
     partition's MBR entry has been erased to simulate a deleted partition.
  2. Partition recovery scans every sector for a FAT boot sector signature
     (0x55AA + a valid BIOS Parameter Block) and rebuilds the missing MBR
     entry.
  3. Deleted files are found from FAT directory entries whose first byte is
     0xE5.  Their cluster chains were cleared on deletion, so the data is
     read contiguously from the recorded start cluster.
  4. Files whose directory entry was also destroyed are recovered by file
     carving - scanning the raw image for JPEG / PNG / PDF signatures.
  5. Every recovered file is written to recovered/ and hashed with SHA-256.

The tool always works on a copy of the evidence.  The disk image is only
modified when it is created or explicitly rebuilt with --rebuild.

Usage:
    python3 forensic_recovery.py            # create image if needed, recover
    python3 forensic_recovery.py --rebuild  # regenerate the demo disk image
    python3 forensic_recovery.py --image other.dd
"""

import argparse
import hashlib
import json
import struct
from pathlib import Path

SECTOR = 512
HERE = Path(__file__).parent
IMAGE_FILE = HERE / "disk_image.dd"
RECOVERED_DIR = HERE / "recovered"
REPORT_FILE = HERE / "recovery_report.json"

# ---------------------------------------------------------------- disk layout
DISK_SECTORS = 18_432                 # 9 MiB evidence disk
PARTITION_START = 2_048               # LBA of partition 1
PARTITION_SECTORS = 8_192             # 4 MiB per partition
SECOND_PARTITION_START = PARTITION_START + PARTITION_SECTORS

FAT_RESERVED = 1                      # boot sector
FAT_COUNT = 2
FAT_SECTORS = 32
ROOT_ENTRIES = 64
ROOT_SECTORS = ROOT_ENTRIES * 32 // SECTOR
ROOT_START = FAT_RESERVED + FAT_COUNT * FAT_SECTORS          # sector 65
DATA_START = ROOT_START + ROOT_SECTORS                       # sector 69
CLUSTER_SIZE = SECTOR                                        # 1 sector/cluster

FAT16_EOC = 0xFFF8                    # first "end of chain" value
DELETED_MARKER = 0xE5                 # FAT uses 0xE5 for a deleted entry


# =====================================================================
# 1. Building the demonstration evidence disk image
# =====================================================================

def _jpeg(tag, target_size):
    """Return bytes that start with a JPEG SOI and end with an EOI marker."""
    header = (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01"
              b"\x00\x01\x00\x00")
    text = f"JPEG evidence {tag} - camera DSC-9000 - photo of the exhibit. ".encode()
    filler = (text * (target_size // len(text) + 1))[:target_size - len(header) - 4]
    return header + filler + b"\xff\xd9"


def _pdf(tag, target_size):
    """Return bytes that start with %PDF- and end with %%EOF."""
    text = f"Digital evidence archive {tag} - confidential case notes. ".encode()
    body = (b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    filler = (text * (target_size // len(text) + 1))[:target_size - len(body) - 6]
    return body + filler + b"\n%%EOF\n"


def _text(tag):
    return (f"Recovered case note {tag}.\n"
            "Owner: Example Forensic Lab\n"
            "This text survived deletion because its clusters were not reused.\n"
            "SHA-256 of every recovered file is recorded in the report.\n"
            ).encode()


def _dir_entry(name, start_cluster, size, deleted=False):
    """Build one 32-byte FAT16 8.3 directory entry."""
    base, _, extension = name.partition(".")
    entry = bytearray(32)
    entry[0:8] = base[:8].ljust(8).encode("ascii")
    entry[8:11] = extension[:3].ljust(3).encode("ascii")
    entry[11] = 0x20                                    # archive attribute
    struct.pack_into("<H", entry, 26, start_cluster)    # first cluster
    struct.pack_into("<I", entry, 28, size)             # file size
    if deleted:
        entry[0] = DELETED_MARKER                       # 0xE5 overwrites the name
    return bytes(entry)


def _label_entry(label):
    entry = bytearray(32)
    entry[0:11] = label.upper().encode("ascii").ljust(11)[:11]
    entry[11] = 0x08                                    # volume label
    return bytes(entry)


def _boot_sector(label, total_sectors, hidden_sectors):
    boot = bytearray(SECTOR)
    boot[0:3] = b"\xeb\x3c\x90"                         # jump to boot code
    boot[3:11] = b"MSWIN4.1"                            # OEM name
    struct.pack_into("<H", boot, 11, SECTOR)
    boot[13] = 1                                        # sectors per cluster
    struct.pack_into("<H", boot, 14, FAT_RESERVED)
    boot[16] = FAT_COUNT
    struct.pack_into("<H", boot, 17, ROOT_ENTRIES)
    struct.pack_into("<H", boot, 19, total_sectors)     # 16-bit sector count
    boot[21] = 0xF8                                     # fixed disk
    struct.pack_into("<H", boot, 22, FAT_SECTORS)
    struct.pack_into("<H", boot, 24, 63)                # sectors per track
    struct.pack_into("<H", boot, 26, 255)               # heads
    struct.pack_into("<I", boot, 28, hidden_sectors)
    struct.pack_into("<I", boot, 32, total_sectors)
    boot[36] = 0x80                                     # hard disk
    boot[38] = 0x29                                     # extended boot signature
    struct.pack_into("<I", boot, 39, 0x20260814)        # volume serial number
    boot[43:54] = label.upper().encode("ascii").ljust(11)[:11]
    boot[54:62] = b"FAT16   "
    boot[510:512] = b"\x55\xaa"
    return bytes(boot)


def build_fat16_partition(label, files, orphan=None, hidden_sectors=0):
    """Create one FAT16 partition.

    files  : list of dicts {name, data, deleted, wipe}
    orphan : bytes of a file whose directory entry was destroyed
    """
    volume = bytearray(PARTITION_SECTORS * SECTOR)
    fat = [0] * (FAT_SECTORS * SECTOR // 2)
    fat[0] = 0xFFF8
    fat[1] = 0xFFFF
    next_cluster = 2

    def allocate(data):
        nonlocal next_cluster
        clusters = max(1, (len(data) + CLUSTER_SIZE - 1) // CLUSTER_SIZE)
        start = next_cluster
        for index in range(clusters):
            cluster = start + index
            offset = DATA_START * SECTOR + (cluster - 2) * CLUSTER_SIZE
            chunk = data[index * CLUSTER_SIZE:(index + 1) * CLUSTER_SIZE]
            volume[offset:offset + len(chunk)] = chunk
            fat[cluster] = cluster + 1 if index < clusters - 1 else 0xFFFF
        next_cluster = start + clusters
        return start, clusters

    entries = [_label_entry(label)]
    for spec in files:
        start, clusters = allocate(spec["data"])
        entries.append(_dir_entry(spec["name"], start, len(spec["data"]),
                                  deleted=spec.get("deleted", False)))
        if spec.get("deleted", False):
            # A real FAT delete frees the chain.  The data bytes stay on disk
            # unless another file reuses (overwrites) those clusters.
            for cluster in range(start, start + clusters):
                fat[cluster] = 0
        if spec.get("wipe", False):
            # Simulate the clusters being reused: the content is gone for good.
            offset = DATA_START * SECTOR + (start - 2) * CLUSTER_SIZE
            volume[offset:offset + clusters * CLUSTER_SIZE] = (
                b"\x00" * clusters * CLUSTER_SIZE)

    if orphan is not None:
        allocate(orphan)                # allocated clusters, no directory entry

    volume[0:SECTOR] = _boot_sector(label, PARTITION_SECTORS,
                                    hidden_sectors=hidden_sectors)

    # Write both FAT copies.
    for copy in range(FAT_COUNT):
        base = (FAT_RESERVED + copy * FAT_SECTORS) * SECTOR
        for index, value in enumerate(fat):
            struct.pack_into("<H", volume, base + index * 2, value)

    # Write the root directory.
    root_offset = ROOT_START * SECTOR
    for index, entry in enumerate(entries):
        start = root_offset + index * 32
        volume[start:start + 32] = entry
    return bytes(volume)


def create_disk_image(path):
    """Write the complete evidence image (MBR + two FAT16 partitions)."""
    image = bytearray(DISK_SECTORS * SECTOR)

    partition_one = build_fat16_partition(
        "CASE_A",
        files=[
            {"name": "LIVE.TXT", "data": b"Case file opened 14 Aug 2026.\n"},
            {"name": "NOTES.TXT", "data": _text("A-101"),
             "deleted": True},
            {"name": "PHOTO.JPG", "data": _jpeg("A-101", 2_200),
             "deleted": True},
            {"name": "WIPED.JPG", "data": _jpeg("A-999", 1_500),
             "deleted": True, "wipe": True},
        ],
        orphan=_jpeg("ORPHAN", 1_800),
        hidden_sectors=PARTITION_START,
    )
    partition_two = build_fat16_partition(
        "HIDDEN",
        files=[
            {"name": "REPORT.PDF", "data": _pdf("B-202", 1_900)},
            {"name": "LEDGER.TXT", "data": _text("B-202"), "deleted": True},
        ],
        hidden_sectors=SECOND_PARTITION_START,
    )

    image[PARTITION_START * SECTOR:
          (PARTITION_START + PARTITION_SECTORS) * SECTOR] = partition_one
    image[SECOND_PARTITION_START * SECTOR:
          (SECOND_PARTITION_START + PARTITION_SECTORS) * SECTOR] = partition_two

    # MBR: partition 1 is present, partition 2's slot is zeroed (deleted).
    mbr = bytearray(SECTOR)
    struct.pack_into("<B3sB3sII", mbr, 446,
                     0x80, b"\x00\x00\x00", 0x0E, b"\x00\x00\x00",
                     PARTITION_START, PARTITION_SECTORS)
    mbr[510:512] = b"\x55\xaa"
    image[0:SECTOR] = mbr

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(image))
    return path


# =====================================================================
# 2. Parsing the evidence
# =====================================================================

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_mbr_partitions(image):
    """Return the four MBR partition slots (only the non-empty ones)."""
    partitions = []
    for slot in range(4):
        offset = 446 + slot * 16
        status = image[offset]
        ptype = image[offset + 4]
        start_lba, sectors = struct.unpack_from("<II", image, offset + 8)
        if ptype == 0 or sectors == 0:
            continue
        partitions.append({
            "slot": slot + 1,
            "status": "ACTIVE" if status == 0x80 else "INACTIVE",
            "type": f"0x{ptype:02X}",
            "start_lba": start_lba,
            "sectors": sectors,
        })
    return partitions


def parse_boot_sector(sector):
    """Validate a FAT16 BIOS Parameter Block; return its geometry."""
    if len(sector) < SECTOR or sector[510:512] != b"\x55\xaa":
        return None

    bytes_per_sector = struct.unpack_from("<H", sector, 11)[0]
    sectors_per_cluster = sector[13]
    reserved = struct.unpack_from("<H", sector, 14)[0]
    fat_count = sector[16]
    root_entries = struct.unpack_from("<H", sector, 17)[0]
    total_16 = struct.unpack_from("<H", sector, 19)[0]
    total_32 = struct.unpack_from("<I", sector, 32)[0]
    fat_sectors = struct.unpack_from("<H", sector, 22)[0]
    filesystem = sector[54:62].decode("ascii", errors="ignore").strip()
    label = sector[43:54].decode("ascii", errors="ignore").strip()

    total_sectors = total_32 or total_16
    if (bytes_per_sector != SECTOR
            or sectors_per_cluster not in (1, 2, 4, 8, 16, 32, 64)
            or reserved < 1 or fat_count not in (1, 2)
            or root_entries < 1 or fat_sectors < 1 or total_sectors < 1
            or "FAT" not in filesystem):
        return None

    root_sectors = (root_entries * 32 + bytes_per_sector - 1) // bytes_per_sector
    data_start = reserved + fat_count * fat_sectors + root_sectors
    clusters = (total_sectors - data_start) // sectors_per_cluster
    if clusters < 1 or data_start >= total_sectors:
        return None

    return {
        "filesystem": filesystem,
        "label": label,
        "bytes_per_sector": bytes_per_sector,
        "sectors_per_cluster": sectors_per_cluster,
        "reserved_sectors": reserved,
        "fat_count": fat_count,
        "root_entries": root_entries,
        "fat_sectors": fat_sectors,
        "total_sectors": total_sectors,
        "root_start": reserved + fat_count * fat_sectors,
        "data_start": data_start,
        "clusters": clusters,
    }


def scan_for_boot_sectors(image):
    """Scan every 512-byte sector for a valid FAT16 boot sector."""
    found = []
    total = len(image) // SECTOR
    for lba in range(total):
        sector = image[lba * SECTOR:(lba + 1) * SECTOR]
        if sector[510:512] != b"\x55\xaa":
            continue
        geometry = parse_boot_sector(sector)
        if geometry:
            found.append({"start_lba": lba, **geometry})
    return found


def directory_entries(image, part_offset, geometry):
    """Return the root-directory entries of a FAT16 partition."""
    root_offset = part_offset + geometry["root_start"] * SECTOR
    entries = []
    for index in range(geometry["root_entries"]):
        raw = image[root_offset + index * 32:root_offset + (index + 1) * 32]
        if len(raw) < 32 or raw[0] == 0x00:
            break
        entries.append(raw)
    return entries


def entry_name(raw):
    """Decode an 8.3 name.  A deleted entry lost its first character."""
    base = raw[0:8].rstrip(b" ").decode("ascii", errors="replace")
    extension = raw[8:11].rstrip(b" ").decode("ascii", errors="replace")
    if raw[0] == DELETED_MARKER:
        base = "_" + base[1:]
    return base + (f".{extension}" if extension else "")


def file_extent(part_offset, geometry, start_cluster, size):
    """Byte range [start, end) of a file's data inside the disk image."""
    if start_cluster < 2 or size == 0:
        return None
    cluster_size = geometry["sectors_per_cluster"] * SECTOR
    start = (part_offset + (geometry["data_start"]
             + (start_cluster - 2) * geometry["sectors_per_cluster"]) * SECTOR)
    return start, start + size


def live_cluster_ranges(image, part_offset, geometry):
    """Cluster numbers currently owned by non-deleted files."""
    ranges = set()
    for raw in directory_entries(image, part_offset, geometry):
        attribute = raw[11]
        if raw[0] == DELETED_MARKER or attribute & 0x08 or attribute & 0x10:
            continue
        if attribute & 0x0F == 0x0F:
            continue
        start_cluster = struct.unpack_from("<H", raw, 26)[0]
        size = struct.unpack_from("<I", raw, 28)[0]
        clusters = max(1, (size + CLUSTER_SIZE - 1) // CLUSTER_SIZE)
        ranges.update(range(start_cluster, start_cluster + clusters))
    return ranges


def read_deleted_file(image, part_offset, geometry, start_cluster, size,
                      used_clusters):
    """Read a deleted file's data and judge whether it is still intact."""
    cluster_size = geometry["sectors_per_cluster"] * SECTOR
    cluster_count = max(1, (size + cluster_size - 1) // cluster_size)
    clusters = set(range(start_cluster, start_cluster + cluster_count))
    data_start = (part_offset + (geometry["data_start"]
                  + (start_cluster - 2) * geometry["sectors_per_cluster"]) * SECTOR)
    data = bytes(image[data_start:data_start + size])

    if clusters & used_clusters:
        return data, "OVERWRITTEN", "clusters were reused by a live file"
    if not data or all(byte == 0 for byte in data):
        return data, "OVERWRITTEN", "data area is filled with zeros"
    return data, "RECOVERED", "contiguous clusters were still intact"


# =====================================================================
# 3. File carving (recovery without any directory entry)
# =====================================================================

SIGNATURES = [
    ("jpg", b"\xff\xd8\xff", b"\xff\xd9"),
    ("png", b"\x89PNG\r\n\x1a\n", b"IEND\xaeB`\x82"),
    ("pdf", b"%PDF-", b"%%EOF"),
]


def carve_files(image, known_ranges):
    """Find JPEG/PNG/PDF files by their headers and footers."""
    carved = []
    for extension, header, footer in SIGNATURES:
        position = 0
        while True:
            start = image.find(header, position)
            if start < 0:
                break
            end = image.find(footer, start + len(header))
            if end < 0:
                position = start + 1       # stray header without a footer
                continue
            end += len(footer)
            size = end - start
            position = max(end, start + 1)
            if size < 100:
                continue
            covered = next((name for name, (lo, hi) in known_ranges.items()
                            if lo <= start < hi), None)
            if covered:
                print(f"  signature at offset 0x{start:X} belongs to "
                      f"'{covered}' - already handled, skipping")
                continue
            carved.append({
                "extension": extension,
                "offset": start,
                "lba": start // SECTOR,
                "size": size,
                "data": bytes(image[start:end]),
            })
    return carved


# =====================================================================
# 4. Main recovery workflow and reporting
# =====================================================================

def section(title):
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)


def recover(image_path, report_path):
    image = image_path.read_bytes()
    RECOVERED_DIR.mkdir(exist_ok=True)
    for old in RECOVERED_DIR.iterdir():
        if old.is_file():
            old.unlink()

    report = {
        "evidence": {
            "file": image_path.name,
            "size_bytes": len(image),
            "sectors": len(image) // SECTOR,
            "sha256": sha256(image),
            "write_blocker": "original image opened read-only and never modified",
        },
        "mbr_partitions": [],
        "deleted_partitions": [],
        "deleted_files": [],
        "carved_files": [],
        "summary": {},
    }

    print("=" * 70)
    print("       DELETED FILE AND PARTITION RECOVERY - FORENSIC REPORT")
    print("=" * 70)
    print(f"Evidence image : {image_path}")
    print(f"Image size     : {len(image):,} bytes "
          f"({len(image) / (1024 * 1024):.2f} MiB, {len(image) // SECTOR:,} sectors)")
    print(f"SHA-256        : {report['evidence']['sha256']}")
    print("Acquisition    : working on the image only, source is not changed")

    # ---------------------------------------------------------- partitions
    section("[1] MBR PARTITION TABLE")
    mbr_partitions = read_mbr_partitions(image)
    report["mbr_partitions"] = mbr_partitions
    print(f"{'Slot':<6}{'Type':<7}{'Status':<10}{'Start LBA':>12}"
          f"{'Sectors':>10}{'Size':>12}")
    for partition in mbr_partitions:
        size_mib = partition["sectors"] * SECTOR / (1024 * 1024)
        print(f"{partition['slot']:<6}{partition['type']:<7}"
              f"{partition['status']:<10}{partition['start_lba']:>12}"
              f"{partition['sectors']:>10}{size_mib:>9.2f} MiB")
    empty_slots = 4 - len(mbr_partitions)
    print(f"\n{empty_slots} partition slot(s) are empty - one of them is the "
          f"deleted partition.")

    section("[2] DELETED PARTITION RECOVERY (boot-sector scan)")
    boot_sectors = scan_for_boot_sectors(image)
    print(f"Scanned {len(image) // SECTOR:,} sectors, "
          f"found {len(boot_sectors)} FAT16 boot sector(s).")

    live_partitions = []
    deleted_partitions = []
    for boot in boot_sectors:
        covered_by = next((p for p in mbr_partitions
                           if p["start_lba"] <= boot["start_lba"]
                           < p["start_lba"] + p["sectors"]), None)
        boot["status"] = "ALLOCATED" if covered_by else "DELETED"
        if covered_by:
            live_partitions.append(boot)
            print(f"  LBA {boot['start_lba']:>6}  {boot['filesystem']:<8} "
                  f"label={boot['label']:<10} status=allocated (live partition)")
        else:
            deleted_partitions.append(boot)
            print(f"  LBA {boot['start_lba']:>6}  {boot['filesystem']:<8} "
                  f"label={boot['label']:<10} status=DELETED PARTITION")
            print(f"           size={boot['total_sectors'] * SECTOR:,} bytes, "
                  f"{boot['clusters']:,} clusters, "
                  f"volume label {boot['label']!r}")

    if deleted_partitions:
        # Rebuild a repaired MBR copy; the evidence image itself is untouched.
        repaired = bytearray(image[0:SECTOR])
        used_slots = {partition["slot"] - 1 for partition in mbr_partitions}
        free_slots = [slot for slot in range(4) if slot not in used_slots]
        for slot, boot in zip(free_slots, deleted_partitions):
            struct.pack_into("<B3sB3sII", repaired, 446 + slot * 16,
                             0x00, b"\x00\x00\x00", 0x0E, b"\x00\x00\x00",
                             boot["start_lba"], boot["total_sectors"])
        (RECOVERED_DIR / "recovered_mbr.bin").write_bytes(bytes(repaired))
        print("\n  Wrote repaired MBR copy -> recovered/recovered_mbr.bin")
        print("  (the original disk_image.dd was not modified)")
        report["repaired_mbr"] = "recovered/recovered_mbr.bin"
        report["deleted_partitions"] = [
            {
                "start_lba": boot["start_lba"],
                "filesystem": boot["filesystem"],
                "label": boot["label"],
                "sectors": boot["total_sectors"],
                "clusters": boot["clusters"],
            }
            for boot in deleted_partitions
        ]

    # ---------------------------------------------------------- files
    section("[3] DELETED FILE RECOVERY (FAT16 directory entries)")
    partitions = [(index + 1, boot)
                  for index, boot in enumerate(live_partitions + deleted_partitions)]
    known_ranges = {}

    for part_number, boot in partitions:
        part_offset = boot["start_lba"] * SECTOR
        used_clusters = live_cluster_ranges(image, part_offset, boot)
        print(f"\nPartition {part_number}: label={boot['label']} "
              f"start=LBA {boot['start_lba']}  ({boot['filesystem']})")

        live_names = []
        deleted_entries = []
        for raw in directory_entries(image, part_offset, boot):
            attribute = raw[11]
            if attribute & 0x08:
                continue                                # volume label
            if attribute & 0x10 or attribute & 0x0F == 0x0F:
                continue                                # folder / LFN
            name = entry_name(raw)
            start_cluster = struct.unpack_from("<H", raw, 26)[0]
            size = struct.unpack_from("<I", raw, 28)[0]
            if raw[0] == DELETED_MARKER:
                deleted_entries.append((name, start_cluster, size))
            else:
                live_names.append(f"{name} ({size} bytes)")
                extent = file_extent(part_offset, boot, start_cluster, size)
                if extent:
                    known_ranges[f"P{part_number}/{name}"] = extent

        print("  live files      : " + (", ".join(live_names) if live_names else "none"))
        if not deleted_entries:
            print("  deleted entries : none")
            continue

        for index, (name, start_cluster, size) in enumerate(deleted_entries, start=1):
            data, status, reason = read_deleted_file(
                image, part_offset, boot, start_cluster, size, used_clusters)
            extent = file_extent(part_offset, boot, start_cluster, size)
            if extent:
                known_ranges[f"P{part_number}/{name}"] = extent

            item = {
                "partition": part_number,
                "name": name,
                "size": size,
                "start_cluster": start_cluster,
                "status": status,
                "reason": reason,
            }
            if status == "RECOVERED":
                output_name = f"P{part_number}_deleted_{name.replace('?', '_')}"
                output_path = RECOVERED_DIR / output_name
                output_path.write_bytes(data)
                item["recovered_as"] = f"recovered/{output_name}"
                item["sha256"] = sha256(data)
                print(f"  [{index}] {name:<14} {size:>6} bytes  "
                      f"RECOVERED -> recovered/{output_name}")
                print(f"      SHA-256 {item['sha256']}")
            else:
                print(f"  [{index}] {name:<14} {size:>6} bytes  "
                      f"UNRECOVERABLE ({reason})")
            report["deleted_files"].append(item)

    # ---------------------------------------------------------- carving
    section("[4] FILE CARVING (no directory entry - signature scan)")
    known_ranges = {name: extent for name, extent in known_ranges.items()
                    if extent}
    carved = carve_files(image, known_ranges)
    for number, item in enumerate(carved, start=1):
        output_name = f"carved_{number:03d}.{item['extension']}"
        output_path = RECOVERED_DIR / output_name
        output_path.write_bytes(item["data"])
        record = {
            "file": f"recovered/{output_name}",
            "offset": item["offset"],
            "lba": item["lba"],
            "size": item["size"],
            "sha256": sha256(item["data"]),
        }
        report["carved_files"].append(record)
        print(f"  {output_name:<18} offset=0x{item['offset']:08X} "
              f"(LBA {item['lba']:>6})  size={item['size']:>5} bytes")
        print(f"      SHA-256 {record['sha256']}")
    if not carved:
        print("  no orphaned files found")

    # ---------------------------------------------------------- summary
    deleted_total = len(report["deleted_files"])
    recovered_total = sum(1 for item in report["deleted_files"]
                          if item["status"] == "RECOVERED")
    overwritten_total = deleted_total - recovered_total
    report["summary"] = {
        "live_partitions": len(live_partitions),
        "deleted_partitions_found": len(deleted_partitions),
        "deleted_files_found": deleted_total,
        "deleted_files_recovered": recovered_total,
        "deleted_files_unrecoverable": overwritten_total,
        "carved_files": len(carved),
        "total_files_written": recovered_total + len(carved),
    }
    section("[5] SUMMARY")
    print(f"Live partitions              : {len(live_partitions)}")
    print(f"Deleted partitions recovered : {len(deleted_partitions)}")
    print(f"Deleted files found          : {deleted_total}")
    print(f"  recovered from metadata    : {recovered_total}")
    print(f"  permanently overwritten    : {overwritten_total}")
    print(f"Files recovered by carving   : {len(carved)}")
    print(f"Output folder                : {RECOVERED_DIR}")
    print(f"Report                       : {report_path}")
    print("\nNote: a 'permanently deleted' file is only unrecoverable when its")
    print("clusters have been overwritten.  Until then the data remains on disk.")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Recover deleted FAT16 files and deleted partitions")
    parser.add_argument("--image", type=Path, default=IMAGE_FILE,
                        help="disk image to examine (default: disk_image.dd)")
    parser.add_argument("--rebuild", action="store_true",
                        help="regenerate the demonstration disk image first")
    parser.add_argument("--report", type=Path, default=REPORT_FILE,
                        help="JSON report output path")
    args = parser.parse_args()

    if args.rebuild or not args.image.exists():
        print(f"Building demonstration evidence image: {args.image}")
        create_disk_image(args.image)
        print(f"Created {args.image} "
              f"({args.image.stat().st_size:,} bytes)\n")

    recover(args.image, args.report)


if __name__ == "__main__":
    main()
