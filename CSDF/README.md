# CSDF Practicals (Cyber Security and Digital Forensics)

Practicals 1 to 3 of Group 1 (as per the LP-IV schedule) and the CSDF mini
project.

| No. | Practical | File |
|-----|-----------|------|
| 1 | Track emails and investigate email crimes (analyse email header) | `Practical1_Email_Header_Analysis/email_header_analysis.py` |
| 2 | Generate and verify CAPTCHA image | `Practical2_CAPTCHA/captcha.py` |
| 3 | Detect WiFi password-cracking attempt and block the device | `Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py` |
| Mini-project | Digital image forensics tool (hashes, EXIF/GPS, ELA, noise analysis, dHash comparison, HTML report) | `MiniProject_Image_Forensics/image_forensics.py` |

## How to run

```
python3 Practical1_Email_Header_Analysis/email_header_analysis.py
python3 Practical2_CAPTCHA/captcha.py
python3 Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py

# mini project: generate sample images and run the self-test
python3 MiniProject_Image_Forensics/image_forensics.py --demo
```

Or run all of them from the repository root: `../run_all.sh csdf`
(or `../run_all.sh csdf-project` for only the mini project).

## Dependencies

- Practicals 1 and 3 use only Python's standard library.
- Practical 2 needs Pillow: `pip install pillow`.
- The image forensics mini project also needs Pillow:
  `python3 -m pip install -r MiniProject_Image_Forensics/requirements.txt`.

See `MiniProject_Image_Forensics/README.md` for the full documentation, the
mathematical formulas, sample output and usage options.
