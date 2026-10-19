# CSDF Practicals (Cyber Security and Digital Forensics)

Practicals 1 to 3 of Group 1 (as per the LP-IV schedule). Mini-projects are skipped for now.

| No. | Practical | File |
|-----|-----------|------|
| 1 | Track emails and investigate email crimes (analyse email header) | `Practical1_Email_Header_Analysis/email_header_analysis.py` |
| 2 | Generate and verify CAPTCHA image | `Practical2_CAPTCHA/captcha.py` |
| 3 | Detect WiFi password-cracking attempt and block the device | `Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py` |

## How to run

```
python3 email_header_analysis.py
python3 captcha.py
python3 wifi_intrusion_detection.py
```

Or run all three at once from here: `../run_all.sh csdf`

- Practicals 1 and 3 use only Python's standard library.
- Practical 2 needs Pillow: `pip install pillow` (or install the system package `python-pillow`).
