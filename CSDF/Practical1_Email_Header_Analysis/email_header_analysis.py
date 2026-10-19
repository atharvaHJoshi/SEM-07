"""
Practical 1 : Tracking Emails and Investigating Email Crimes
Aim         : Analyse an email header, show the path the mail travelled,
              find the sender's IP address and detect suspicious signs
              such as spoofing and phishing links.
"""

import re
from pathlib import Path

EMAIL_FILE = Path(__file__).parent / "sample_email.txt"
SUSPICIOUS_WORDS = ["urgent", "verify", "password", "otp", "lottery",
                    "prize", "winner", "click", "immediately"]


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


def main():
    headers, received, body = parse_email(EMAIL_FILE.read_text())

    print("=" * 60)
    print("                 EMAIL HEADER REPORT")
    print("=" * 60)
    print("From       :", headers.get("from", "-"))
    print("Reply-To   :", headers.get("reply-to", "-"))
    print("To         :", headers.get("to", "-"))
    print("Subject    :", headers.get("subject", "-"))
    print("Date       :", headers.get("date", "-"))
    print("Message-ID :", headers.get("message-id", "-"))

    print("\nMail route (Received headers, newest first):")
    for hop in received:
        print(" -", hop)

    # Sender IP = IP found in the oldest (last) Received header
    ips = []
    for hop in received:
        match = re.search(r"\[(\d{1,3}(?:\.\d{1,3}){3})\]", hop)
        if match:
            ips.append(match.group(1))
    print("\nSender IP address :", ips[-1] if ips else "not found")

    # ---------------- checks for suspicious signs ----------------
    warnings = []
    from_address = headers.get("from", "")
    from_domain = from_address.split("@")[-1].rstrip(">").lower()
    reply_domain = headers.get("reply-to", "").split("@")[-1].lower()

    if reply_domain and reply_domain != from_domain:
        warnings.append(f"Reply-To domain '{reply_domain}' is different from "
                        f"From domain '{from_domain}' (possible spoofing)")

    subject = headers.get("subject", "").lower()
    found_words = [word for word in SUSPICIOUS_WORDS if word in subject]
    if found_words:
        warnings.append("Subject has suspicious words: " + ", ".join(found_words))

    for url in re.findall(r"https?://[^\s]+", body):
        link_domain = url.split("//")[-1].split("/")[0].lower()
        if link_domain != from_domain:
            warnings.append(f"Body link '{url}' is not from the sender's domain")

    print("\nSuspicious signs:")
    if warnings:
        for warning in warnings:
            print(" [WARNING]", warning)
        print("\nVerdict: this email looks like a phishing / suspicious mail.")
    else:
        print(" none")
        print("\nVerdict: the email headers look normal.")


if __name__ == "__main__":
    main()
