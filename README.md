# SEM-07 Practicals

Semester 7 (2026-27 BE Sem-I) LP-IV practicals, covering two subjects:

| Subject | Full form | Folder |
|---------|-----------|--------|
| CSDF | Cyber Security and Digital Forensics | [`CSDF/`](CSDF/) |
| IR | Information Retrieval | [`IR/`](IR/) |

Each subject folder has its own README with details on every practical.

## Contents

| Subject | Practicals |
|---------|-----------|
| CSDF | 1. Email header analysis · 2. CAPTCHA generation & verification · 3. WiFi intrusion detection |
| IR | 1. Document similarity · 2. PageRank · 3. Map-Reduce character count · 4. Web crawler · 5. XML web graph + topic PageRank · Mini-project: document summarization |

## How to run

All practicals in one go:

```bash
./run_all.sh          # everything
./run_all.sh csdf     # only CSDF
./run_all.sh ir       # only IR
./run_all.sh project  # only the IR mini-project
```

Or run any individual script directly, e.g.:

```bash
python3 CSDF/Practical1_Email_Header_Analysis/email_header_analysis.py
```

Requirements: Python 3 (standard library only, except CSDF Practical 2 which needs Pillow).

Reference: [2026-27 BE Sem-I LP-IV Schedule](<2026-27 BE Sem-I LP-IV Schedule.docx.pdf>)
