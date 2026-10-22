# SEM-07 Practicals

Semester 7 (2026-27 BE Sem-I) practicals for **Laboratory Practice III** and
**Laboratory Practice IV**:

| Subject | Full form | Folder |
|---------|-----------|--------|
| LP3 | Laboratory Practice III — DAA and Machine Learning | [`LP3/`](LP3/) |
| CSDF | Cyber Security and Digital Forensics | [`CSDF/`](CSDF/) |
| IR | Information Retrieval | [`IR/`](IR/) |

Each subject folder has its own README with details on every practical.
For a single-file walkthrough of the CSDF and IR practicals — theory, code, and
outputs — see [`ALL_PRACTICALS_EXPLAINED.md`](ALL_PRACTICALS_EXPLAINED.md).

## Contents

| Subject | Practicals |
|---------|-----------|
| LP3 — DAA | 1. Fibonacci · 2. Huffman coding · 3. 0/1 Knapsack · 4. N-Queens · 5. Quick sort · Mini-project: Naive vs Rabin-Karp string matching |
| LP3 — ML | 1. Uber fare prediction · 2. Email spam classification · 3. Bank churn neural network · 4. Gradient descent · 5. K-Means clustering · Mini-project: Titanic survival prediction |
| CSDF | 1. Email header analysis · 2. CAPTCHA generation & verification · 3. WiFi intrusion detection · 4. Deleted file & partition recovery · 5. Log capture & event correlation · Mini-project: Digital image forensics tool |
| IR | 1. Document similarity · 2. PageRank · 3. Map-Reduce character count · 4. Web crawler · 5. XML web graph + topic PageRank · Mini-project: document summarization |

The LP-III Blockchain practicals (Group C) are intentionally not included;
[`LP3/`](LP3/) covers only the DAA and ML groups.

## How to run

### LP-III notebooks (DAA and ML)

The notebooks are already executed and saved with their outputs. Every
practical includes a **Detailed output explanation** cell that prints a guided
interpretation of the computed values. To regenerate and run them from the
jupytext sources:

```bash
./LP3/run_all.sh          # DAA + ML
./LP3/run_all.sh daa      # DAA only
./LP3/run_all.sh ml       # ML only
```

See [`LP3/README.md`](LP3/README.md) for the environment setup, dataset links
and notebook index. The notebooks need the packages in
[`LP3/requirements.txt`](LP3/requirements.txt).

### LP-IV scripts (CSDF and IR)

All scripts in one go:

```bash
./run_all.sh                # everything
./run_all.sh csdf           # CSDF practicals + image forensics mini-project
./run_all.sh csdf-project   # only the CSDF image forensics mini-project
./run_all.sh ir             # only IR practicals
./run_all.sh project        # only the IR mini-project
```

Or run any individual script directly, e.g.:

```bash
python3 CSDF/Practical1_Email_Header_Analysis/email_header_analysis.py
python3 CSDF/Practical4_Deleted_File_Partition_Recovery/forensic_recovery.py
python3 CSDF/Practical5_Log_Capture_Event_Correlation/log_capture_correlation.py
python3 CSDF/MiniProject_Image_Forensics/image_forensics.py --demo
```

The CSDF/IR scripts use the Python standard library only, except CSDF Practical
2 and the CSDF image forensics mini-project, which need Pillow.

## References

- [LP-III lab manual](<LP3/3. Signed BE Comp Sem-I LP-III Lab Manual 2026-27.pdf>)
- [2026-27 BE Sem-I LP-IV Schedule](<2026-27 BE Sem-I LP-IV Schedule.docx.pdf>)
