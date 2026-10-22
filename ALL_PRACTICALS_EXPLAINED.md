# SEM 7 LP-IV Practicals — Complete Codebase Guide

This is a single-file explanation of **every practical in this repository**:
what it aims to do, the theory behind it, how the actual code is organised,
the important functions line by line, and the output each program produces.

The repository contains two subjects:

| Subject | Full form | Practicals |
|---|---|---|
| **CSDF** | Cyber Security and Digital Forensics | 1. Email header analysis<br>2. CAPTCHA generation & verification<br>3. WiFi intrusion detection<br>Mini project: Digital image forensics tool |
| **IR** | Information Retrieval | 1. Document similarity<br>2. PageRank<br>3. Map-Reduce character count<br>4. Web crawler<br>5. XML web graph + topic PageRank<br>Mini project: Document summarization |

---

## Table of contents

- [0. Repository map and setup](#0-repository-map-and-setup)
- [CSDF Practical 1 — Email header analysis](#csdf-practical-1--email-header-analysis)
- [CSDF Practical 2 — CAPTCHA generation and verification](#csdf-practical-2--captcha-generation-and-verification)
- [CSDF Practical 3 — WiFi intrusion detection](#csdf-practical-3--wifi-intrusion-detection)
- [CSDF Mini Project — Digital image forensics tool](#csdf-mini-project--digital-image-forensics-tool)
- [IR Practical 1 — Document similarity](#ir-practical-1--document-similarity)
- [IR Practical 2 — PageRank](#ir-practical-2--pagerank)
- [IR Practical 3 — Map-Reduce alphabetic character count](#ir-practical-3--map-reduce-alphabetic-character-count)
- [IR Practical 4 — Simple web crawler](#ir-practical-4--simple-web-crawler)
- [IR Practical 5 — XML web graph and topic-specific PageRank](#ir-practical-5--xml-web-graph-and-topic-specific-pagerank)
- [IR Mini Project — Document summarization](#ir-mini-project--document-summarization)
- [Cross-practical revision sheet](#cross-practical-revision-sheet)

---

## 0. Repository map and setup

### 0.1 Source layout

Only the files that matter for the practicals are shown; generated `output/`
folders and the local `.venv/` are omitted.

```text
PRACTICALS/
├── README.md
├── run_all.sh                         # one command to run everything
│
├── CSDF/
│   ├── README.md
│   ├── Practical1_Email_Header_Analysis/
│   │   ├── email_header_analysis.py   # Practical 1
│   │   └── sample_email.txt           # phishing-style test email
│   ├── Practical2_CAPTCHA/
│   │   ├── captcha.py                 # Practical 2
│   │   └── captcha.png                # generated image (overwritten each run)
│   ├── Practical3_WiFi_Intrusion_Detection/
│   │   ├── wifi_intrusion_detection.py
│   │   └── wifi_log.txt               # simulated access-point log
│   └── MiniProject_Image_Forensics/
│       ├── image_forensics.py         # main tool
│       ├── make_samples.py            # synthetic evidence generator
│       ├── run_demo.sh                # wrapper that finds Python + Pillow
│       ├── requirements.txt           # Pillow
│       ├── sample_images/             # original / tampered / resized copies
│       └── output/                    # per-run reports (HTML + JSON + images)
│
└── IR/
    ├── README.md
    ├── OUTPUTS.md                     # recorded output of every IR practical
    ├── Practical1_Document_Similarity/
    │   ├── document_similarity.py
    │   ├── doc1.txt
    │   └── doc2.txt
    ├── Practical2_PageRank/
    │   └── pagerank.py
    ├── Practical3_MapReduce_Character_Count/
    │   ├── map_reduce_char_count.py
    │   └── dataset.txt
    ├── Practical4_Web_Crawler/
    │   └── web_crawler.py
    ├── Practical5_XML_WebGraph_Topic_PageRank/
    │   ├── xml_topic_pagerank.py
    │   └── webgraph.xml
    └── MiniProject_Document_Summarization/
        ├── summarizer.py
        ├── sample_document.txt
        └── README.md
```

### 0.2 Dependencies

| Practical | Dependency |
|---|---|
| CSDF 1 (email) | Python standard library only |
| CSDF 2 (CAPTCHA) | **Pillow** (`pip install pillow`) |
| CSDF 3 (WiFi) | Python standard library only |
| CSDF mini project | **Pillow** (`python3 -m pip install -r requirements.txt`) |
| IR 1–5 | Python standard library only |
| IR mini project | Python standard library only |
| IR 4 (crawler) | Internet access (or any reachable URL) |

### 0.3 How to run

From the repository root:

```bash
./run_all.sh                # CSDF + IR + IR mini project
./run_all.sh csdf           # CSDF 1-3 + CSDF image forensics demo
./run_all.sh csdf-project   # only the CSDF image forensics demo
./run_all.sh ir             # IR practicals 1-5
./run_all.sh project        # only the IR document summarizer
```

Individual programs:

```bash
python3 CSDF/Practical1_Email_Header_Analysis/email_header_analysis.py
python3 CSDF/Practical2_CAPTCHA/captcha.py
python3 CSDF/Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py
python3 CSDF/MiniProject_Image_Forensics/image_forensics.py --demo

python3 IR/Practical1_Document_Similarity/document_similarity.py
python3 IR/Practical2_PageRank/pagerank.py
python3 IR/Practical3_MapReduce_Character_Count/map_reduce_char_count.py
python3 IR/Practical4_Web_Crawler/web_crawler.py
python3 IR/Practical5_XML_WebGraph_Topic_PageRank/xml_topic_pagerank.py
python3 IR/MiniProject_Document_Summarization/summarizer.py --stats
```

> `run_all.sh` detects whether it is attached to a terminal. When it is not,
> it feeds dummy answers to the CAPTCHA program so the batch run does not hang.

### 0.4 Coding conventions used across the repo

Every practical is a **standalone script**, so it can be run directly without
installing the folder as a package. The common patterns are:

1. **Paths are relative to the script**, not the current directory:
   `Path(__file__).parent / "sample_email.txt"`. This means the script works
   even if it is launched from the repository root.
2. **Pure functions plus a thin `main()`**: parsing/scoring functions can be
   tested independently, while `main()` only handles input, printing and
   orchestration.
3. **Standard library first**: `re`, `math`, `Counter`, `defaultdict`,
   `Path`, `xml.etree.ElementTree`, `html.parser`, `urllib`, `hashlib`,
   `statistics`.
4. **Deterministic sample data**: the practicals ship with test inputs so the
   output is reproducible. The only randomness is the CAPTCHA text and the
   synthetic image noise.
5. **Reports as data**: the larger tools return a dictionary, then render it
   to console, JSON and HTML from the same dictionary.

---

# PART A — Cyber Security and Digital Forensics (CSDF)

---

## CSDF Practical 1 — Email header analysis

**Folder:** `CSDF/Practical1_Email_Header_Analysis/`
**Main file:** `email_header_analysis.py`
**Input:** `sample_email.txt`

### Aim

Track an email and investigate a possible email crime by analysing its header:
show the route the message travelled, find the sender's IP address, and detect
signs of spoofing and phishing.

### Background: what an email header contains

An email has two parts separated by a blank line: **headers** and **body**.

```text
Received: ...        <- one entry per mail server the message passed through
From: ...            <- claimed sender (easy to forge)
Reply-To: ...         <- where replies should go (often different in phishing)
To: ...
Subject: ...
Date: ...
Message-ID: ...
Content-Type: ...

<body starts here>
```

Two details matter:

1. **Header folding.** A long header can continue on the next line. Continuation
   lines start with a space or a tab. They must be joined to the previous header.
2. **`Received` is repeated.** Each mail server prepends its own `Received`
   line, so the **first** `Received` in the file is the newest hop and the
   **last** one is the oldest hop (closest to the original sender).

A simplified delivery path looks like this:

```text
sender  ->  smtp.fake-bank.com  ->  mx.receiver.com  ->  inbox.receiver.com
             (203.0.113.45)
```

### Code walkthrough

#### 1. Splitting headers, `Received` lines and body

```python
def parse_email(text):
    """Split the email into (headers dictionary, Received list, body)."""
    header_part, _, body = text.partition("\n\n")
    headers = {}
    received = []
    current = None

    for line in header_part.splitlines():
        # Lines starting with a space/tab continue the previous header
        if line[:1] in (" ", "\t") and current:
            if current == "received":
                received[-1] += " " + line.strip()
            else:
                headers[current] += " " + line.strip()
            continue

        name, _, value = line.partition(":")
        name = name.strip().lower()
        if name == "received":
            received.append(value.strip())
        else:
            headers[name] = value.strip()
        current = name

    return headers, received, body
```

Key points:

- `text.partition("\n\n")` cuts the file at the first blank line.
- Header names are lower-cased, so lookups like `headers.get("from")` work
  regardless of the original capitalisation.
- `Received` is stored in a **list** because it repeats; every other header is
  stored in a **dictionary** because it appears once.
- `current` remembers the last header name so a folded continuation line can be
  appended to the correct place.
- `line.partition(":")` splits on the first colon, which is important because
  values such as `Message-ID: <9c1f2e3d@fake-bank.com>` contain more colons.

#### 2. Printing the parsed header

```python
print("From       :", headers.get("from", "-"))
print("Reply-To   :", headers.get("reply-to", "-"))
print("To         :", headers.get("to", "-"))
print("Subject    :", headers.get("subject", "-"))
print("Date       :", headers.get("date", "-"))
print("Message-ID :", headers.get("message-id", "-"))
```

`headers.get(name, "-")` avoids a `KeyError` when an optional header is missing.

#### 3. Finding the sender IP address

```python
ips = []
for hop in received:
    match = re.search(r"\[(\d{1,3}(?:\.\d{1,3}){3})\]", hop)
    if match:
        ips.append(match.group(1))
print("\nSender IP address :", ips[-1] if ips else "not found")
```

- The regular expression matches an IPv4 address inside square brackets, e.g.
  `[203.0.113.45]`.
- `received` is newest-first, so `ips[-1]` is the IP in the **oldest** hop — the
  closest information available about the sender.
- In the sample, the oldest hop is `smtp.fake-bank.com (unknown [203.0.113.45])`,
  so the reported sender IP is `203.0.113.45`.

#### 4. Spoofing and phishing checks

```python
from_address = headers.get("from", "")
from_domain = from_address.split("@")[-1].rstrip(">").lower()
reply_domain = headers.get("reply-to", "").split("@")[-1].lower()

if reply_domain and reply_domain != from_domain:
    warnings.append(f"Reply-To domain '{reply_domain}' is different from "
                    f"From domain '{from_domain}' (possible spoofing)")
```

For the sample:

```text
From     : "Secure Bank Alert" <support@fake-bank.com>   -> fake-bank.com
Reply-To : helpdesk@evil-scam.net                        -> evil-scam.net
```

Because the two domains differ, the tool warns about possible spoofing. This is
a classic phishing pattern: the mail claims to come from a bank, but replies go
to an attacker-controlled domain.

```python
subject = headers.get("subject", "").lower()
found_words = [word for word in SUSPICIOUS_WORDS if word in subject]
if found_words:
    warnings.append("Subject has suspicious words: " + ", ".join(found_words))
```

`SUSPICIOUS_WORDS` is:

```python
["urgent", "verify", "password", "otp", "lottery",
 "prize", "winner", "click", "immediately"]
```

The subject `URGENT!!! Verify your account now to avoid closure` matches
`urgent` and `verify`.

```python
for url in re.findall(r"https?://[^\s]+", body):
    link_domain = url.split("//")[-1].split("/")[0].lower()
    if link_domain != from_domain:
        warnings.append(f"Body link '{url}' is not from the sender's domain")
```

Any URL in the body whose domain is not the sender's domain is flagged. The
sample contains `http://evil-scam.net/verify-login`, which is not
`fake-bank.com`.

### Actual output

```text
============================================================
                 EMAIL HEADER REPORT
============================================================
From       : "Secure Bank Alert" <support@fake-bank.com>
Reply-To   : helpdesk@evil-scam.net
To         : alice@receiver.com
Subject    : URGENT!!! Verify your account now to avoid closure
Date       : Fri, 17 Jul 2026 10:20:50 +0530
Message-ID : <9c1f2e3d@fake-bank.com>

Mail route (Received headers, newest first):
 - from mx.receiver.com (mx.receiver.com [198.51.100.10]) by inbox.receiver.com ...
 - from smtp.fake-bank.com (unknown [203.0.113.45]) by mx.receiver.com ...

Sender IP address : 203.0.113.45

Suspicious signs:
 [WARNING] Reply-To domain 'evil-scam.net' is different from From domain 'fake-bank.com' (possible spoofing)
 [WARNING] Subject has suspicious words: urgent, verify
 [WARNING] Body link 'http://evil-scam.net/verify-login' is not from the sender's domain

Verdict: this email looks like a phishing / suspicious mail.
```

### Why the checks work — and their limits

- A **display name** is not an identity. `"Secure Bank Alert"` is free text; the
  real address is `support@fake-bank.com`.
- A forged `From` header is easy, so `Reply-To` mismatches and authentication
  results (SPF/DKIM/DMARC) are stronger evidence.
- `Received` headers can also be forged by the sender's own server, so the
  oldest untrusted hop is the interesting one.
- This practical intentionally avoids network lookups. A real investigation
  would add reverse DNS, WHOIS, SPF/DKIM/DMARC verification, URL reputation and
  header-authentication results.

### Viva points

| Question | Short answer |
|---|---|
| Why is `Received` stored in a list? | It appears once per mail server; the full chain is needed. |
| Which `Received` line is oldest? | The last one in the file, because each server prepends its line. |
| Why compare `Reply-To` and `From` domains? | A mismatch is a common phishing/spoofing signal. |
| Why `partition(":")` instead of `split(":")`? | Header values such as `Message-ID` contain colons; only the first colon separates name and value. |
| What does `line[:1] in (" ", "\t")` handle? | Folded/continuation lines of a long header. |

---

## CSDF Practical 2 — CAPTCHA generation and verification

**Folder:** `CSDF/Practical2_CAPTCHA/`
**Main file:** `captcha.py`
**Output:** `captcha.png`

### Aim

Generate a CAPTCHA image containing random characters and visual noise, then
verify the text entered by the user.

### What a CAPTCHA is

CAPTCHA stands for **Completely Automated Public Turing test to tell Computers
and Humans Apart**. The idea is to create a challenge that is easy for a human
to solve but hard for a bot. This practical uses a **text CAPTCHA**:

- random uppercase letters and digits,
- characters drawn at random vertical positions and in random dark colours,
- random lines and dots as noise,
- three verification attempts.

### Code walkthrough

#### 1. Constants and font loading

```python
WIDTH, HEIGHT = 250, 90
LENGTH = 5                        # number of characters in the CAPTCHA
OUTPUT = Path(__file__).parent / "captcha.png"

def load_font(size):
    """Use a normal font if it exists on the system, else Pillow's default font."""
    for path in ("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()
```

The font fallback makes the script portable: on systems without DejaVu it still
runs using Pillow's built-in bitmap font.

#### 2. Drawing the CAPTCHA

```python
def generate_captcha(text):
    """Draw the given text on an image with random noise and save it."""
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    font = load_font(42)
    x = 15

    for char in text:
        # random dark colour and small random position for each character
        colour = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        y = random.randint(5, 30)
        draw.text((x, y), char, font=font, fill=colour)
        x += 45
```

Each character gets:

- a random **dark** RGB colour in the range 0–100 (dark text on white),
- a random vertical offset between 5 and 30 pixels,
- a fixed horizontal step of 45 pixels.

This alone would be easy for OCR, so noise is added:

```python
    # noise: random lines and dots so that a bot cannot read the text easily
    for _ in range(6):
        draw.line((random.randint(0, WIDTH), random.randint(0, HEIGHT),
                   random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                  fill=(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)),
                  width=2)
    for _ in range(300):
        draw.point((random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                   fill=(random.randint(120, 200),) * 3)

    image.save(OUTPUT)
```

- 6 random lines cross the image,
- 300 random light-grey dots add pixel noise,
- the result is saved to `captcha.png` next to the script.

#### 3. Verification

```python
def verify(expected, answer):
    """Check the text typed by the user (ignore case and extra spaces)."""
    return answer.strip().upper() == expected.upper()
```

Verification is deliberately forgiving about case and surrounding whitespace.
This is a usability choice: users should not fail because of capitalisation.

#### 4. Main loop

```python
def main():
    text = "".join(random.choices(string.ascii_uppercase + string.digits, k=LENGTH))
    generate_captcha(text)

    for attempt in range(1, 4):
        answer = input(f"Attempt {attempt}/3 - enter the CAPTCHA text: ")
        if verify(text, answer):
            print("Verification successful! You are a human.")
            return
        print("Wrong CAPTCHA.")

    print("Verification failed. The correct text was:", text)
```

`random.choices(..., k=5)` chooses five characters **with replacement**, so a
character can repeat. The user gets three attempts; after that the correct text
is revealed (useful for a classroom demo, not for production).

### Output

The text is random on every run. A sample run where dummy answers `TEST` were
supplied:

```text
CAPTCHA image saved as: .../CSDF/Practical2_CAPTCHA/captcha.png
Attempt 1/3 - enter the CAPTCHA text: Wrong CAPTCHA.
Attempt 2/3 - enter the CAPTCHA text: Wrong CAPTCHA.
Attempt 3/3 - enter the CAPTCHA text: Wrong CAPTCHA.
Verification failed. The correct text was: QK06Q
```

With the actual generated text typed correctly:

```text
Attempt 1/3 - enter the CAPTCHA text: Verification successful! You are a human.
```

### Security discussion

This is an **educational** CAPTCHA. Real systems improve on it with:

- distorted/warped text and overlapping characters,
- a larger character set and exclusion of ambiguous characters (`O/0`, `I/1`),
- background textures that resist segmentation,
- rate limiting and short expiry times,
- audio alternatives for accessibility,
- modern risk-based challenges instead of a single image test.

The important concept is the asymmetry: generating and storing the answer is
easy for the server, recognising the noisy image is hard for a generic bot.

### Viva points

| Question | Short answer |
|---|---|
| Expand CAPTCHA. | Completely Automated Public Turing test to tell Computers and Humans Apart. |
| Why add lines and dots? | To break character segmentation and defeat simple OCR. |
| Why is verification case-insensitive? | Better usability; the answer is still checked exactly otherwise. |
| Where is the answer stored? | In the Python variable `text`, not inside the image. |
| What limits brute force? | Only three attempts in this demo; production systems add rate limits and expiry. |

---

## CSDF Practical 3 — WiFi intrusion detection

**Folder:** `CSDF/Practical3_WiFi_Intrusion_Detection/`
**Main file:** `wifi_intrusion_detection.py`
**Input:** `wifi_log.txt`

### Aim

Read an access-point log, detect a device that is trying many passwords
(a brute-force / password-cracking attempt), and block that device from the
network, protecting a resource such as an IP printer.

### Log format

Each line has exactly four whitespace-separated fields:

```text
time                 MAC address          IP address      status
10:00:05  AA:BB:CC:DD:EE:99  192.168.1.55  FAIL
10:00:30  AA:BB:CC:DD:EE:77  192.168.1.60  SUCCESS
```

The sample log contains:

- trusted devices `...:01` and `...:02` (whitelist),
- attacker `...:99` with six consecutive failures,
- device `...:77` with one failure followed by a success.

### Detection policy

| Rule | Value |
|---|---|
| Maximum allowed failures before blocking | `MAX_FAILED_ATTEMPTS = 5` |
| Whitelisted MACs | `AA:BB:CC:DD:EE:01`, `AA:BB:CC:DD:EE:02` |
| Action on the 5th failure | print an alert and block the MAC |
| Subsequent attempts from a blocked MAC | rejected, even if the password is correct |

### Code walkthrough

#### 1. Constants and state

```python
MAX_FAILED_ATTEMPTS = 5
WHITELIST = {"AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02"}

failed_attempts = {}   # mac -> number of failed logins
blocked = set()        # devices that are now blocked
```

- `failed_attempts` is a dictionary because each MAC has its own counter.
- `blocked` is a set because membership tests (`mac in blocked`) are O(1) and
  duplicates do not matter.

#### 2. Reading the log

```python
for line in LOG_FILE.read_text().splitlines():
    parts = line.split()
    if len(parts) != 4:
        continue
    time, mac, ip, status = parts
```

Malformed lines are skipped defensively. This is important in real log
processing: logs may contain comments, blank lines or partial writes.

#### 3. Whitelist and already-blocked checks

```python
    if mac in WHITELIST:
        continue                 # trusted device, nothing to check

    if mac in blocked:
        print(f"{time}  [REJECTED] {mac} is blocked - access denied again")
        continue
```

Whitelisting prevents false positives for known infrastructure devices (the
printer itself, an admin laptop, etc.). The second check ensures a blocked
device stays blocked even if it later presents the correct password.

#### 4. Counting failures and raising the alert

```python
    if status == "FAIL":
        failed_attempts[mac] = failed_attempts.get(mac, 0) + 1
        print(f"{time}  failed login from {mac} ({ip}), "
              f"total failures = {failed_attempts[mac]}")

        if failed_attempts[mac] >= MAX_FAILED_ATTEMPTS:
            blocked.add(mac)
            print(f"{time}  [ALERT] {mac} is trying to crack the WiFi password!")
            print(f"{time}  [ACTION] Access denied - {mac} blocked from the "
                  f"network (IP Printer protected)\n")
```

The counter is incremented **before** the threshold test, so the fifth failure
triggers the block. `>=` rather than `==` also means the block is not missed if
the threshold is changed or a log line is processed twice.

#### 5. Summary

```python
print("----- Summary -----")
print("Failed login attempts :", failed_attempts)
print("Blocked devices       :", blocked if blocked else "none")
print("Trusted devices       :", sorted(WHITELIST))
```

`blocked if blocked else "none"` prints a readable message for the empty-set
case instead of `set()`.

### Actual output

```text
Monitoring WiFi access point log: wifi_log.txt

10:00:05  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 1
10:00:07  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 2
10:00:09  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 3
10:00:11  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 4
10:00:13  failed login from AA:BB:CC:DD:EE:99 (192.168.1.55), total failures = 5
10:00:13  [ALERT] AA:BB:CC:DD:EE:99 is trying to crack the WiFi password!
10:00:13  [ACTION] Access denied - AA:BB:CC:DD:EE:99 blocked from the network (IP Printer protected)

10:00:15  [REJECTED] AA:BB:CC:DD:EE:99 is blocked - access denied again
10:00:25  failed login from AA:BB:CC:DD:EE:77 (192.168.1.60), total failures = 1
----- Summary -----
Failed login attempts : {'AA:BB:CC:DD:EE:99': 5, 'AA:BB:CC:DD:EE:77': 1}
Blocked devices       : {'AA:BB:CC:DD:EE:99'}
Trusted devices       : ['AA:BB:CC:DD:EE:01', 'AA:BB:CC:DD:EE:02']
```

Observations:

- `...:99` reaches five failures and is blocked.
- The sixth failure at `10:00:15` is rejected without increasing the counter.
- `...:77` is not blocked because it had only one failure and then succeeded.
- Whitelisted devices never appear in the failure summary.

### Limitations and realistic extensions

- The log is a **static file**; a production IDS reads a live stream.
- MAC addresses can be spoofed. Real systems combine MAC, IP, 802.1X identity
  and behaviour over time.
- Five failures in a row is a simple threshold. Better detectors use a **time
  window** (e.g. 5 failures within 60 seconds), per-AP baselines, and alerts
  rather than automatic blocking.
- Blocking should be reversible and audited; false positives can disconnect
  legitimate users.
- A real implementation would integrate with the access point's firewall
  (`iptables`, `nftables`, hostapd deny list) rather than only printing.

### Viva points

| Question | Short answer |
|---|---|
| Why use a dictionary for failures? | It maps each MAC to its own count. |
| Why use a set for blocked devices? | Fast membership test and automatic de-duplication. |
| When exactly is a device blocked? | On the fifth failed attempt (`>= 5`). |
| Why are whitelisted devices skipped? | Trusted infrastructure should never be auto-blocked. |
| What is the attack called? | Brute-force / dictionary attack on the WiFi password. |

---

## CSDF Mini Project — Digital image forensics tool

**Folder:** `CSDF/MiniProject_Image_Forensics/`
**Main file:** `image_forensics.py` (~1400 lines)
**Helpers:** `make_samples.py`, `run_demo.sh`, `requirements.txt`

### Aim

Design a tool that examines a suspect image the way a digital forensics
examiner would:

1. prove the evidence file was not changed (cryptographic hashes),
2. recover hidden metadata (camera, software, timestamps, GPS),
3. detect and localise regions that were spliced, cloned or retouched,
4. compare a suspect image with a known original,
5. write a self-contained HTML + JSON report.

The original evidence file is **never modified**.

### Architecture

```text
image_forensics.py
│
├── analyze(path)                       main pipeline for one image
│   ├── describe_file()                 SHA-256, MD5, size, format, entropy
│   ├── extract_metadata()              EXIF, GPS, editor signatures, flags
│   ├── dhash()                         perceptual fingerprint
│   ├── error_level_analysis()          JPEG re-compression residual
│   ├── block_stats()                   mean/variance per 16x16 block
│   ├── evaluate_blocks()               robust z-score + regions
│   ├── Laplacian filter + block_stats()  noise inconsistency
│   ├── fuse_anomalies()                ELA AND noise agreement map
│   ├── tamper_suspicion_score()        weighted 0-100 heuristic
│   └── write_reports()                 report.json + report.html + images
│
├── compare_images(a, b)                dHash + SHA-256 comparison
├── print_console(result)               formatted console report
├── write_json_report()                 machine-readable output
├── write_html_report()                 standalone report with base64 images
└── run_demo()                          self-test with synthetic evidence
```

`make_samples.py` creates three synthetic images:

| File | What it is |
|---|---|
| `original.jpg` | clean "camera" JPEG with EXIF + GPS |
| `tampered.jpg` | same scene after a grass patch was replaced, re-compressed, saved with GIMP metadata and no camera info |
| `copy_resized.jpg` | original resized and re-saved, used to test dHash |

`ground_truth.json` stores the known manipulated rectangle
`(560, 445, 760, 560)`.

### The mathematics

#### 1. Chain of custody: cryptographic hashes

```text
SHA-256(file) = 256-bit digest
MD5(file)     = 128-bit digest
```

Any change of a single byte changes the digest completely. Recording the hash
before analysis proves the evidence was not altered afterwards.

#### 2. Byte entropy

```text
H = -Σ p(i) · log₂ p(i),   i = 0…255
```

`p(i)` is the fraction of bytes equal to `i`. A JPEG typically has high entropy
(close to 8 bits/byte) because compressed data looks random. A very low entropy
can indicate padding or a simple/blank file.

#### 3. Error Level Analysis (ELA)

```text
I_q(x, y) = JPEG(I(x, y), quality = q)          re-compressed image
E(x, y)   = | I(x, y) - I_q(x, y) | * s         error level
```

A JPEG saved once has a small, fairly uniform error. A pasted/cloned region has
a different compression history, so its error level differs from its
neighbours. The residual is amplified by `s` (default 15) so humans can see it.

Each 16×16 block `B` is tested with a **robust z-score**:

```text
z_E(B) = 0.6745 · ( mean(E over B) − median(mean(E)) ) / MAD(mean(E))
```

where `MAD` is the median absolute deviation. A block is flagged when
`|z_E(B)| > threshold` (default 3.5).

#### 4. Noise inconsistency (Laplacian variance)

```text
L(x, y) = I(x−1,y) + I(x+1,y) + I(x,y−1) + I(x,y+1) − 4·I(x, y)
Var(B)  = (1/n) · Σ ( L(x,y) − mean_B )²
z_N(B)  = 0.6745 · ( Var(B) − median(Var) ) / MAD(Var)
```

The Laplacian is a second-derivative edge detector: it responds strongly to
fine detail and noise. A blurred or cloned region has less noise; a noisy
spliced region has more. Either way, its block variance becomes an outlier.

#### 5. Agreement map

```text
A(B) = ELA_flag(B) AND Noise_flag(B)
```

A block is marked as **strongly suspicious** only when both independent tests
flag it. Ordinary edges may trigger one test, but a real splice usually
disturbs both compression and noise, so the AND rule reduces false positives.

#### 6. Perceptual hash (dHash)

```text
H(i, j) = 1 if I(i, j) < I(i, j+1) else 0
distance(H1, H2) = population count of (H1 XOR H2)
similarity = 100 · (1 − distance / 64)
```

The image is converted to grayscale and resized to 9×8. Each of the 64 bits
records whether a pixel is darker than its right neighbour. This survives
resizing and re-saving, unlike a cryptographic hash.

#### 7. Final suspicion score

```text
S = 100 · (0.25·ELA + 0.25·Noise + 0.30·Localisation + 0.20·Metadata)
```

Each component is normalised to `0…1`:

| Component | Normalisation |
|---|---|
| ELA | `min(1, anomaly_fraction / 0.10)` |
| Noise | `min(1, anomaly_fraction / 0.10)` |
| Localisation | largest connected region blocks / `max(10, 4% of blocks)` |
| Metadata | `min(1, number_of_flags / 3)` |

| Score | Level | Meaning |
|---|---|---|
| 0–30 | **LOW** | no strong forensic indicator |
| 31–60 | **MEDIUM** | some anomalies; closer inspection recommended |
| 61–100 | **HIGH** | strong indicators of manipulation |

This is a **heuristic**, not proof.

### Code walkthrough

#### 1. File identity and chain of custody

```python
def sha256_file(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()
```

The file is read in 1 MiB chunks, so even large evidence files do not need to
fit in memory. `md5_file()` is identical apart from the algorithm.

```python
def byte_entropy(path, limit=4_000_000):
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
```

`describe_file()` combines the hashes with:

- absolute path,
- file size (bytes and human-readable),
- image format and mode,
- width, height and megapixels,
- number of frames (animated formats),
- byte entropy.

#### 2. Metadata forensics

```python
def extract_metadata(image, path):
    exif = image.getexif()
    ...
    for tag_id, value in exif.items():
        name = ExifTags.TAGS.get(tag_id, str(tag_id))
        exif_data[name] = _to_text(value)
```

Pillow exposes EXIF tags by numeric ID. `ExifTags.TAGS` maps IDs such as
`0x010F` to names such as `Make`. Some tags (`DateTimeOriginal`) live in a
**sub-IFD**, so the code also reads IFD `0x8769`:

```python
exif_ifd = _read_ifd(exif, 0x8769)
```

GPS data is in IFD `0x8825`:

```python
gps_ifd = _read_ifd(exif, 0x8825)
latitude  = _gps_component(gps_ifd.get(2))
longitude = _gps_component(gps_ifd.get(4))
```

GPS values can be a single number or a `(degrees, minutes, seconds)` triple.
`_gps_component()` converts DMS to decimal degrees:

```python
degrees + minutes / 60.0 + seconds / 3600.0
```

The hemisphere reference (tags 1 and 3) flips the sign for south/west:

```python
if str(gps_ifd.get(1, "N")).upper().startswith("S"):
    latitude = -latitude
if str(gps_ifd.get(3, "E")).upper().startswith("W"):
    longitude = -longitude
```

Editor signatures are searched in the **raw bytes** of the first 2 MB, not only
in EXIF, because names can hide in XMP packets or embedded thumbnails:

```python
def scan_editor_signatures(path, limit=2_000_000):
    data = path.read_bytes()[:limit].lower()
    return [marker for marker in EDITOR_MARKERS
            if marker.encode("ascii", "ignore") in data]
```

`EDITOR_MARKERS` includes Photoshop, GIMP, Lightroom, Snapseed, Picsart,
Canva, Facetune, FaceApp, Paint.NET, Pixelmator, Affinity Photo, ACDSee,
Picasa, Inkscape, Krita, Photopea, Meitu, YouCam and VSCO.

Metadata findings (`flags`) include:

| Code | Trigger |
|---|---|
| `editing-software` | an editor signature was found |
| `missing-camera-info` | EXIF exists but has no Make/Model |
| `missing-exif` | no EXIF at all |
| `timestamp-mismatch` | `DateTime` differs from `DateTimeOriginal` |

GPS presence and the `Software` tag are recorded as notes.

#### 3. Error Level Analysis

```python
def error_level_analysis(rgb, quality, scale):
    buffer = io.BytesIO()
    rgb.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    with Image.open(buffer) as recompressed:
        recompressed = recompressed.convert("RGB")

    difference = ImageChops.difference(rgb, recompressed).convert("L")
    histogram = difference.histogram()
    total = sum(histogram) or 1

    mean = sum(i * count for i, count in enumerate(histogram)) / total
    variance = sum(count * (i - mean) ** 2
                   for i, count in enumerate(histogram)) / total
    std = math.sqrt(variance)
    maximum = max(i for i, count in enumerate(histogram) if count)
    threshold = mean + 3.0 * std
    hot_pixels = sum(count for i, count in enumerate(histogram) if i > threshold)
    ...
    amplified = difference.point(lambda value: min(255, int(value * scale)))
```

Why save to `BytesIO`? It re-compresses the image **in memory** without writing
a temporary file. The difference is converted to 8-bit grayscale, then
statistics are computed from its 256-bin histogram. The amplified image is a
visual heatmap; the numbers are used for the actual decision.

#### 4. Block statistics

```python
def block_stats(data, width, height, block):
    stats = []
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
            stats.append({"x": x0, "y": y0, "mean": mean,
                          "var": variance if variance > 0 else 0.0})
    return stats
```

This is the computational core: every non-overlapping 16×16 block gets a mean
and a variance. The variance shortcut

```text
Var = E[X²] − (E[X])²
```

avoids a second pass over the block.

#### 5. Robust outliers and connected regions

```python
def robust_outliers(values, threshold):
    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)

    if mad > 1e-9:
        scores = [0.6745 * (value - median) / mad for value in values]
    else:
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        scores = [(value - median) / std for value in values] if std > 1e-9 else [0.0] * len(values)

    flags = [abs(score) > threshold for score in scores]
    return flags, scores, median, mad
```

Median and MAD are used instead of mean and standard deviation because a few
extreme blocks would inflate the mean/std and hide themselves. The constant
`0.6745` makes the MAD-based score comparable to a standard z-score for normal
data. If MAD is zero, the code falls back to standard deviation, then to zeros.

```python
def merge_regions(blocks, block_size):
    cells = {(b["x"] // block_size, b["y"] // block_size): b for b in blocks}
    ...
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            neighbour = (cell_x + dx, cell_y + dy)
            ...
```

Adjacent flagged blocks are merged with an **8-neighbour flood fill**. This
turns a scatter of flagged squares into connected bounding boxes, which are
much easier to interpret: a real edit usually forms one compact region.

#### 6. Agreement map

```python
def fuse_anomalies(ela_blocks, noise_blocks, block_size):
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
    ...
```

Both maps use the same block grid, so blocks can be matched by `(x, y)`.
`z` is the weaker of the two scores (the evidence is only as strong as the
weaker test); `strength` is the sum and is used to rank the top blocks.

#### 7. dHash and comparison

```python
def dhash(image, hash_size=8):
    gray = image.convert("L").resize((hash_size + 1, hash_size), LANCZOS)
    pixels = gray.tobytes()          # 8-bit grayscale: one byte per pixel
    bits = 0
    for row in range(hash_size):
        for column in range(hash_size):
            left = pixels[row * (hash_size + 1) + column]
            right = pixels[row * (hash_size + 1) + column + 1]
            bits = (bits << 1) | (1 if left < right else 0)
    return bits
```

Why resize to **9×8**? Each row needs 9 pixels to produce 8 comparisons.
The result is a 64-bit integer, printed as 16 hexadecimal digits.

```python
def hamming_distance(first, second):
    return bin(first ^ second).count("1")
```

`XOR` marks differing bits; `count("1")` counts them.

Comparison verdicts:

| Condition | Verdict |
|---|---|
| same SHA-256 | `IDENTICAL FILE (same SHA-256)` |
| similarity ≥ 95% | `VERY LIKELY THE SAME IMAGE (re-saved or resized)` |
| similarity ≥ 85% | `SIMILAR IMAGE (possible edit, crop or compression)` |
| otherwise | `DIFFERENT IMAGES` |

#### 8. Suspicion score

```python
ela_component = min(1.0, ela["anomaly_fraction"] / 0.10)
noise_component = min(1.0, noise["anomaly_fraction"] / 0.10)
localisation_component = min(
    1.0,
    localization["largest_region_blocks"] / localization["reference_blocks"],
)
metadata_component = min(1.0, len(metadata["flags"]) / 3.0)

score = round(100 * (0.25 * ela_component + 0.25 * noise_component +
                     0.30 * localisation_component + 0.20 * metadata_component))
```

The localisation component gets the highest weight (0.30) because a single
compact anomalous region is stronger evidence than scattered edge artefacts.

#### 9. The `analyze()` pipeline

```python
with Image.open(path) as image:
    image.load()
    file_info = describe_file(path, image)
    metadata = extract_metadata(image, path)
    rgb_full = image.convert("RGB")
    perceptual_hash = dhash(rgb_full)
    analysis_rgb, preview_factor, preview_note = fit_for_analysis(rgb_full, max_side)
```

- `image.load()` forces decoding while the file handle is open.
- `convert("RGB")` normalises grayscale, CMYK, palette and RGBA images.
- `fit_for_analysis()` downscales only if the longest side exceeds 1400 px, so
  the analysis stays fast. The scale factor is recorded in the report.
- The original file itself is never written to.

Then the two maps, the agreement map, the score, the artifact images and the
reports are produced. Artifacts include:

```text
original_view.jpg
ela_heatmap.png
ela_overlay.jpg
noise_heatmap.png
noise_overlay.jpg
agreement_overlay.jpg
report.json
report.html
```

`report.html` embeds the images as base64 data URIs, so it is a **single
self-contained file** that can be submitted or emailed.

#### 10. Demo / self-test

```python
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
```

`localised` checks whether any detected region with at least 8 blocks overlaps
the known ground-truth rectangle (scaled to the analysis preview).

### Actual results from the generated reports

| Measure | `original.jpg` | `tampered.jpg` |
|---|---|---|
| Tamper score | **25 / 100 — LOW** | **64 / 100 — HIGH** |
| Metadata flags | none | `editing-software` (GIMP), `missing-camera-info` |
| ELA flagged blocks | 49 / 2072 (2.365%) | 49 / 2072 (2.365%) |
| Noise flagged blocks | 81 / 2072 (3.909%) | 148 / 2072 (7.143%) |
| Agreement blocks | 19 / 2072 (0.917%) | 19 / 2072 (0.917%) |
| Score components | ELA 0.2365, Noise 0.3909, Loc 0.3012, Meta 0.0 | ELA 0.2365, Noise 0.7143, Loc 0.9036, Meta 0.6667 |

The tampered image jumps from LOW to HIGH because:

- its metadata carries a GIMP signature and no camera information,
- its localisation component is high (a large connected anomaly region),
- its noise component is high (the pasted patch has a different noise level).

dHash comparison of `original.jpg` and `copy_resized.jpg`:

```text
dHash original  : 9a8a963c17d52891
dHash resized   : 9a8a963c17d52c50
Hamming distance: 4 / 64 bits
Similarity      : 93.75%
Verdict         : SIMILAR IMAGE (possible edit, crop or compression)
```

A 4-bit difference out of 64 after resizing from 900×600 to 495×330 shows why
perceptual hashing is used for "same picture?" questions instead of SHA-256.

Run the self-test with:

```bash
python3 CSDF/MiniProject_Image_Forensics/image_forensics.py --demo
# or, if Pillow is not on the system Python:
CSDF/MiniProject_Image_Forensics/run_demo.sh
```

Expected self-test:

```text
  [PASS] Exact hashes differ between original and tampered
  [PASS] Metadata flags appear on tampered copy
  [PASS] Tampered copy has a higher risk score
  [PASS] Re-saved copy still matches the original (dHash >= 85%)
  [PASS] Tampered region localised by ELA/noise region analysis

  Checks passed : 5 / 5
```

### CLI options

| Option | Meaning |
|---|---|
| `IMAGE` | image to analyse (default: `sample_images/tampered.jpg` if present) |
| `-o, --output DIR` | output directory |
| `-q, --quality Q` | JPEG quality for ELA re-compression (default 90) |
| `-s, --scale S` | ELA amplification (default 15) |
| `-b, --block B` | block size in pixels (default 16) |
| `-z, --z-threshold Z` | robust z-score threshold (default 3.5) |
| `--max-side N` | downscale for very large images (default 1400) |
| `--compare IMAGE2` | compare with a second image using dHash |
| `--demo` | generate samples and run the self-test |
| `--json` | also print the full JSON report |
| `--version`, `--help` | version/help |

### Limitations

- ELA and noise analysis are **heuristic**; a high score is a reason to look
  closer, not proof of tampering.
- ELA is weaker for PNG/BMP/TIFF because those formats are not JPEG
  block-compressed.
- Social-media re-compression can create or hide ELA artifacts.
- A resize or heavy crop can defeat dHash matching.
- Always preserve the original, record its hash before analysis, and work on a
  copy (chain of custody).
- No single forensic test is conclusive; correlate with metadata, hashes,
  source evidence and other tools.

### Viva points

| Question | Short answer |
|---|---|
| Why SHA-256 and MD5 both? | SHA-256 is the strong integrity proof; MD5 is kept for compatibility/reference. |
| What does ELA actually compare? | Original pixels vs the same pixels re-compressed at quality `q`. |
| Why median/MAD instead of mean/std? | They are robust to a few extreme blocks. |
| Why merge blocks into regions? | A real edit forms a compact area; isolated flags are usually edges/noise. |
| Why AND the two maps? | To reduce false positives; both tests must agree. |
| Why does dHash survive resizing? | It compares relative brightness of neighbouring pixels, not exact pixel values. |
| What is chain of custody? | Documented, tamper-evident handling of evidence; here, hashes + untouched original. |

---

# PART B — Information Retrieval (IR)

---

## IR Practical 1 — Document similarity

**Folder:** `IR/Practical1_Document_Similarity/`
**Main file:** `document_similarity.py`
**Inputs:** `doc1.txt`, `doc2.txt`

### Aim

Read two text documents and measure how similar they are using **cosine
similarity** of their word-frequency vectors.

### Theory: bag of words and cosine similarity

Each document is converted into a vector over the vocabulary. If the vocabulary
is `{cricket, sport, ball, …}`, then:

```text
doc1 = (count of cricket, count of sport, count of ball, …)
doc2 = (count of cricket, count of sport, count of ball, …)
```

The **cosine similarity** is the cosine of the angle between the two vectors:

```text
                 Σ (w1i · w2i)
sim(d1, d2) = ─────────────────────────
              ‖w1‖ · ‖w2‖
```

where

```text
‖w‖ = sqrt(Σ wi²)
```

Properties:

- `1.0` → vectors point in the same direction (identical word distribution),
- `0.0` → no shared words (orthogonal),
- the value is independent of document length, because the denominator
  normalises both vectors.

### Code walkthrough

#### 1. Tokenisation

```python
def words_in(document):
    """Return the list of words in a document (lowercase, punctuation removed)."""
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in document)
    return cleaned.split()
```

Every alphanumeric character is kept and lower-cased; everything else becomes
a space. This removes punctuation and line breaks without needing a regex.
`split()` then collapses runs of spaces.

#### 2. Word counts

```python
count1 = Counter(words1)      # word -> how many times it appears
count2 = Counter(words2)
```

A `Counter` is a dictionary specialised for counting. It gives O(1) average
lookup for the dot product.

#### 3. Cosine similarity

```python
def cosine_similarity(count1, count2):
    common_words = set(count1) & set(count2)      # words present in both

    dot_product = sum(count1[word] * count2[word] for word in common_words)
    length1 = math.sqrt(sum(count * count for count in count1.values()))
    length2 = math.sqrt(sum(count * count for count in count2.values()))

    if length1 == 0 or length2 == 0:
        return 0.0
    return dot_product / (length1 * length2)
```

Only words present in **both** documents contribute to the dot product, so the
loop iterates over the intersection. The zero-length guard prevents division by
zero for empty documents.

#### 4. Verdict

```python
if similarity > 0.8:
    print("Result: the two documents are very similar")
elif similarity > 0.4:
    print("Result: the two documents are somewhat similar")
else:
    print("Result: the two documents are different")
```

The thresholds are arbitrary but reasonable for a classroom demo:
`> 0.8` very similar, `> 0.4` somewhat similar, otherwise different.

### Actual output

Both documents are about cricket and share most of their vocabulary.

```text
Document 1 : doc1.txt - 58 words
Document 2 : doc2.txt - 52 words
Common words : 34 -> a, and, ball, between, by, countries, cricket, eleven,
hitting, in, is, many, match, matches, more, of, on, played, players, running,
runs, score, sport, stadiums, team, teams, television, the, to, two, watching,
wickets, wins, with

Cosine similarity = 0.8820  (88.20 %)
Result: the two documents are very similar
```

### Interpretation

34 words occur in both documents. Even though the documents are 58 and 52
words long and use slightly different wording (`popular` vs `famous`,
`Each team tries` vs `The players try`), the frequency vectors point in almost
the same direction. `0.8820 > 0.80`, so the program reports "very similar".

### Limitations

- **No semantics**: "car" and "automobile" are treated as unrelated.
- **No word order**: "dog bites man" and "man bites dog" are identical.
- **Stopwords dominate**: `the`, `is`, `and` contribute heavily unless removed
  or weighted (TF-IDF).
- **Length normalisation is only via the denominator**; a long document that
  repeats one word many times can still score oddly.
- Better IR systems use stemming/lemmatisation, stopword removal, TF-IDF or
  BM25, and sentence embeddings.

### Viva points

| Question | Short answer |
|---|---|
| Why cosine and not Euclidean distance? | Cosine is length-independent and measures orientation, which suits text counts. |
| What does 0 similarity mean? | The documents share no words (orthogonal vectors). |
| Why `Counter`? | Fast counting and O(1) frequency lookup. |
| What is the bag-of-words assumption? | Word order and grammar are ignored; only counts matter. |

---

## IR Practical 2 — PageRank

**Folder:** `IR/Practical2_PageRank/`
**Main file:** `pagerank.py`

### Aim

Compute the importance of web pages from their link structure using the
PageRank formula and display the ranking.

### Theory

PageRank models a **random surfer**:

- with probability `d` (the damping factor, usually `0.85`) the surfer follows a
  random outgoing link,
- with probability `1 − d` the surfer jumps to a random page.

The recursive formula is:

```text
PR(p) = (1 − d)/N + d · Σ  PR(q) / L(q)
                         q→p
```

where:

- `N` is the number of pages,
- `q → p` means page `q` links to page `p`,
- `L(q)` is the number of outgoing links from `q`,
- `(1 − d)/N` is the teleport term.

The `1/L(q)` factor means a page's vote is split equally among its outgoing
links. A page linked to by many important pages becomes important itself.

### Input graph

```text
A -> B, C
B -> C
C -> A
D -> C
```

Visualised:

```text
        ┌──────┐
        │  A   │
        └──┬───┘
        ┌──┴───┐
        ▼      ▼
      ┌───┐  ┌───┐
      │ B │  │ C │◄── D
      └─┬─┘  └─┬─┘
        └──────┘
             │
             ▼
             A
```

### Code walkthrough

#### 1. Parameters and graph

```python
DAMPING = 0.85      # chance that the user follows a link (d in the formula)
ITERATIONS = 50     # number of times the formula is applied

web_graph = {
    "A": ["B", "C"],
    "B": ["C"],
    "C": ["A"],
    "D": ["C"],
}
```

The graph is an adjacency list: each key is a page and each value is the list of
pages it links to.

#### 2. Initialisation

```python
pages = list(graph)
rank = {page: 1 / len(pages) for page in pages}
```

Every page starts with equal rank `1/N = 0.25`. This is the standard starting
point for the iterative algorithm.

#### 3. Iteration

```python
for _ in range(ITERATIONS):
    new_rank = {}
    for page in pages:
        votes = 0.0
        for other in pages:
            if page in graph[other]:
                votes += rank[other] / len(graph[other])
        new_rank[page] = (1 - DAMPING) / len(pages) + DAMPING * votes
    rank = new_rank
```

For each page:

1. scan every other page,
2. if that page links to the current page, add its rank divided by its
   out-degree,
3. apply the damping and teleport terms.

The update uses a **new dictionary**, not in-place updates. This is important:
in-place updates would mix old and new scores within the same iteration and
change the algorithm.

#### 4. Output

```python
for page, score in sorted(rank.items(), key=lambda item: -item[1]):
    print(f"  {page} : {score:.4f}")
best = max(rank, key=rank.get)
print(f"\nMost important page: {best}")
```

### Actual output

```text
Web graph (page -> links):
  A -> B, C
  B -> C
  C -> A
  D -> C

PageRank scores (higher = more important):
  C : 0.3941
  A : 0.3725
  B : 0.1958
  D : 0.0375

Most important page: C
```

### Why this ranking?

- **C** receives links from A, B and D, so it collects votes from three pages.
- **A** receives a link from C, which has the highest rank; the vote is not
  split because C has only one outgoing link.
- **B** receives a link from A, but A splits its vote between B and C, so B gets
  only half of A's contribution.
- **D** has no incoming links. Its score is exactly the teleport term:
  `(1 − 0.85)/4 = 0.15/4 = 0.0375`.

The scores sum to `1.0`, as PageRank is a probability distribution.

### Convergence and complexity

- `ITERATIONS = 50` is more than enough for this four-node graph. In practice,
  stop when the change between iterations is below a tolerance (e.g. `1e-6`).
- The code is `O(ITERATIONS × N²)` because for every page it scans every other
  page. Using an incoming-edge list would make it `O(ITERATIONS × (N + E))`.
- Dangling pages (no outgoing links) would divide by zero in a naive
  implementation. Here every page has at least one link, so the code does not
  hit that case. A robust implementation redistributes dangling rank or treats
  missing links as links to all pages.

### Viva points

| Question | Short answer |
|---|---|
| What is the damping factor? | Probability `d` that the surfer follows a link instead of teleporting; usually 0.85. |
| Why is PageRank iterative? | The formula is recursive; scores depend on other scores. |
| Why does C rank first? | It has the most incoming links from pages that pass rank. |
| Why does D score exactly 0.0375? | It has no incoming links, so only the teleport term remains. |
| What is a dangling node? | A page with no outgoing links; its rank must be redistributed. |

---

## IR Practical 3 — Map-Reduce alphabetic character count

**Folder:** `IR/Practical3_MapReduce_Character_Count/`
**Main file:** `map_reduce_char_count.py`
**Input:** `dataset.txt`

### Aim

Count how many times each letter A–Z appears in a dataset using the **Map,
Shuffle and Reduce** phases. Counting is case-insensitive and non-alphabetic
characters are ignored. The phases are implemented in Python, so no Hadoop
cluster is required.

### The Map-Reduce model

Map-Reduce is a distributed data-processing pattern with three conceptual
stages:

| Phase | Responsibility | In this practical |
|---|---|---|
| **Map** | Convert each input record into intermediate `(key, value)` pairs | `(letter, 1)` per alphabetic character |
| **Shuffle / Sort** | Group all values by key | `i -> [1, 1, 1, …]` |
| **Reduce** | Aggregate the values for each key | `i -> 8` |

The key idea is that **all values for the same key must reach the same
reducer**. That is what makes the aggregation correct in a distributed system.

### Input

```text
In 2026, Data Science & Information Retrieval are popular subjects!
Students love Python3, Hadoop, MapReduce, and Big-Data tools.
The quick brown fox jumps over the lazy dog -- 123 times.
```

### Code walkthrough

#### 1. Map

```python
def mapper(line):
    """Break a line into (letter, 1) pairs. Ignore non-letters, lowercase them."""
    for char in line:
        if char.isalpha():
            yield char.lower(), 1
```

This is a **generator**: it yields pairs one at a time instead of building a
list. `char.isalpha()` excludes digits, spaces and punctuation; `lower()`
merges `A` and `a`.

#### 2. Shuffle

```python
def shuffle(mapped_pairs):
    """Group all values that have the same key."""
    grouped = defaultdict(list)
    for key, value in mapped_pairs:
        grouped[key].append(value)
    return grouped
```

`defaultdict(list)` automatically creates an empty list for a new letter, so no
`if key not in grouped` check is needed. The result is:

```text
'i' -> [1, 1, 1, 1, 1, 1, 1, 1]
'e' -> [1, 1, 1, ...]
```

#### 3. Reduce

```python
def reducer(key, values):
    """Add the 1's for one letter."""
    return key, sum(values)
```

The reducer is intentionally trivial because the aggregation is a sum. In a
real Map-Reduce job this function could be any associative aggregation.

#### 4. Driver

```python
lines = DATASET.read_text().splitlines()

mapped = []
for line in lines:
    mapped.extend(mapper(line))

grouped = shuffle(mapped)

counts = {}
for key, values in sorted(grouped.items()):
    letter, count = reducer(key, values)
    counts[letter] = count
```

`mapped.extend(mapper(line))` consumes the generator into one flat list of
pairs. This is fine for a small dataset; a real cluster streams the pairs into
the shuffle phase.

### Actual output

```text
Alphabetic character count (case-insensitive):
  a : 12
  b : 3
  c : 5
  d : 7
  e : 14
  f : 2
  g : 2
  h : 4
  i : 8
  j : 2
  k : 1
  l : 5
  m : 4
  n : 8
  o : 13
  p : 6
  q : 1
  r : 8
  s : 8
  t : 12
  u : 6
  v : 3
  w : 1
  x : 1
  y : 2
  z : 1

Total letters: 139
```

### Interpretation

- `e` is the most frequent letter (14), followed by `o` (13), then `a` and `t`
  (12 each). This matches normal English letter frequency.
- Digits (`2026`, `3`, `123`), `&`, `!`, `,`, `-` and spaces are excluded.
- Upper- and lower-case letters are merged.
- The counts sum to **139**, the total number of alphabetic characters.

### Why Map-Reduce fits this problem

The count for each letter is independent, so the data can be split across many
machines:

```text
chunk 1 ── map ──► (e,1), (a,1), ...
chunk 2 ── map ──► (e,1), (t,1), ...
                         │
                    shuffle by key
                         │
          e -> [1,1,...] │ a -> [1,1,...]
                         │
                 reduce (sum)
                         │
                 e -> 14, a -> 12
```

Because addition is associative and commutative, the final result does not
depend on the chunk order.

### Viva points

| Question | Short answer |
|---|---|
| What does the mapper emit? | `(letter, 1)` for each alphabetic character. |
| What does the shuffle do? | Groups all values belonging to the same key. |
| What does the reducer do? | Sums the list of 1s for each letter. |
| Why is the result order-independent? | Addition is associative and commutative. |
| Why is `Counter` not used here? | The practical deliberately shows the three phases explicitly. |

---

## IR Practical 4 — Simple web crawler

**Folder:** `IR/Practical4_Web_Crawler/`
**Main file:** `web_crawler.py`
**Default start URL:** `https://quotes.toscrape.com/`

### Aim

Visit a website, follow the links found on its pages, and print every page
visited using **breadth-first search** with a depth limit and a page limit.

### Theory: crawling as graph traversal

The web is a directed graph:

- a page is a **node**,
- a hyperlink is a **directed edge**.

A crawler starts from a seed URL and explores the graph. Two common orders are:

| Order | Data structure | Behaviour |
|---|---|---|
| **BFS** | queue (FIFO) | visits all pages at depth 1, then depth 2, … |
| **DFS** | stack (LIFO) | goes deep along one path first |

This crawler uses BFS because it gives a broad view of the site near the start
page and respects the depth limit naturally.

### Important crawler rules implemented

1. **Stay on the same website**: only follow links whose `netloc` equals the
   start URL's `netloc`.
2. **Depth limit**: do not follow links beyond `MAX_DEPTH = 2`.
3. **Page limit**: stop after `MAX_PAGES = 5`.
4. **Visited set**: never visit the same URL twice (prevents loops).
5. **URL normalisation**: resolve relative links with `urljoin` and strip
   `#fragment` parts.
6. **Timeout and User-Agent**: `timeout=10` and `SimpleCrawler/1.0`, so the
   crawler does not hang forever and identifies itself.

### Code walkthrough

#### 1. Link extraction with `HTMLParser`

```python
class LinkFinder(HTMLParser):
    """Collect all href links from an HTML page."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)
```

`HTMLParser` is a standard-library, event-driven parser. `handle_starttag()` is
called for every opening tag; the class records `href` values only from `<a>`
tags. This avoids fragile regex-based HTML parsing.

#### 2. Downloading a page

```python
def get_page(url):
    request = Request(url, headers={"User-Agent": "SimpleCrawler/1.0"})
    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as error:
        print("  could not open", url, "->", error)
        return None
```

Errors are caught so one bad link does not stop the whole crawl. `errors="ignore"`
prevents a decode error from crashing on a non-UTF-8 page.

#### 3. BFS loop

```python
visited = set()             # pages already seen
queue = [(START_URL, 0)]    # (url, depth) pairs still to visit
start_domain = urlparse(START_URL).netloc

while queue and len(visited) < MAX_PAGES:
    url, depth = queue.pop(0)      # take the first url (BFS)

    if url in visited:
        continue
    visited.add(url)
    print(f"[{len(visited)}] visiting: {url}  (depth {depth})")

    html = get_page(url)
    if html is None:
        continue

    finder = LinkFinder()
    finder.feed(html)

    for link in finder.links:
        full_url = urljoin(url, link)          # relative -> full url
        full_url = full_url.split("#")[0]      # remove #section part

        if urlparse(full_url).netloc == start_domain and depth < MAX_DEPTH:
            if full_url not in visited:
                queue.append((full_url, depth + 1))
```

Step by step:

- `queue.pop(0)` implements FIFO. (`collections.deque` with `popleft()` would be
  more efficient for large crawls.)
- `visited.add(url)` happens **before** downloading. This prevents the same URL
  from being queued repeatedly, even if the download fails.
- `urljoin("https://site/a/", "b")` produces `https://site/a/b`; it also handles
  absolute links and protocol-relative links.
- Splitting on `#` removes in-page anchors, so `page#top` and `page` are treated
  as the same page.
- The `netloc` check keeps the crawler on one website.
- `depth < MAX_DEPTH` means links found at depth 2 are not followed further.

#### 4. Finish

```python
print("-" * 60)
print("Pages visited:", len(visited))
```

### Actual output

```text
Simple Web Crawler
Start URL : https://quotes.toscrape.com/
Max pages : 5
Max depth : 2
------------------------------------------------------------
[1] visiting: https://quotes.toscrape.com/  (depth 0)
[2] visiting: https://quotes.toscrape.com/login  (depth 1)
[3] visiting: https://quotes.toscrape.com/author/Albert-Einstein  (depth 1)
[4] visiting: https://quotes.toscrape.com/tag/change/page/1/  (depth 1)
[5] visiting: https://quotes.toscrape.com/tag/deep-thoughts/page/1/  (depth 1)
------------------------------------------------------------
Pages visited: 5
```

The exact pages depend on the site's current links and on network conditions.
The important behaviour is: home page at depth 0, its links at depth 1, and the
crawl stopping at five pages.

### Ethical and practical crawler rules

A production crawler must also:

- read and obey `robots.txt`,
- rate-limit requests (e.g. one request per second),
- set a descriptive User-Agent with contact information,
- handle HTTP status codes, redirects, content types and compressed responses,
- store content with metadata (URL, timestamp, hash),
- avoid login-protected or personal data unless authorised,
- respect copyright and the website's terms.

This demo crawler deliberately omits these to keep the code readable.

### Viva points

| Question | Short answer |
|---|---|
| BFS or DFS? | BFS, using a FIFO queue. |
| Why a `visited` set? | To avoid loops and duplicate pages. |
| Why `urljoin`? | To convert relative links into absolute URLs. |
| How is the depth limited? | Links are enqueued only when `depth < MAX_DEPTH`. |
| What is a seed URL? | The starting page of the crawl. |
| Why strip `#fragment`? | Different fragments point to the same page. |

---

## IR Practical 5 — XML web graph and topic-specific PageRank

**Folder:** `IR/Practical5_XML_WebGraph_Topic_PageRank/`
**Main file:** `xml_topic_pagerank.py`
**Input:** `webgraph.xml`
**Topic:** `sports`

### Aim

Parse an XML description of web pages and links, build the web graph, and rank
pages using **topic-specific (personalised) PageRank**, where the random surfer
always restarts on a page of the chosen topic.

### Input XML

```xml
<web>
  <page id="A" topic="news">
    <link to="B"/>
    <link to="C"/>
  </page>
  <page id="B" topic="sports">
    <link to="C"/>
    <link to="D"/>
  </page>
  <page id="C" topic="sports">
    <link to="A"/>
  </page>
  <page id="D" topic="sports">
    <link to="B"/>
    <link to="E"/>
  </page>
  <page id="E" topic="news">
    <link to="C"/>
  </page>
  <page id="F" topic="health">
    <link to="E"/>
    <link to="A"/>
  </page>
</web>
```

Parsed graph:

| Page | Outgoing links | Topic page? |
|---|---|:---:|
| A | B, C | No |
| B | C, D | **Yes** |
| C | A | **Yes** |
| D | B, E | **Yes** |
| E | C | No |
| F | E, A | No |

### Theory: topic-specific PageRank

Standard PageRank teleports uniformly to any page:

```text
PR(p) = (1 − d)/N + d · Σ PR(q)/L(q)
```

Topic-specific PageRank replaces the uniform teleport vector with a
**topic vector** `T(p)`:

```text
PR(p) = (1 − d)·T(p) + d · Σ PR(q)/L(q)
```

where

```text
T(p) = 1 / |topic_pages|   if p is a topic page
T(p) = 0                   otherwise
```

The random surfer who gets bored always restarts on a page about the chosen
topic. Pages in that topic therefore receive extra rank, and pages linked from
them benefit indirectly.

In this example:

- topic = `sports`,
- topic pages = `{B, C, D}`,
- `|topic_pages| = 3`,
- `T(B) = T(C) = T(D) = 1/3`,
- `T(A) = T(E) = T(F) = 0`.

### Code walkthrough

#### 1. Parsing the XML

```python
def build_web_graph(root):
    graph = {}
    topic_pages = set()

    for page in root.findall("page"):
        name = page.get("id")
        graph[name] = [link.get("to") for link in page.findall("link")]
        if page.get("topic") == TOPIC:
            topic_pages.add(name)

    return graph, topic_pages
```

`xml.etree.ElementTree.parse(...).getroot()` gives the `<web>` element.
`root.findall("page")` finds direct child pages; `page.findall("link")` finds
their direct link children. Attributes are read with `.get("id")`,
`.get("topic")` and `.get("to")`.

The function returns two structures:

- `graph`: adjacency list `page -> [outgoing pages]`,
- `topic_pages`: a set for O(1) membership tests.

#### 2. Building the teleport vector

```python
pages = list(graph)
teleport = {page: (1 / len(topic_pages) if page in topic_pages else 0)
            for page in pages}

rank = teleport.copy()       # start the surfer on the topic pages
```

The teleport vector sums to 1 because it is spread only over the topic pages.
Initialising `rank` to the teleport vector is a natural starting point: the
surfer begins on a topic page.

#### 3. Iteration

```python
for _ in range(ITERATIONS):
    new_rank = {}
    for page in pages:
        votes = 0.0
        for other in pages:
            out_links = graph[other]
            if out_links and page in out_links:
                votes += rank[other] / len(out_links)
        new_rank[page] = (1 - DAMPING) * teleport[page] + DAMPING * votes
    rank = new_rank
```

The only difference from standard PageRank is the teleport term:

```python
(1 - DAMPING) * teleport[page]
```

For a non-topic page this term is `0`, so its score comes entirely from incoming
links. The `if out_links` guard avoids division by zero for a dangling page.

#### 4. Printing the result

```python
for page, score in sorted(rank.items(), key=lambda item: -item[1]):
    mark = " <-- topic page" if page in topic_pages else ""
    print(f"  {page} : {score:.4f}{mark}")
```

### Actual output

```text
Web graph from webgraph.xml:
  A -> B, C
  B -> C, D  [topic page]
  C -> A  [topic page]
  D -> B, E  [topic page]
  E -> C
  F -> E, A

Topic: sports  (topic pages: B, C, D)

Topic specific PageRank (topic pages get a higher score):
  C : 0.3085 <-- topic page
  A : 0.2622
  B : 0.2230 <-- topic page
  D : 0.1448 <-- topic page
  E : 0.0615
  F : 0.0000
```

### Why this result?

- **C** is a topic page and receives links from A, B and E. It ranks first.
- **A** is not a topic page but receives a link from C (which has high rank) and
  from F. It ranks second.
- **B** is a topic page and receives links from A and D, but its outgoing links
  are split between C and D.
- **D** is a topic page and receives a link from B; its outgoing links go to B
  and E.
- **E** is not a topic page; it receives a link from D only.
- **F** has **no incoming links** and is **not** a topic page, so both terms of
  the formula are zero: `PR(F) = 0.0000`.

The topic pages B, C and D all receive teleport mass, but C still wins because
its link structure is stronger. This shows that topic-specific PageRank is not
simply "give every topic page the same score"; the link graph still matters.

### Standard vs topic-specific PageRank

| | Standard | Topic-specific |
|---|---|---|
| Teleport target | any page uniformly | only pages of the chosen topic |
| Teleport value | `(1−d)/N` for every page | `(1−d)/|topic|` for topic pages, 0 otherwise |
| Use case | global importance | "important **within this topic**" |

### Viva points

| Question | Short answer |
|---|---|
| What does the teleport vector do? | Decides where a bored surfer restarts. |
| Why do topic pages get extra rank? | The restart always lands on a topic page. |
| Why does F score 0? | No incoming links and not a topic page. |
| Which XML library is used? | `xml.etree.ElementTree`. |
| What is the difference from Practical 2? | The teleport term is restricted to the topic set. |

---

## IR Mini Project — Document summarization

**Folder:** `IR/MiniProject_Document_Summarization/`
**Main file:** `summarizer.py`
**Input:** `sample_document.txt`

### Aim

Build a document summarization system that produces an **extractive** summary:
it selects the most important sentences from the document itself rather than
writing new sentences. (Writing new text is *abstractive* summarization.)

### Pipeline

```text
raw text
   │
   ├─ split_sentences()        regex sentence boundary detection
   │
   ├─ clean_words()            lowercase, keep letters, remove stopwords
   │
   ├─ word_weights()           TF-IDF weight per word, normalised 0…1
   │
   ├─ sentence_scores()        average word weight + position bonus
   │
   ├─ select_sentences()       greedy top-N with Jaccard redundancy filter
   │
   └─ print_report() / output  summary in original sentence order
```

### Theory: TF-IDF sentence scoring

For a word `w`:

```text
TF(w)  = count(w) / most_common_count
IDF(w) = log( (1 + N_sentences) / (1 + sentences_with_w) ) + 1
weight(w) = TF(w) · IDF(w)
```

- **TF** rewards words that occur often in the document.
- **IDF** penalises words that occur in almost every sentence (they are not
  discriminative).
- The `+1` smoothing prevents division by zero and keeps IDF positive.
- Weights are then divided by the maximum weight, so every weight is in `0…1`.

Sentence score:

```text
score(s) = ( Σ weight(w) for w in s ) / |s|  ×  position_bonus(s)
position_bonus(s) = 1 + 0.15 · (1 − index / max(N−1, 1))
```

The average prevents long sentences from winning simply because they contain
more words. The position bonus reflects the journalistic convention that the
first sentences often carry the main idea.

### Redundancy removal

Two sentences are compared with **Jaccard similarity** on their cleaned word
sets:

```text
J(A, B) = |A ∩ B| / |A ∪ B|
```

If `J > 0.6`, the candidate is considered too similar to an already selected
sentence and is skipped. This avoids a summary that repeats the same fact in
different words.

### Code walkthrough

#### 1. Sentence splitting

```python
def split_sentences(text):
    text = " ".join(text.split())                       # remove extra spaces
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text)
    return [part.strip() for part in parts if part.strip()]
```

The regex uses:

- a **lookbehind** `(?<=[.!?])` — the previous character must be `.`, `!` or
  `?`,
- `\s+` — one or more whitespace characters,
- a **lookahead** `(?=[A-Z\"'(])` — the next character must be an uppercase
  letter, a quote, an apostrophe or an opening bracket.

The lookbehind/lookahead are zero-width, so the punctuation and the capital
letter stay in the sentence. `" ".join(text.split())` first collapses newlines
and multiple spaces, which makes the regex behaviour predictable.

#### 2. Cleaning words

```python
def clean_words(sentence):
    letters = "".join(char.lower() if char.isalpha() else " " for char in sentence)
    return [word for word in letters.split()
            if word not in STOPWORDS and len(word) > 1]
```

`STOPWORDS` contains common function words (`the`, `is`, `and`, `of`, …).
Single-letter words are also removed because they carry little meaning.

#### 3. TF-IDF weights

```python
def word_weights(sentence_words):
    counts = Counter()                    # word -> how many times in total
    sentences_with_word = Counter()       # word -> in how many sentences

    for words in sentence_words:
        counts.update(words)
        sentences_with_word.update(set(words))     # count once per sentence

    most_common = max(counts.values())
    total_sentences = len(sentence_words)

    weights = {}
    for word, count in counts.items():
        term_frequency = count / most_common
        inverse_document_frequency = math.log((1 + total_sentences) /
                                              (1 + sentences_with_word[word])) + 1
        weights[word] = term_frequency * inverse_document_frequency

    highest = max(weights.values())
    return {word: value / highest for word, value in weights.items()}
```

The `set(words)` is crucial: a word that appears five times in one sentence
should still count as appearing in **one** sentence for the document frequency.
Otherwise IDF would be distorted by repetition within a single sentence.

#### 4. Sentence scoring

```python
def sentence_scores(sentence_words, weights):
    scores = []
    total = len(sentence_words)

    for index, words in enumerate(sentence_words):
        if words:
            score = sum(weights.get(word, 0) for word in words) / len(words)
        else:
            score = 0
        position_bonus = 1 + POSITION_BONUS * (1 - index / max(total - 1, 1))
        scores.append(score * position_bonus)

    return scores
```

`max(total - 1, 1)` avoids division by zero for a one-sentence document. The
first sentence gets a multiplier of `1.15`, the last gets `1.0`.

#### 5. Selecting sentences

```python
def select_sentences(scores, sentence_words, number):
    best_first = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    picked, skipped = [], []

    for index in best_first:
        if len(picked) == number:
            break
        too_similar = any(similarity(sentence_words[index], sentence_words[other]) > REDUNDANCY_LIMIT
                          for other in picked)
        (skipped if too_similar else picked).append(index)

    # if too many were skipped, fill the remaining places with the best skipped ones
    for index in skipped:
        if len(picked) == number:
            break
        picked.append(index)

    picked.sort()               # summary keeps the original order of sentences
    return picked
```

- `best_first` sorts sentence indices by score, highest first.
- The loop greedily accepts a sentence unless it is too similar to one already
  picked.
- If the redundancy filter skipped too many candidates, the skipped sentences
  are added back in score order to reach the requested count.
- `picked.sort()` restores document order, so the summary reads naturally.

#### 6. Entry point

```python
def summarize(text, number=None, ratio=None):
    sentences = split_sentences(text)
    ...
    if number is None:
        number = DEFAULT_SENTENCES if ratio is None else max(1, round(len(sentences) * ratio))
    number = max(1, min(number, len(sentences)))

    sentence_words = [clean_words(sentence) for sentence in sentences]
    weights = word_weights(sentence_words)
    scores = sentence_scores(sentence_words, weights)
    picked = select_sentences(scores, sentence_words, number)

    return {
        "sentences": sentences,
        "summary": [sentences[index] for index in picked],
        "weights": weights,
        "scores": scores,
        "number": len(picked),
    }
```

The return value is a dictionary so the CLI, the report printer and tests can
all reuse the same computation. `number` is clamped to `[1, len(sentences)]`.

### CLI

```python
parser.add_argument("file", nargs="?", default=str(DEFAULT_DOCUMENT), metavar="FILE")
size = parser.add_mutually_exclusive_group()
size.add_argument("-n", "--sentences", type=int)
size.add_argument("-r", "--ratio", type=float)
parser.add_argument("-o", "--output", metavar="FILE")
parser.add_argument("-q", "--quiet", action="store_true")
parser.add_argument("-s", "--stats", action="store_true")
```

| Option | Meaning |
|---|---|
| `FILE` | text file to summarize (default: `sample_document.txt`) |
| `-n, --sentences N` | number of sentences in the summary (default: 3) |
| `-r, --ratio R` | summary size as a fraction, e.g. `0.3` |
| `-o, --output FILE` | save the summary to a file |
| `-q, --quiet` | print only the summary sentences |
| `-s, --stats` | show top keywords and sentence scores |
| `--version` | show the version |

`-n` and `-r` are in a **mutually exclusive group**, so the user cannot give
both at once. The code also validates that `-n >= 1` and `0 < ratio <= 1`.

### Actual output

The sample document has 12 sentences and 187 words. With the default
three-sentence summary:

```text
==============================================================
                DOCUMENT SUMMARIZATION REPORT
==============================================================
 Document       : sample_document.txt
 Original size  : 12 sentences, 187 words
 Summary length : 3 sentences (25% of the document)

----------------------- SUMMARY -----------------------
 1. ISRO has successfully launched its latest communication satellite into orbit from the Sriharikota space centre.
 2. The satellite, named GSAT-25, was carried by the heaviest rocket built by ISRO.
 3. The ISRO chairman said the successful launch of the satellite is an important step for the country's space programme.

 Summary size   : 47 words
 Compression    : 74.9% smaller than the original
```

With `--stats`:

```text
 Top keywords   : satellite (1.00), isro (0.75), launch (0.75), orbit (0.63),
                  space (0.63), gsat (0.63), communication (0.47), centre (0.47),
                  mission (0.47), internet (0.47)
 Sentence scores (higher = more important):
   sentence  1 : 0.582
   sentence  2 : 0.534
   sentence  8 : 0.505
   sentence  4 : 0.488
   sentence  5 : 0.486
```

The chosen sentences 1, 2 and 8 keep the main facts (launch, satellite name,
significance) in their original order. The summary is 47 words against 187,
i.e. **74.9% smaller**.

### Why the chosen sentences?

- `satellite` has the highest normalized TF-IDF weight (1.00) and appears in
  several key sentences.
- `isro` and `launch` are also strong keywords.
- Sentences 1 and 2 are early in the document (position bonus) and contain
  strong keywords.
- Sentence 8 also contains `satellite`, `launch`, `isro` and `space`, so it
  scores highly.
- Sentence 3 is about the launch event but does not rank in the top five; its
  words (launch, Friday, people, viewing gallery) are less discriminative, and
  the redundancy filter would also skip it if it were too similar to sentence 1.
- Sentences near the end score lower because of the position bonus and because
  they discuss secondary details (future missions, telemedicine).

### Limitations and future scope

- **Extractive only**: it cannot paraphrase or merge facts.
- Sentence splitting is regex-based; abbreviations (`Dr.`, `U.S.`) and decimals
  can confuse it.
- No stemming, so `satellite` and `satellites` are different words.
- TF-IDF is statistical; it does not understand meaning or entailment.
- No coreference resolution: "it" and "the satellite" are not linked.
- Future work: stemming/lemmatisation, sentence embeddings, graph-based
  TextRank, abstractive summarization with a language model, PDF/Word input,
  and a GUI.

### Viva points

| Question | Short answer |
|---|---|
| Extractive vs abstractive? | Extractive copies sentences; abstractive writes new text. |
| What does TF-IDF reward? | Frequent words that are rare across sentences. |
| Why average word weight? | To avoid favouring long sentences. |
| Why the position bonus? | Early sentences often carry the main idea. |
| How is redundancy removed? | Jaccard similarity > 0.6 against already picked sentences. |
| Why output in original order? | A summary should read coherently, not as a ranked list. |

---

# Cross-practical revision sheet

## 1. One-line summary of every practical

| Practical | Core idea | Key formula / rule | Actual key result |
|---|---|---|---|
| CSDF 1 — Email header | Parse headers, trace `Received`, find sender IP, detect phishing | domain mismatch / suspicious words / link domain | `203.0.113.45`, 3 warnings, phishing verdict |
| CSDF 2 — CAPTCHA | Generate noisy image, verify user text | `answer.strip().upper() == expected.upper()` | random 5-char text, 3 attempts |
| CSDF 3 — WiFi IDS | Count failures per MAC, block brute force | block when failures `>= 5` | `...:99` blocked after 5 failures |
| CSDF mini — Image forensics | Hashes, EXIF, ELA, noise, dHash, score | `S = 100(0.25E + 0.25N + 0.30L + 0.20M)` | original 25 LOW, tampered 64 HIGH |
| IR 1 — Document similarity | Cosine of word-count vectors | `sim = (w1·w2)/(‖w1‖‖w2‖)` | **0.8820 (88.20%)** very similar |
| IR 2 — PageRank | Random-surfer link analysis | `PR(p) = (1−d)/N + d Σ PR(q)/L(q)` | **C = 0.3941** |
| IR 3 — Map-Reduce | Count letters with map/shuffle/reduce | `(letter, 1)` → group → sum | **139** letters; `e` = 14 |
| IR 4 — Web crawler | BFS over hyperlinks | queue + visited + same domain + depth ≤ 2 | **5 pages** visited |
| IR 5 — Topic PageRank | Personalised teleport to topic pages | `PR(p) = (1−d)T(p) + d Σ PR(q)/L(q)` | **C = 0.3085** (sports) |
| IR mini — Summarizer | TF-IDF sentence ranking + redundancy filter | avg TF-IDF + position bonus, Jaccard ≤ 0.6 | 3 sentences, **74.9%** compression |

## 2. Which data structure is used where?

| Structure | Used in | Why |
|---|---|---|
| `dict` | email headers, PageRank ranks, WiFi counters | key → value lookup |
| `list` | `Received` headers, crawler queue, mapped pairs | ordered sequence |
| `set` | blocked MACs, visited URLs, topic pages, common words | fast membership + no duplicates |
| `Counter` | document similarity, summarizer | counting with O(1) lookup |
| `defaultdict(list)` | Map-Reduce shuffle | auto-create groups |
| `queue` via list `pop(0)` | crawler | BFS |
| XML tree | Practical 5 | parse nested page/link structure |

## 3. Complexity cheat sheet

| Practical | Time complexity | Space |
|---|---|---|
| Email parser | O(header size) | O(headers) |
| CAPTCHA | O(pixels + characters) | O(image) |
| WiFi IDS | O(number of log lines) | O(number of MACs) |
| Image forensics | O(pixels) for ELA/noise + O(blocks log blocks) for median | O(image + blocks) |
| Document similarity | O(words in both docs) | O(vocabulary) |
| PageRank | O(iterations × N²) in this code | O(N) |
| Map-Reduce count | O(number of characters) | O(alphabet) |
| Web crawler | O(pages visited × links per page) | O(visited URLs) |
| Topic PageRank | O(iterations × N²) | O(N) |
| Summarizer | O(sentences² × words) worst case for Jaccard comparisons | O(text) |

## 4. How the whole repository fits together

```text
                 ┌──────────────────────────────┐
                 │        run_all.sh            │
                 └──────────────┬───────────────┘
                                │
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
   CSDF practicals                             IR practicals
   ├─ 1 email header                           ├─ 1 cosine similarity
   ├─ 2 CAPTCHA                                ├─ 2 PageRank
   ├─ 3 WiFi IDS                               ├─ 3 Map-Reduce
   └─ mini: image forensics                    ├─ 4 web crawler
                                               ├─ 5 XML topic PageRank
                                               └─ mini: summarizer
```

All scripts are independent, but they share a common teaching progression:

1. **Parse a real-world format** — email headers, logs, XML, HTML, images.
2. **Turn it into a simple data structure** — dictionary, graph, list of
   blocks, word counts.
3. **Apply a well-known algorithm** — rule matching, cosine similarity,
   PageRank, Map-Reduce, BFS, TF-IDF.
4. **Present the result** — console report, ranking, blocked device, HTML/JSON
   report.

## 5. Common viva questions (short answers)

**CSDF**

1. **What is the difference between `From` and `Reply-To`?** `From` is the
   claimed sender; `Reply-To` is where replies are sent. A mismatch is a
   phishing signal.
2. **How do you find the sender IP in a header?** Take the IP from the oldest
   `Received` header (the last one in the file).
3. **Why is CAPTCHA case-insensitive here?** Usability; the answer is still
   random and limited to three attempts.
4. **What is a brute-force attack in the WiFi practical?** Repeated password
   guesses; the detector blocks after five failures.
5. **What does ELA measure?** The difference between the image and a
   re-compressed copy; edited regions often have a different error level.
6. **Why use median/MAD?** Robustness against extreme blocks.
7. **What is a perceptual hash?** A compact fingerprint of visual content that
   survives resizing/re-saving.
8. **What is chain of custody?** Documented, tamper-evident handling of
   evidence; hashes prove the file was not changed.

**IR**

1. **Why cosine similarity?** It is length-independent and measures the angle
   between word vectors.
2. **What is the damping factor in PageRank?** The probability of following a
   link (`0.85`), with `0.15` teleport probability.
3. **What is a dangling page?** A page with no outgoing links; its rank must be
   redistributed.
4. **What are the three Map-Reduce phases?** Map, shuffle/sort, reduce.
5. **Why BFS for the crawler?** It explores the site level by level and fits
   the depth limit.
6. **Why topic-specific PageRank?** The teleport vector is restricted to topic
   pages, so importance is measured within that topic.
7. **Extractive vs abstractive summarization?** Extractive selects existing
   sentences; abstractive generates new text.
8. **What does IDF mean?** Inverse document frequency: words appearing in many
   sentences are less discriminative.

## 6. Quick run checklist

```bash
# 1. CSDF
python3 CSDF/Practical1_Email_Header_Analysis/email_header_analysis.py
python3 CSDF/Practical2_CAPTCHA/captcha.py                 # needs Pillow; type the text
python3 CSDF/Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py
python3 CSDF/MiniProject_Image_Forensics/image_forensics.py --demo

# 2. IR
python3 IR/Practical1_Document_Similarity/document_similarity.py
python3 IR/Practical2_PageRank/pagerank.py
python3 IR/Practical3_MapReduce_Character_Count/map_reduce_char_count.py
python3 IR/Practical4_Web_Crawler/web_crawler.py           # needs internet
python3 IR/Practical5_XML_WebGraph_Topic_PageRank/xml_topic_pagerank.py
python3 IR/MiniProject_Document_Summarization/summarizer.py --stats

# 3. Everything
./run_all.sh
```

If Pillow is missing on the system Python, the image forensics wrapper can
create a local virtual environment automatically:

```bash
CSDF/MiniProject_Image_Forensics/run_demo.sh
```

## 7. Notes for the practical file / report

When writing up each practical, include:

1. **Aim** — one or two lines from the practical heading.
2. **Theory** — the formula or model used (cosine, PageRank, TF-IDF, ELA, …).
3. **Algorithm / flowchart** — the sequence of phases (parse → transform →
   score → output).
4. **Code** — the important function(s), not necessarily the entire file.
5. **Input and output** — include the sample input and the actual console
   output.
6. **Result / conclusion** — the key numeric result and what it means.
7. **Limitations** — show that you understand the assumptions and failure
   cases.

That structure is exactly how this guide is organised, so each section can be
condensed into a practical-file entry.
