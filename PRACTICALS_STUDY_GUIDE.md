# CSDF and IR Practicals — Detailed Study Guide

This is a readable, revision-oriented explanation of every **CSDF** and **IR**
practical in this repository. It covers the aim, the theory, how the code
works, the important formulas, the actual results, and the main limitations.

For the line-by-line version with longer code excerpts and full output blocks,
see [`ALL_PRACTICALS_EXPLAINED.md`](ALL_PRACTICALS_EXPLAINED.md).

| Subject | Full form | Practicals |
|---|---|---|
| **CSDF** | Cyber Security and Digital Forensics | 1. Email header analysis<br>2. CAPTCHA generation and verification<br>3. WiFi intrusion detection<br>4. Deleted file and partition recovery<br>5. Log capture and event correlation<br>Mini project: Digital image forensics |
| **IR** | Information Retrieval | 1. Document similarity<br>2. PageRank<br>3. Map-Reduce character count<br>4. Web crawler<br>5. XML web graph and topic-specific PageRank<br>Mini project: Document summarization |

---

# Part A — CSDF (Cyber Security and Digital Forensics)

## CSDF Practical 1 — Email Header Analysis

**Files:** `CSDF/Practical1_Email_Header_Analysis/email_header_analysis.py`,
`sample_email.txt`

### Aim

Track the path an email took and investigate possible email crimes by analysing
its header: find the sender IP, detect spoofing, and identify phishing
indicators.

### Theory

An email has two parts separated by a blank line:

```text
Headers
<blank line>
Body
```

Important headers:

| Header | Meaning |
|---|---|
| `From` | Claimed sender — easy to forge |
| `Reply-To` | Where replies actually go |
| `Received` | One entry per mail server the message passed through |
| `Message-ID` | Unique message identifier |
| `Subject`, `Date`, `To` | Display and routing metadata |

Two header rules matter:

1. **Header folding** — a long header can continue on the next line, which
   starts with a space or tab.
2. **Received ordering** — every mail server *prepends* its own `Received`
   line. So:
   - the first `Received` in the file is the newest hop,
   - the last `Received` is the oldest hop, closest to the sender.

### How the code works

`parse_email()`:

1. Splits headers from the body with `text.partition("\n\n")`.
2. Reads each header line.
3. If the line starts with a space or tab, appends it to the previous header
   (`current`).
4. Stores repeated `Received` headers in a list and all other headers in a
   dictionary.

Finding the sender IP:

```python
ips = []
for hop in received:
    match = re.search(r"\[(\d{1,3}(?:\.\d{1,3}){3})\]", hop)
    if match:
        ips.append(match.group(1))

print("Sender IP address :", ips[-1] if ips else "not found")
```

The last IP belongs to the oldest hop, so it is the best available indication
of the sender.

Phishing checks:

- `Reply-To` domain differs from `From` domain → possible spoofing.
- Subject contains words such as `urgent`, `verify`, `password`, `otp`, `prize`.
- A body URL points to a domain different from the sender's domain.

### Sample result

```text
From       : "Secure Bank Alert" <support@fake-bank.com>
Reply-To   : helpdesk@evil-scam.net
Sender IP  : 203.0.113.45

[WARNING] Reply-To domain 'evil-scam.net' is different from From domain 'fake-bank.com'
[WARNING] Subject has suspicious words: urgent, verify
[WARNING] Body link 'http://evil-scam.net/verify-login' is not from the sender's domain

Verdict: this email looks like a phishing / suspicious mail.
```

### Limitations

- `From` and `Received` can be forged.
- A real investigation should also check SPF, DKIM, DMARC, reverse DNS, WHOIS,
  and URL reputation.

---

## CSDF Practical 2 — CAPTCHA Generation and Verification

**File:** `CSDF/Practical2_CAPTCHA/captcha.py`
**Dependency:** Pillow

### Aim

Generate a distorted text CAPTCHA image and verify the text entered by the
user.

### Theory

CAPTCHA means **Completely Automated Public Turing test to tell Computers and
Humans Apart**. It should be easy for a human and hard for an automated bot.

This practical creates:

- 5 random uppercase letters/digits,
- random dark colours,
- random vertical positions,
- 6 random noise lines,
- 300 random noise dots.

### How the code works

1. `random.choices(string.ascii_uppercase + string.digits, k=5)` creates the
   answer.
2. `generate_captcha()` creates a white 250×90 image.
3. Each character is drawn with:
   - a random dark RGB colour,
   - a random `y` position,
   - a fixed horizontal step.
4. Noise is added with `draw.line()` and `draw.point()`.
5. The image is saved as `captcha.png`.
6. `verify()` checks:

```python
answer.strip().upper() == expected.upper()
```

This is case-insensitive and ignores surrounding whitespace for usability.

The user gets **three attempts**. After three failures, the correct text is
printed for the classroom demo.

### Output

The CAPTCHA text changes every run. With dummy input:

```text
CAPTCHA image saved as: .../captcha.png
Attempt 1/3 - enter the CAPTCHA text: Wrong CAPTCHA.
Attempt 2/3 - enter the CAPTCHA text: Wrong CAPTCHA.
Attempt 3/3 - enter the CAPTCHA text: Wrong CAPTCHA.
Verification failed. The correct text was: QK06Q
```

### Limitations

- Text is not warped or heavily overlapped.
- The font is fixed.
- The noise is simple enough for a modern OCR system.
- A production CAPTCHA needs distortion, background textures, rate limiting,
  and server-side session binding.

---

## CSDF Practical 3 — WiFi Intrusion Detection

**Files:** `CSDF/Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py`,
`wifi_log.txt`

### Aim

Read a wireless access-point log, detect a device trying many passwords to
access an IP printer, and block that device.

### Log format

Each line has four fields:

```text
time  MAC-address  IP-address  status
10:00:05  AA:BB:CC:DD:EE:99  192.168.1.55  FAIL
```

### Detection policy

| Rule | Value |
|---|---|
| Maximum failures before blocking | 5 |
| Whitelisted devices | `...:01`, `...:02` |
| Action | On the 5th failure, block the MAC |
| After blocking | Reject all further attempts, even correct passwords |

### How the code works

Two state containers:

```python
failed_attempts = {}   # MAC -> number of failures
blocked = set()        # MACs that are blocked
```

For each log line:

1. Skip malformed lines (`len(parts) != 4`).
2. Skip whitelisted devices.
3. If the MAC is already blocked, reject it immediately.
4. On `FAIL`, increment the counter.
5. When `failed_attempts[mac] >= 5`, add it to `blocked` and print an alert.
6. `SUCCESS` from a non-blocked, non-whitelisted device is allowed.

The counter is incremented **before** comparing with the threshold, so the
fifth failure triggers the block.

### Output

```text
10:00:05  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 1
...
10:00:13  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 5
10:00:13  [ALERT] AA:BB:CC:DD:EE:99 is trying to crack the WiFi password!
10:00:13  [ACTION] Access denied - AA:BB:CC:DD:EE:99 blocked from the network

10:00:15  [REJECTED] AA:BB:CC:DD:EE:99 is blocked - access denied again

----- Summary -----
Failed login attempts : {'AA:BB:CC:DD:EE:99': 5, 'AA:BB:CC:DD:EE:77': 1}
Blocked devices       : {'AA:BB:CC:DD:EE:99'}
```

### Limitations

- This is a static log, not a live monitor.
- MAC addresses can be spoofed.
- A fixed failure count is simplistic; production systems use time windows,
  per-AP baselines, and reversible blocks.
- Real blocking would use `iptables`, `nftables`, or the access point's deny
  list.

---

## CSDF Practical 4 — Deleted File and Partition Recovery

**File:** `CSDF/Practical4_Deleted_File_Partition_Recovery/forensic_recovery.py`
**Input:** generated 9 MiB FAT16 disk image, `disk_image.dd`
**Output:** `recovered/`, `recovery_report.json`

### Aim

Build a forensic tool that recovers deleted files, recovers a deleted
partition, and documents every recovered artefact with SHA-256 hashes.

### Why a disk image?

Reading a real disk such as `/dev/sda` requires root access and risks modifying
evidence. The practical therefore generates a realistic FAT16 image and applies
the same byte-level recovery logic to the image file. The original image is
never modified.

### FAT16 background

A FAT16 partition contains:

| Region | Purpose |
|---|---|
| Boot sector / BPB | File-system geometry |
| FAT 1 and FAT 2 | Cluster chains |
| Root directory | 32-byte file entries |
| Data region | File contents |

The data region starts at:

```text
data_start = reserved_sectors + fat_count × fat_sectors + root_dir_sectors
```

A directory entry contains:

| Offset | Field |
|---|---|
| 0–7 | 8-character name |
| 8–10 | 3-character extension |
| 11 | Attribute |
| 26–27 | First cluster |
| 28–31 | File size |

### What deletion actually does

On a FAT quick delete:

1. The first byte of the directory entry becomes `0xE5`.
2. The FAT chain is set to `0` — clusters are marked free.
3. The start cluster and file size remain in the directory entry.
4. **The file contents remain on disk** until those clusters are reused.

So "permanently deleted" really means **overwritten**. The demo includes:

| Partition | Contents |
|---|---|
| `CASE_A`, LBA 2048 | live `LIVE.TXT`; deleted `NOTES.TXT`; deleted `PHOTO.JPG`; deleted and zeroed `WIPED.JPG`; orphan JPEG with no directory entry |
| `HIDDEN`, LBA 10240 | **MBR entry erased**; live `REPORT.PDF`; deleted `LEDGER.TXT` |

### Recovery pipeline

```text
create image
   ↓
read MBR partition table
   ↓
scan every sector for valid FAT boot sectors
   ↓
walk root directory for entries marked 0xE5
   ↓
read deleted file data from first cluster + size
   ↓
carve files that have no directory entry
   ↓
hash and report
```

### 1. Partition recovery

`read_mbr_partitions()` reads four 16-byte MBR slots at offset 446. A slot is
skipped if its type byte is `0`.

`scan_for_boot_sectors()` checks every 512-byte sector for:

- the `0x55AA` boot signature,
- a valid FAT BPB: 512-byte sectors, legal cluster size, valid FAT count, root
  entries, FAT size, total sectors, and a file-system string containing `FAT`.

`0x55AA` alone is not enough because it appears in boot code and random data.
Geometry validation removes false positives.

A boot sector inside an existing MBR partition is a **live partition**. A boot
sector outside all MBR partitions is a **deleted partition**.

The tool writes `recovered/recovered_mbr.bin`, a repaired copy of the MBR,
without touching the evidence image.

### 2. Metadata-based file recovery

For each deleted directory entry:

```python
name = entry_name(raw)              # first character lost
start_cluster = unpack("<H", raw, 26)
size = unpack("<I", raw, 28)
```

The deleted file's FAT chain is gone, so the code reads
`ceil(size / cluster_size)` clusters **contiguously** from the recorded start
cluster.

It declares the file unrecoverable if:

- its clusters are now used by a live file, or
- the data area is entirely zeros.

The lost first filename character is replaced with `_`, which is why
`NOTES.TXT` becomes `_OTES.TXT`.

### 3. File carving

Carving ignores the file system and searches raw bytes for signatures:

| Type | Header | Footer |
|---|---|---|
| JPEG | `FF D8 FF` | `FF D9` |
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `IEND` + `AE 42 60 82` |
| PDF | `%PDF-` | `%%EOF` |

Offsets already covered by a directory entry are skipped to avoid duplicates.
The orphan JPEG becomes `carved_001.jpg`.

### Actual result

```text
Live partitions              : 1
Deleted partitions recovered : 1
Deleted files found          : 4
  recovered from metadata    : 3
  permanently overwritten    : 1
Files recovered by carving   : 1
```

Recovered:

- `_OTES.TXT`
- `_HOTO.JPG`
- `_EDGER.TXT` from the deleted partition

Not recovered:

- `_IPED.JPG` — its clusters were zeroed.

Carved:

- `carved_001.jpg` — no directory entry existed.

### Why this matters

- Deletion removes **metadata pointers**, not necessarily the data.
- Recovery fails when data is overwritten, zeroed, trimmed on an SSD, or
  encrypted.
- A real investigation uses write blockers, hashes, a chain-of-custody log, and
  tools such as Autopsy, The Sleuth Kit, TestDisk, or PhotoRec.

---

## CSDF Practical 5 — Log Capturing and Event Correlation

**File:** `CSDF/Practical5_Log_Capture_Event_Correlation/log_capture_correlation.py`
**Inputs:** `logs/auth.log`, `logs/firewall.log`, `logs/web_access.log`
**Output:** `output/captured_events.jsonl`, `log_manifest.json`,
`correlation_report.json`

### Aim

Capture logs from multiple sources, normalise them into one event format,
detect attacks using sliding time windows, and correlate related alerts into
incidents.

### Why correlation is needed

A single log line rarely proves an attack:

- five failed SSH logins alone are suspicious,
- a port scan before them and a successful login afterwards tell a much
  stronger story.

The pipeline mirrors a SIEM:

```text
collect → normalise → detect → correlate → report
```

### Input formats

**Auth log — Linux syslog:**

```text
Aug 14 10:13:50 webserver sshd[2092]: Failed password for invalid user admin from 203.0.113.45 port 50110 ssh2
```

**Firewall log:**

```text
2026-08-14T10:13:10Z FW01 DENY TCP 203.0.113.45 10.0.0.5 44001 21
```

**Web access log — Apache/Nginx combined:**

```text
203.0.113.45 - - [14/Aug/2026:10:17:10 +0000] "GET /admin/login.php HTTP/1.1" 404 512 "-" "sqlmap/1.7"
```

### Stage 1 — Capture

`capture_logs()` reads each source and records a SHA-256 hash of the **raw
bytes** before parsing. This is the digital-forensics equivalent of sealing
evidence: if the file changes later, its hash will no longer match the
manifest.

### Stage 2 — Normalise

Every source is converted to the same schema:

| Field | Meaning |
|---|---|
| `id` | `EVT-0001` |
| `timestamp`, `epoch` | UTC time for sorting and comparison |
| `source` | auth / firewall / web |
| `event` | `ssh_login_failure`, `firewall_deny`, `web_request` |
| `src_ip` | used for correlation |
| `user`, `path`, `status`, `dst_port` | source-specific details |
| `raw`, `line` | original evidence |

Two time problems are handled:

- syslog has no year/time zone → the demo assumes UTC and 2026.
- Apache logs include `+0000` → `%z` parses it and converts to UTC.

Without this, `10:15` from two logs could mean different real times.

### Stage 3 — Detection rules

| Rule | Condition | Severity |
|---|---|---|
| `PORT_SCAN` | ≥ 5 distinct denied ports from one IP in 60 s | MEDIUM |
| `SSH_BRUTE_FORCE` | ≥ 3 failed SSH logins from one IP in 120 s | HIGH |
| `LOGIN_AFTER_FAILURES` | successful SSH login after ≥ 3 failures in 15 min | CRITICAL |
| `WEB_SCAN` | ≥ 3 distinct 4xx paths from one IP in 120 s | MEDIUM |

The key function is `first_window()`:

```python
for start in range(len(events)):
    window = [event for event in events[start:]
              if event["epoch"] - events[start]["epoch"] <= window_seconds]
    count = len({event[distinct_key] for event in window}) ...
    if count >= threshold:
        return window
```

Why sliding windows?

- Counting failures across the whole file would eventually flag a normal user
  who occasionally mistypes a password.
- The window asks: *did many bad things happen close together?*
- Port and web scans count **distinct** ports/paths, because repeating one URL
  is not a scan.

### Stage 4 — Correlation

`correlate()` groups alerts by `src_ip` and merges alerts whose gap is at most
15 minutes.

Each incident gets:

- the maximum severity of its alerts,
- a score = sum of alert scores, capped at 100:
  - MEDIUM = 15
  - HIGH = 30
  - CRITICAL = 40
- ordered attack stages,
- all related events,
- recommendations.

### Attack story in the sample logs

```text
10:13:10–10:13:30  port scan: 21, 22, 23, 80, 443, 3306
10:13:50–10:14:23  five failed SSH logins
10:15:40           successful login as 'deploy'
10:17:10–10:17:35  web scanning: /.env, /admin/login.php, /backup.zip ...
```

Correlated result:

```text
INC-001  CRITICAL  score=100  source=203.0.113.45
Stages: Reconnaissance → Credential access → Initial access → Discovery
```

A second IP, `198.51.100.7`, only produced a MEDIUM web-scan incident. Its two
SSH failures were deliberately below the brute-force threshold — an example of
threshold tuning to avoid false positives.

### Final summary

```text
Events captured          : 36
Log sources              : 3
Alerts raised            : 5
Correlated incidents     : 2
Critical incidents       : 1
Highest risk source      : 203.0.113.45 (score 100, 19 events)
```

### Limitations

- Logs are replayed from files, not followed live.
- Correlation is IP-based; NAT and shared proxies can mislead it.
- Clock skew breaks correlation.
- Attackers can forge or delete logs; hashes detect changes only after capture.
- Thresholds are fixed; real SIEMs use baselines, threat intelligence, and risk
  scoring.

---

## CSDF Mini Project — Digital Image Forensics Tool

**File:** `CSDF/MiniProject_Image_Forensics/image_forensics.py`
**Dependency:** Pillow

### Aim

Design a tool that examines a suspect image like a forensic examiner:

1. prove integrity with hashes,
2. recover EXIF/GPS metadata,
3. localise possible splicing, cloning, or retouching,
4. compare a suspect image with a known original,
5. produce HTML and JSON reports.

### Techniques used

#### 1. Integrity and chain of custody

- SHA-256 and MD5 hashes.
- File size, format, dimensions, frames, and byte entropy:

```text
H = −Σ p(i) · log₂ p(i),   i = 0…255
```

SHA-256 proves integrity; MD5 is kept for compatibility.

#### 2. Metadata forensics

- Camera make/model, software, timestamps.
- GPS latitude/longitude converted from degrees-minutes-seconds to decimal.
- Raw-byte scan for editor signatures: Photoshop, GIMP, Lightroom, Snapseed,
  Canva, etc.
- Flags:
  - editing software found,
  - missing camera information,
  - missing EXIF,
  - timestamp mismatch.

#### 3. Error Level Analysis (ELA)

Recompress the image as JPEG at quality `q` and measure the pixel difference:

```text
I_q = JPEG(I, quality=q)
E(x,y) = |I(x,y) − I_q(x,y)| × scale
```

A region saved with a different compression history has a different error
level. Each 16×16 block is tested with a robust z-score:

```text
z_E(B) = 0.6745 × (mean(E in B) − median(mean(E))) / MAD(mean(E))
```

`median` and `MAD` are used instead of mean/standard deviation so a few
extreme blocks do not distort the threshold.

#### 4. Noise inconsistency

Laplacian variance per block:

```text
L(x,y) = I(x−1,y) + I(x+1,y) + I(x,y−1) + I(x,y+1) − 4I(x,y)
Var(B) = average of (L − mean)²
z_N(B) = 0.6745 × (Var(B) − median(Var)) / MAD(Var)
```

A blurred cloned region has less noise; a noisy pasted region has more.

#### 5. Agreement map

A block is strongly suspicious only if **both** ELA and noise analysis flag it:

```text
A(B) = ELA_flag(B) AND Noise_flag(B)
```

This reduces false positives from ordinary edges.

#### 6. Perceptual hash — dHash

The image is resized to 9×8 grayscale. Each bit is:

```text
1 if pixel(i,j) < pixel(i,j+1), else 0
```

Similarity:

```text
distance = number of differing bits
similarity = 100 × (1 − distance / 64)
```

dHash survives resizing and re-saving, unlike SHA-256.

#### 7. Final score

```text
S = 100 × (0.25·ELA + 0.25·Noise + 0.30·Localisation + 0.20·Metadata)
```

| Score | Level |
|---|---|
| 0–30 | LOW |
| 31–60 | MEDIUM |
| 61–100 | HIGH |

### Demo result

| Image | Score | Meaning |
|---|---|---|
| `original.jpg` | **25 / 100** | LOW |
| `tampered.jpg` | **64 / 100** | HIGH |

The tampered image has:

- a GIMP signature in metadata,
- missing camera info,
- a larger connected anomaly region,
- inconsistent noise in the pasted patch.

Comparison:

```text
original.jpg  vs  copy_resized.jpg
dHash distance : 4 / 64
Similarity     : 93.75%
Verdict        : similar image
```

Self-test:

```text
[PASS] Exact hashes differ
[PASS] Metadata flags appear on tampered copy
[PASS] Tampered copy has a higher risk score
[PASS] Re-saved copy still matches original
[PASS] Tampered region localised
Checks passed: 5 / 5
```

### Limitations

- ELA and noise analysis are heuristics, not proof.
- ELA works best for JPEG, weaker for PNG/BMP/TIFF.
- Social-media recompression can create or hide artifacts.
- dHash can fail after a heavy crop or rotation.
- Always preserve the original and work on a copy.

---

# Part B — IR (Information Retrieval)

## IR Practical 1 — Document Similarity

**Files:** `IR/Practical1_Document_Similarity/document_similarity.py`,
`doc1.txt`, `doc2.txt`

### Aim

Measure how similar two text documents are using **cosine similarity** of
word-frequency vectors.

### Theory

Each document becomes a bag-of-words vector:

```text
doc1 = (count of cricket, count of sport, count of ball, ...)
doc2 = (count of cricket, count of sport, count of ball, ...)
```

Cosine similarity:

```text
sim(d1, d2) = (Σ w1i · w2i) / (‖w1‖ · ‖w2‖)
```

where:

```text
‖w‖ = sqrt(Σ wi²)
```

The result is between 0 and 1:

- 1 = identical word distributions,
- 0 = no common words.

### How the code works

1. `words_in()` lowercases text, replaces punctuation with spaces, and splits
   into words.
2. `Counter(words)` builds the word-frequency dictionary.
3. `cosine_similarity()`:
   - computes the dot product only over common words,
   - computes each vector's length,
   - divides the dot product by the product of lengths.

Classification:

| Score | Meaning |
|---|---|
| > 0.8 | very similar |
| > 0.4 | somewhat similar |
| otherwise | different |

### Output

```text
Document 1 : doc1.txt - 58 words
Document 2 : doc2.txt - 52 words
Common words : 34

Cosine similarity = 0.8820  (88.20 %)
Result: the two documents are very similar
```

Both documents discuss cricket and share most vocabulary. Slight wording
changes (`popular` vs `famous`, `Each team tries` vs `The players try`) reduce
the score but still leave it high.

### Limitations

- No semantics — `car` and `automobile` are unrelated.
- No word order — "dog bites man" and "man bites dog" look identical.
- Common words such as `the`, `is`, and `and` dominate unless removed or
  weighted.
- No stemming — `play` and `playing` are different words.

---

## IR Practical 2 — PageRank

**File:** `IR/Practical2_PageRank/pagerank.py`

### Aim

Compute page importance from the link graph using the PageRank algorithm.

### Graph used

```text
A → B, C
B → C
C → A
D → C
```

### Theory

Standard PageRank:

```text
PR(p) = (1 − d)/N + d · Σ PR(q)/L(q)
```

- `d = 0.85` is the damping factor — probability of following a link.
- `1 − d = 0.15` is the teleport probability.
- `N` = number of pages.
- `L(q)` = number of outgoing links from page `q`.
- The sum runs over pages `q` that link to `p`.

Interpretation: a random surfer follows links 85% of the time and jumps to a
random page 15% of the time.

### How the code works

1. Initialise every page to `1/N`.
2. Repeat 50 times:
   - for each page, sum `rank[q] / out_degree(q)` for every page `q` linking
     to it,
   - apply `(1 − d)/N + d × votes`.
3. Sort scores descending.

No `if out_links` guard is needed here because every page in the sample has at
least one outgoing link. In a general implementation, dangling pages must
redistribute their rank.

### Output

```text
PageRank scores (higher = more important):
  C : 0.3941
  A : 0.3725
  B : 0.1958
  D : 0.0375

Most important page: C
```

Why:

- **C** receives links from A, B, and D — three votes.
- **A** receives a link from C, which has the highest rank and only one
  outgoing link.
- **B** receives only half of A's vote because A splits between B and C.
- **D** has no incoming links, so it gets only the teleport term
  `0.15/4 = 0.0375`.

### Limitations

- The code uses a small fixed graph.
- It does not handle dangling pages.
- A real implementation uses sparse matrices, convergence checks, and billions
  of nodes.

---

## IR Practical 3 — Map-Reduce Character Count

**File:** `IR/Practical3_MapReduce_Character_Count/map_reduce_char_count.py`
**Input:** `dataset.txt`

### Aim

Count every alphabetic character case-insensitively, ignoring non-alphabetic
characters, using the Map-Reduce model.

### Map-Reduce theory

| Phase | Job |
|---|---|
| **Map** | Emit `(letter, 1)` for each valid character |
| **Shuffle** | Group values by key: `letter → [1, 1, 1, ...]` |
| **Reduce** | Sum the list: `letter, total` |

### How the code works

**Map:**

```python
def mapper(line):
    for char in line:
        if char.isalpha():
            yield char.lower(), 1
```

**Shuffle:**

```python
grouped = defaultdict(list)
for key, value in mapped_pairs:
    grouped[key].append(value)
```

**Reduce:**

```python
def reducer(key, values):
    return key, sum(values)
```

The program runs all three phases locally in Python, so Hadoop is not required.

### Output

```text
Total letters: 139
e : 14
o : 13
a : 12
t : 12
...
z : 1
```

`e` is the most common letter in the dataset. Uppercase and lowercase versions
of the same letter are merged because the mapper calls `.lower()`. Digits,
spaces, and punctuation are ignored because of `char.isalpha()`.

### Why this demonstrates Map-Reduce

- The map phase is embarrassingly parallel — each line/chunk can be processed
  independently.
- The shuffle phase performs the expensive grouping.
- The reduce phase is a simple associative sum, so partial sums can be
  combined.

---

## IR Practical 4 — Simple Web Crawler

**File:** `IR/Practical4_Web_Crawler/web_crawler.py`
**Default seed:** `https://quotes.toscrape.com/`

### Aim

Visit a website, follow links, and print every visited page using
breadth-first search with limits.

### Theory

The web is a directed graph:

- page = node,
- hyperlink = directed edge.

| Traversal | Data structure | Order |
|---|---|---|
| BFS | queue (FIFO) | level by level |
| DFS | stack (LIFO) | deep first |

This crawler uses **BFS** because it explores the site near the seed page first
and respects depth limits naturally.

### Rules implemented

| Rule | Value/Behaviour |
|---|---|
| Same website only | compare `urlparse(url).netloc` with seed domain |
| Maximum depth | `MAX_DEPTH = 2` |
| Maximum pages | `MAX_PAGES = 5` |
| Visited set | avoid duplicates and loops |
| URL normalisation | `urljoin()` for relative links, strip `#fragment` |
| Timeout / identity | 10 s timeout, `SimpleCrawler/1.0` User-Agent |

### How the code works

**Link extraction:**

```python
class LinkFinder(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)
```

`HTMLParser` is an event-driven standard-library parser — safer than regex for
HTML.

**Downloading:**

```python
request = Request(url, headers={"User-Agent": "SimpleCrawler/1.0"})
with urlopen(request, timeout=10) as response:
    return response.read().decode("utf-8", errors="ignore")
```

Errors are caught so one broken link does not stop the crawl.

**BFS loop:**

```python
visited = set()
queue = [(START_URL, 0)]

while queue and len(visited) < MAX_PAGES:
    url, depth = queue.pop(0)
    if url in visited:
        continue
    visited.add(url)

    html = get_page(url)
    finder = LinkFinder()
    finder.feed(html)

    for link in finder.links:
        full_url = urljoin(url, link).split("#")[0]
        if (urlparse(full_url).netloc == start_domain
                and depth < MAX_DEPTH
                and full_url not in visited):
            queue.append((full_url, depth + 1))
```

### Output

```text
[1] visiting: https://quotes.toscrape.com/  (depth 0)
[2] visiting: https://quotes.toscrape.com/login  (depth 1)
[3] visiting: https://quotes.toscrape.com/author/Albert-Einstein  (depth 1)
[4] visiting: https://quotes.toscrape.com/tag/change/page/1/  (depth 1)
[5] visiting: https://quotes.toscrape.com/tag/deep-thoughts/page/1/  (depth 1)
------------------------------------------------------------
Pages visited: 5
```

Exact pages depend on the live site, but the home page is depth 0 and its links
are depth 1.

### Ethical crawler rules

A production crawler must also:

- obey `robots.txt`,
- rate-limit requests,
- identify itself with a contact User-Agent,
- handle redirects, status codes, and content types,
- avoid private/personal data without authorisation,
- respect copyright and site terms.

---

## IR Practical 5 — XML Web Graph and Topic-Specific PageRank

**Files:** `IR/Practical5_XML_WebGraph_Topic_PageRank/xml_topic_pagerank.py`,
`webgraph.xml`
**Topic:** `sports`

### Aim

Parse an XML web graph, build the graph, and rank pages using topic-specific
PageRank.

### Input graph

```xml
<page id="A" topic="news">
  <link to="B"/>
  <link to="C"/>
</page>
...
```

Parsed graph:

| Page | Links | Sports page? |
|---|---|---|
| A | B, C | No |
| B | C, D | Yes |
| C | A | Yes |
| D | B, E | Yes |
| E | C | No |
| F | E, A | No |

### Theory

Standard PageRank teleports uniformly to all pages:

```text
PR(p) = (1 − d)/N + d · Σ PR(q)/L(q)
```

Topic-specific PageRank uses a **topic teleport vector**:

```text
PR(p) = (1 − d)·T(p) + d · Σ PR(q)/L(q)
```

where:

```text
T(p) = 1/|topic_pages|  if p is a topic page
T(p) = 0                otherwise
```

Here the topic pages are `{B, C, D}`, so:

```text
T(B) = T(C) = T(D) = 1/3
T(A) = T(E) = T(F) = 0
```

A bored surfer always restarts on a sports page, so sports pages get extra rank
and pages linked from them benefit.

### How the code works

1. `ET.parse()` reads the XML.
2. `build_web_graph()`:
   - creates `graph[page] = [links]`,
   - collects pages whose `topic` equals `TOPIC`.
3. Build the teleport dictionary.
4. Start `rank = teleport`.
5. Iterate 50 times:

```python
for page in pages:
    votes = 0.0
    for other in pages:
        out_links = graph[other]
        if out_links and page in out_links:
            votes += rank[other] / len(out_links)
    new_rank[page] = (1 - DAMPING) * teleport[page] + DAMPING * votes
```

The `if out_links` guard prevents division by zero for dangling pages.

### Output

```text
Topic: sports  (topic pages: B, C, D)

C : 0.3085  <-- topic page
A : 0.2622
B : 0.2230  <-- topic page
D : 0.1448  <-- topic page
E : 0.0615
F : 0.0000
```

Why:

- **C** is a topic page and receives links from A, B, and E — it ranks first.
- **A** is not a topic page but is linked from high-ranked C and from F.
- **B** is a topic page but splits its outgoing rank between C and D.
- **D** receives only B's link and splits its own links between B and E.
- **F** has no incoming links and is not a topic page, so both terms are
  zero → `0.0000`.

This shows the important point: topic PageRank is not "give every topic page
the same score"; link structure still matters.

### Standard vs topic-specific

| | Standard | Topic-specific |
|---|---|---|
| Teleport target | all pages uniformly | only topic pages |
| Teleport value | `(1−d)/N` | `(1−d)/|topic|` for topic pages, 0 otherwise |
| Use case | global importance | importance within a topic |

---

## IR Mini Project — Document Summarization System

**File:** `IR/MiniProject_Document_Summarization/summarizer.py`
**Input:** `sample_document.txt`

### Aim

Build an **extractive** summarizer: select the most important existing
sentences instead of generating new text.

Extractive vs abstractive:

- **Extractive** — copies/selects sentences from the document.
- **Abstractive** — rewrites the content in new words.

### Pipeline

```text
raw text
  ↓ split_sentences()
  ↓ clean_words()          lowercase, remove stopwords
  ↓ word_weights()         TF-IDF weight per word
  ↓ sentence_scores()      average weight + position bonus
  ↓ select_sentences()     top-N with redundancy filter
  ↓ print_report()         summary in original order
```

### TF-IDF sentence scoring

For a word `w`:

```text
TF(w) = count(w) / most_common_count
IDF(w) = log((1 + N_sentences) / (1 + sentences_with_w)) + 1
weight(w) = TF(w) × IDF(w)
```

- **TF** rewards frequent words.
- **IDF** penalises words that appear in almost every sentence.
- `+1` smoothing avoids division by zero.
- Weights are normalised by the maximum weight to stay in `0…1`.

Sentence score:

```text
score(s) = average(weight of words in s) × position_bonus(s)
position_bonus(s) = 1 + 0.15 × (1 − index / max(N−1, 1))
```

The average prevents long sentences from winning just because they contain
more words. The position bonus reflects the idea that the opening sentences
often contain the main point.

### Redundancy removal

Two sentences are compared with Jaccard similarity:

```text
J(A, B) = |A ∩ B| / |A ∪ B|
```

If `J > 0.6`, the candidate is skipped because it repeats information already
selected. If too many are skipped, the remaining best sentences fill the
summary.

### Output

Sample document: 12 sentences, 187 words.

```text
Summary length : 3 sentences (25% of the document)

1. ISRO has successfully launched its latest communication satellite into orbit...
2. The satellite, named GSAT-25, was carried by the heaviest rocket built by ISRO.
3. The ISRO chairman said the successful launch ... is an important step ...

Summary size   : 47 words
Compression    : 74.9% smaller than the original
```

Top keywords:

```text
satellite (1.00), isro (0.75), launch (0.75), orbit (0.63), space (0.63)
```

### Limitations

- Extractive only — cannot paraphrase or merge facts.
- Regex sentence splitting can break on abbreviations such as `Dr.` or decimals.
- No stemming or lemmatisation.
- No semantic understanding or coreference resolution.
- Jaccard compares words, not meaning.

---

# Summary table

| Subject | Practical | Core concept | Key result |
|---|---|---|---|
| CSDF | 1 — Email header | Parse headers, trace `Received`, detect phishing | sender `203.0.113.45`, 3 warnings, phishing verdict |
| CSDF | 2 — CAPTCHA | Pillow image + random text + verification | 5-character CAPTCHA, 3 attempts |
| CSDF | 3 — WiFi IDS | Count failures per MAC, block brute force | attacker blocked after 5 failures |
| CSDF | 4 — Recovery | FAT16 parsing, file carving, MBR recovery | 3 files recovered, 1 carved, 1 partition rebuilt |
| CSDF | 5 — Log correlation | Normalise, sliding-window detection, correlate | 36 events, 5 alerts, 2 incidents |
| CSDF | Mini — Image forensics | Hashes, EXIF, ELA, noise, dHash | original 25 LOW, tampered 64 HIGH |
| IR | 1 — Document similarity | Bag-of-words + cosine | **0.8820 (88.20%)** |
| IR | 2 — PageRank | Random-surfer link analysis | **C = 0.3941** |
| IR | 3 — Map-Reduce | Map → shuffle → reduce | **139 letters**, `e = 14` |
| IR | 4 — Web crawler | BFS with depth/page limits | **5 pages** visited |
| IR | 5 — Topic PageRank | Personalised teleport to topic pages | **C = 0.3085** for sports |
| IR | Mini — Summarizer | TF-IDF + position bonus + Jaccard | 3 sentences, **74.9% compression** |

## Common design patterns

1. **Standalone scripts** — every practical runs with `python3 file.py`.
2. **Paths relative to the script** — `Path(__file__).parent / "input.txt"`.
3. **Pure functions plus a thin `main()`** — parsing/scoring functions are
   separate from printing.
4. **Standard library first** — only CSDF 2 and the image forensics project
   need Pillow.
5. **Deterministic sample data** — reproducible output for demonstrations.
6. **Reports as data** — larger tools build a dictionary and render it as
   console, JSON, or HTML.

## Run everything

```bash
./run_all.sh          # CSDF + IR + mini projects
./run_all.sh csdf     # CSDF 1–5 + image forensics demo
./run_all.sh ir       # IR 1–5
```

Individual examples:

```bash
python3 CSDF/Practical4_Deleted_File_Partition_Recovery/forensic_recovery.py
python3 CSDF/Practical5_Log_Capture_Event_Correlation/log_capture_correlation.py
python3 IR/Practical2_PageRank/pagerank.py
python3 IR/MiniProject_Document_Summarization/summarizer.py --stats
```

For the longer line-by-line walkthrough, see
[`ALL_PRACTICALS_EXPLAINED.md`](ALL_PRACTICALS_EXPLAINED.md).
