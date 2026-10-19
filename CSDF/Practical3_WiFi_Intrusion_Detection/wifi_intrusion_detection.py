"""
Practical 3 : Detect WiFi password-cracking attempt and block the device
Aim         : Read the access point log, detect a device that is trying
              many passwords (brute force) to use the IP Printer resource
              and block that device from the network.
"""

from pathlib import Path

LOG_FILE = Path(__file__).parent / "wifi_log.txt"

MAX_FAILED_ATTEMPTS = 5                                        # allowed failures before blocking
WHITELIST = {"AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02"}         # known safe devices


def main():
    failed_attempts = {}   # mac -> number of failed logins
    blocked = set()        # devices that are now blocked

    print("Monitoring WiFi access point log:", LOG_FILE.name, "\n")

    for line in LOG_FILE.read_text().splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        time, mac, ip, status = parts

        if mac in WHITELIST:
            continue                 # trusted device, nothing to check

        if mac in blocked:
            print(f"{time}  [REJECTED] {mac} is blocked - access denied again")
            continue

        if status == "FAIL":
            failed_attempts[mac] = failed_attempts.get(mac, 0) + 1
            print(f"{time}  failed login from {mac} ({ip}), "
                  f"total failures = {failed_attempts[mac]}")

            if failed_attempts[mac] >= MAX_FAILED_ATTEMPTS:
                blocked.add(mac)
                print(f"{time}  [ALERT] {mac} is trying to crack the WiFi password!")
                print(f"{time}  [ACTION] Access denied - {mac} blocked from the "
                      f"network (IP Printer protected)\n")

    print("----- Summary -----")
    print("Failed login attempts :", failed_attempts)
    print("Blocked devices       :", blocked if blocked else "none")
    print("Trusted devices       :", sorted(WHITELIST))


if __name__ == "__main__":
    main()
