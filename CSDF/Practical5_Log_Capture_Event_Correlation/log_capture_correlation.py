"""
Practical 5 : Log capturing and event correlation
Aim         : Capture logs from several sources (authentication, firewall and
              web server), normalise every entry into one common event format,
              detect suspicious activities with correlation rules and merge
              related alerts into a single incident with a timeline.

Pipeline:
    collect  ->  parse/normalise  ->  detect  ->  correlate  ->  report

The demo uses three static logs so the output is reproducible.  A production
system would replace the file reader with syslog/rsyslog, journald, Wazuh or
a SIEM collector, but the normalisation and correlation stages stay the same.

Usage:
    python3 log_capture_correlation.py
    python3 log_capture_correlation.py --logs other_logs --output out
"""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
LOGS_DIR = HERE / "logs"
OUTPUT_DIR = HERE / "output"

# All syslog timestamps in the sample have no year or time zone; the exercise
# assumes UTC and a fixed year so that the three sources share one timeline.
LOG_YEAR = 2026

# Thresholds for the detection rules.
PORT_SCAN_THRESHOLD = 5
PORT_SCAN_WINDOW = 60                 # seconds
BRUTE_FORCE_THRESHOLD = 3
BRUTE_FORCE_WINDOW = 120              # seconds
WEB_SCAN_THRESHOLD = 3
WEB_SCAN_WINDOW = 120                 # seconds
CORRELATION_WINDOW = 15 * 60          # 15 minutes

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
SEVERITY_SCORE = {"LOW": 5, "MEDIUM": 15, "HIGH": 30, "CRITICAL": 40}

RULES = [
    {"id": "PORT_SCAN",
     "rule": f">= {PORT_SCAN_THRESHOLD} denied destination ports from one IP "
             f"within {PORT_SCAN_WINDOW}s",
     "severity": "MEDIUM", "stage": "Reconnaissance",
     "mitre": "T1595 Active Scanning"},
    {"id": "SSH_BRUTE_FORCE",
     "rule": f">= {BRUTE_FORCE_THRESHOLD} failed SSH logins from one IP "
             f"within {BRUTE_FORCE_WINDOW}s",
     "severity": "HIGH", "stage": "Credential access",
     "mitre": "T1110 Brute Force"},
    {"id": "LOGIN_AFTER_FAILURES",
     "rule": "successful SSH login after repeated failures from the same IP",
     "severity": "CRITICAL", "stage": "Initial access",
     "mitre": "T1078 Valid Accounts"},
    {"id": "WEB_SCAN",
     "rule": f">= {WEB_SCAN_THRESHOLD} distinct 4xx web paths from one IP "
             f"within {WEB_SCAN_WINDOW}s",
     "severity": "MEDIUM", "stage": "Discovery",
     "mitre": "T1083 File and Directory Discovery"},
]


# =====================================================================
# 1. Parsing and normalisation
# =====================================================================

AUTH_LINE = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<process>[^:\[]+)(?:\[\d+\])?:\s+(?P<message>.*)$")
AUTH_FAILED = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) from "
    r"(?P<ip>\S+) port (?P<port>\d+)")
AUTH_SUCCESS = re.compile(
    r"Accepted password for (?P<user>\S+) from (?P<ip>\S+) port (?P<port>\d+)")
AUTH_SESSION = re.compile(r"session (?P<action>opened|closed) for user (?P<user>\S+)")

FIREWALL_LINE = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<host>\S+)\s+(?P<action>ALLOW|DENY)\s+"
    r"(?P<protocol>\S+)\s+(?P<src>\S+)\s+(?P<dst>\S+)\s+"
    r"(?P<src_port>\d+)\s+(?P<dst_port>\d+)$")

WEB_LINE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>[^ ]+) [^"]*" '
    r'(?P<status>\d{3}) (?P<size>\S+)(?: "(?P<referer>[^"]*)" "(?P<agent>[^"]*)")?')


def new_event(timestamp, source, event_type, **fields):
    """Create one normalised event (all sources share this schema)."""
    record = {
        "id": None,
        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "epoch": round(timestamp.timestamp(), 3),
        "source": source,
        "event": event_type,
        "src_ip": None,
        "user": None,
        "action": None,
        "method": None,
        "path": None,
        "status": None,
        "dst_ip": None,
        "dst_port": None,
        "raw": None,
    }
    record.update(fields)
    return record


def parse_auth(path):
    events = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        match = AUTH_LINE.match(line)
        if not match:
            continue
        timestamp = datetime.strptime(
            f"{LOG_YEAR} {match['timestamp']}", "%Y %b %d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        message = match["message"]
        process = match["process"].strip()
        common = {"host": match["host"], "raw": line, "line": number}

        failed = AUTH_FAILED.search(message)
        accepted = AUTH_SUCCESS.search(message)
        session = AUTH_SESSION.search(message)
        if failed:
            events.append(new_event(
                timestamp, "auth", "ssh_login_failure",
                src_ip=failed["ip"], user=failed["user"],
                status="FAIL", **common))
        elif accepted:
            events.append(new_event(
                timestamp, "auth", "ssh_login_success",
                src_ip=accepted["ip"], user=accepted["user"],
                status="SUCCESS", **common))
        elif session:
            prefix = "ssh" if process == "sshd" else "system"
            events.append(new_event(
                timestamp, "auth", f"{prefix}_session_{session['action']}",
                user=session["user"], action=session["action"].upper(),
                **common))
        else:
            events.append(new_event(
                timestamp, "auth", "system_message", **common))
    return events


def parse_firewall(path):
    events = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        match = FIREWALL_LINE.match(line)
        if not match:
            continue
        timestamp = datetime.fromisoformat(
            match["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
        action = match["action"]
        events.append(new_event(
            timestamp, "firewall",
            "firewall_deny" if action == "DENY" else "firewall_allow",
            src_ip=match["src"], dst_ip=match["dst"],
            dst_port=int(match["dst_port"]), action=action,
            host=match["host"], raw=line, line=number,
            protocol=match["protocol"], src_port=int(match["src_port"])))
    return events


def parse_web(path):
    events = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        match = WEB_LINE.match(line)
        if not match:
            continue
        timestamp = datetime.strptime(
            match["timestamp"], "%d/%b/%Y:%H:%M:%S %z").astimezone(timezone.utc)
        events.append(new_event(
            timestamp, "web", "web_request",
            src_ip=match["ip"], method=match["method"], path=match["path"],
            status=int(match["status"]), host="webserver",
            raw=line, line=number, user_agent=match["agent"]))
    return events


PARSERS = {
    "auth": parse_auth,
    "firewall": parse_firewall,
    "web": parse_web,
}


SOURCE_FILES = {
    "auth": "auth.log",
    "firewall": "firewall.log",
    "web": "web_access.log",
}


def capture_logs(logs_dir):
    """Read every known log file, normalise and timestamp-order the events."""
    sources = []
    events = []
    for source, parser in PARSERS.items():
        path = logs_dir / SOURCE_FILES[source]
        if not path.exists():
            print(f"  [WARN] missing log source: {path}")
            continue
        raw_bytes = path.read_bytes()
        raw_text = raw_bytes.decode("utf-8", errors="replace")
        source_events = parser(path)
        events.extend(source_events)
        sources.append({
            "source": source,
            "file": str(path.name),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "lines": len(raw_text.splitlines()),
            "events": len(source_events),
        })

    events.sort(key=lambda event: (event["epoch"], event["source"], event["line"]))
    for number, event in enumerate(events, start=1):
        event["id"] = f"EVT-{number:04d}"
    return events, sources


# =====================================================================
# 2. Detection rules
# =====================================================================

def group_by_ip(events):
    grouped = defaultdict(list)
    for event in events:
        if event["src_ip"]:
            grouped[event["src_ip"]].append(event)
    for values in grouped.values():
        values.sort(key=lambda event: event["epoch"])
    return grouped


def first_window(events, window_seconds, threshold, distinct_key=None):
    """Return the first time window that reaches the threshold.

    Using a sliding window (instead of counting the whole file) prevents old
    events from accumulating into a false positive.
    """
    for start in range(len(events)):
        window = [event for event in events[start:]
                  if event["epoch"] - events[start]["epoch"] <= window_seconds]
        count = (len({event[distinct_key] for event in window})
                 if distinct_key else len(window))
        if count >= threshold:
            return window
    return []


def make_alert(rule, src_ip, window, detail, extra_count=None, first=None):
    first = first or window[0]
    last = window[-1]
    severity = rule["severity"]
    return {
        "rule": rule["id"],
        "title": RULE_TITLES[rule["id"]],
        "src_ip": src_ip,
        "severity": severity,
        "score": SEVERITY_SCORE[severity],
        "stage": rule["stage"],
        "mitre": rule["mitre"],
        "count": extra_count if extra_count is not None else len(window),
        "first": first["epoch"],
        "last": last["epoch"],
        "first_time": first["timestamp"],
        "last_time": last["timestamp"],
        "detail": detail,
        "event_ids": [event["id"] for event in window],
    }


RULE_TITLES = {
    "PORT_SCAN": "Port scan / service probing",
    "SSH_BRUTE_FORCE": "SSH brute-force attempt",
    "LOGIN_AFTER_FAILURES": "Successful login after failed attempts",
    "WEB_SCAN": "Web application scanning",
}

RULE_BY_ID = {rule["id"]: rule for rule in RULES}


def detect_alerts(events):
    alerts = []
    groups = group_by_ip(events)

    # Rule 1 - port scan: one IP denied on many distinct ports.
    for ip, source_events in groups.items():
        denied = [event for event in source_events
                  if event["event"] == "firewall_deny"]
        window = first_window(denied, PORT_SCAN_WINDOW, PORT_SCAN_THRESHOLD,
                              distinct_key="dst_port")
        if window:
            ports = sorted({event["dst_port"] for event in window})
            alerts.append(make_alert(
                RULE_BY_ID["PORT_SCAN"], ip, window,
                f"{len(window)} denied connections to ports {ports}",
                extra_count=len(window)))

    # Rule 2 - SSH brute force: many failed logins from one IP.
    for ip, source_events in groups.items():
        failures = [event for event in source_events
                    if event["event"] == "ssh_login_failure"]
        window = first_window(failures, BRUTE_FORCE_WINDOW,
                              BRUTE_FORCE_THRESHOLD)
        if window:
            users = sorted({event["user"] for event in window})
            alerts.append(make_alert(
                RULE_BY_ID["SSH_BRUTE_FORCE"], ip, window,
                f"{len(window)} failed logins for users {users}"))

    # Rule 3 - success after failures: the attacker probably guessed a password.
    for ip, source_events in groups.items():
        failures = [event for event in source_events
                    if event["event"] == "ssh_login_failure"]
        successes = [event for event in source_events
                     if event["event"] == "ssh_login_success"]
        for success in successes:
            prior = [event for event in failures
                     if 0 <= success["epoch"] - event["epoch"] <= CORRELATION_WINDOW]
            if len(prior) >= BRUTE_FORCE_THRESHOLD:
                sequence = prior + [success]
                alerts.append(make_alert(
                    RULE_BY_ID["LOGIN_AFTER_FAILURES"], ip, sequence,
                    f"successful login as '{success['user']}' after "
                    f"{len(prior)} failed attempts",
                    extra_count=len(prior), first=success))
                break                       # one incident per successful account

    # Rule 4 - web scanning: many distinct error paths from one IP.
    for ip, source_events in groups.items():
        errors = [event for event in source_events
                  if event["event"] == "web_request" and event["status"] >= 400]
        window = first_window(errors, WEB_SCAN_WINDOW, WEB_SCAN_THRESHOLD,
                              distinct_key="path")
        if window:
            paths = sorted({event["path"] for event in window})
            alerts.append(make_alert(
                RULE_BY_ID["WEB_SCAN"], ip, window,
                f"{len(window)} error responses for paths {paths}"))

    alerts.sort(key=lambda alert: alert["first"])
    return alerts


# =====================================================================
# 3. Event correlation
# =====================================================================

def correlate(alerts, events):
    """Merge alerts from the same IP that fall inside one time window."""
    by_ip = defaultdict(list)
    for alert in alerts:
        by_ip[alert["src_ip"]].append(alert)

    incidents = []
    for ip, ip_alerts in sorted(by_ip.items(),
                                key=lambda item: item[1][0]["first"]):
        ip_alerts.sort(key=lambda alert: alert["first"])
        clusters = [[ip_alerts[0]]]
        for alert in ip_alerts[1:]:
            previous_end = max(item["last"] for item in clusters[-1])
            if alert["first"] - previous_end <= CORRELATION_WINDOW:
                clusters[-1].append(alert)
            else:
                clusters.append([alert])

        for cluster in clusters:
            start = min(alert["first"] for alert in cluster)
            end = max(alert["last"] for alert in cluster)
            severity = max((alert["severity"] for alert in cluster),
                           key=lambda value: SEVERITY_ORDER[value])
            alert_event_ids = {event_id for alert in cluster
                               for event_id in alert["event_ids"]}
            related = [event for event in events
                       if (event["src_ip"] == ip
                           and start <= event["epoch"] <= end)
                       or event["id"] in alert_event_ids]
            related.sort(key=lambda event: event["epoch"])
            stages = []
            for alert in cluster:
                if alert["stage"] not in stages:
                    stages.append(alert["stage"])

            if len(cluster) >= 3:
                title = f"Multi-stage intrusion from {ip}"
            elif len(cluster) == 2:
                title = f"Correlated suspicious activity from {ip}"
            else:
                title = f"{cluster[0]['title']} from {ip}"

            incidents.append({
                "id": f"INC-{len(incidents) + 1:03d}",
                "title": title,
                "src_ip": ip,
                "severity": severity,
                "score": min(100, sum(alert["score"] for alert in cluster)),
                "start": start,
                "end": end,
                "start_time": _time(start),
                "end_time": _time(end),
                "stages": stages,
                "alerts": cluster,
                "related_events": len(related),
                "event_ids": [event["id"] for event in related],
                "recommendations": _recommendations(cluster),
            })

    incidents.sort(key=lambda incident: (-incident["score"], incident["start"]))
    for number, incident in enumerate(incidents, start=1):
        incident["id"] = f"INC-{number:03d}"
    return incidents


def _recommendations(cluster):
    rules = {alert["rule"] for alert in cluster}
    actions = []
    if "PORT_SCAN" in rules:
        actions.append("Block the source IP at the perimeter firewall and "
                       "review which services are exposed.")
    if "SSH_BRUTE_FORCE" in rules:
        actions.append("Enable key-based SSH authentication, rate-limit failed "
                       "logins and deny the source IP.")
    if "LOGIN_AFTER_FAILURES" in rules:
        actions.append("Treat the host as compromised: reset the account "
                       "password, kill active sessions and collect volatile "
                       "evidence before rebooting.")
    if "WEB_SCAN" in rules:
        actions.append("Check the web server logs for any successful access to "
                       "the scanned paths and update the WAF rules.")
    actions.append("Preserve the original log files and the SHA-256 manifest "
                   "as evidence.")
    return actions


# =====================================================================
# 4. Reporting
# =====================================================================

def _time(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%H:%M:%S")


def _stamp(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def section(title):
    print()
    print("-" * 72)
    print(title)
    print("-" * 72)


def describe_event(event):
    """One-line human readable form of a normalised event."""
    parts = [event["id"], event["timestamp"], f"{event['source']:<9}",
             f"{event['event']:<20}"]
    if event["src_ip"]:
        parts.append(f"src={event['src_ip']}")
    if event["user"]:
        parts.append(f"user={event['user']}")
    if event["dst_port"]:
        parts.append(f"dport={event['dst_port']}")
    if event["path"]:
        parts.append(f"{event['method']} {event['path']} -> {event['status']}")
    return "  ".join(parts)


def write_outputs(events, sources, alerts, incidents, output_dir):
    output_dir.mkdir(exist_ok=True)
    for name in ("captured_events.jsonl", "log_manifest.json",
                 "correlation_report.json"):
        (output_dir / name).unlink(missing_ok=True)

    event_path = output_dir / "captured_events.jsonl"
    event_path.write_text("".join(json.dumps(event) + "\n" for event in events))

    manifest = {
        "tool": "LogCapture 1.0",
        "normalised_schema": [
            "id", "timestamp", "epoch", "source", "event", "src_ip", "user",
            "action", "method", "path", "status", "dst_ip", "dst_port", "raw",
        ],
        "sources": sources,
        "total_events": len(events),
    }
    manifest_path = output_dir / "log_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    report = {
        "manifest": str(manifest_path.name),
        "rules": RULES,
        "alerts": alerts,
        "incidents": incidents,
        "summary": {
            "events": len(events),
            "sources": len(sources),
            "alerts": len(alerts),
            "incidents": len(incidents),
            "critical_incidents": sum(
                1 for incident in incidents
                if incident["severity"] == "CRITICAL"),
        },
    }
    report_path = output_dir / "correlation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return event_path, manifest_path, report_path


def main():
    parser = argparse.ArgumentParser(
        description="Capture multi-source logs and correlate security events")
    parser.add_argument("--logs", type=Path, default=LOGS_DIR,
                        help="folder containing auth.log, firewall.log and "
                             "web_access.log (default: logs/)")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR,
                        help="folder for JSONL + JSON artefacts (default: output/)")
    args = parser.parse_args()

    print("=" * 72)
    print("           LOG CAPTURE AND EVENT CORRELATION REPORT")
    print("=" * 72)

    # -------------------------------------------------------------- capture
    section("[1] LOG CAPTURE")
    events, sources = capture_logs(args.logs)
    print(f"{'Source':<11}{'File':<20}{'Lines':>7}{'Events':>8}  SHA-256 (first 16)")
    for source in sources:
        print(f"{source['source']:<11}{source['file']:<20}"
              f"{source['lines']:>7}{source['events']:>8}  "
              f"{source['sha256'][:16]}")
    print(f"\nTotal normalised events: {len(events)}")

    # -------------------------------------------------------------- normalise
    section("[2] NORMALISED EVENT STREAM (first 8 events)")
    for event in events[:8]:
        print(" ", describe_event(event))
    print(f"  ... {len(events) - 8} more events, written to "
          f"{(args.output / 'captured_events.jsonl')}")

    # -------------------------------------------------------------- rules
    section("[3] DETECTION RULES")
    for number, rule in enumerate(RULES, start=1):
        print(f"  {number}. {rule['id']:<22} {rule['rule']}")
        print(f"     severity={rule['severity']:<9} stage={rule['stage']:<18} "
              f"MITRE={rule['mitre']}")

    # -------------------------------------------------------------- alerts
    alerts = detect_alerts(events)
    incidents = correlate(alerts, events)

    section("[4] CORRELATED ALERTS")
    print(f"{'Rule':<24}{'Source IP':<17}{'Count':>6}  "
          f"{'First':<9}{'Last':<9}Severity")
    for alert in alerts:
        print(f"{alert['rule']:<24}{alert['src_ip']:<17}{alert['count']:>6}  "
              f"{_time(alert['first']):<9}{_time(alert['last']):<9}"
              f"{alert['severity']}")
    if not alerts:
        print("  none")

    # -------------------------------------------------------------- incidents
    section("[5] CORRELATED INCIDENTS")
    if not incidents:
        print("  no incident required attention")
    for incident in incidents:
        print(f"{incident['id']}  {incident['severity']:<9} "
              f"score={incident['score']:>3}  source={incident['src_ip']}")
        print(f"  Title    : {incident['title']}")
        print(f"  Window   : {incident['start_time']} to {incident['end_time']} "
              f"({len(incident['alerts'])} alert(s), "
              f"{incident['related_events']} related events)")
        print(f"  Stages   : {' -> '.join(incident['stages'])}")
        print("  Timeline :")
        for alert in incident["alerts"]:
            print(f"    {_time(alert['first'])}  [{alert['severity']:<8}] "
                  f"{alert['rule']:<22} {alert['detail']}")
        print("  Actions  :")
        for action in incident["recommendations"]:
            print(f"    - {action}")
        print()

    # -------------------------------------------------------------- summary
    section("[6] SUMMARY")
    total_events = len(events)
    critical = sum(1 for incident in incidents
                   if incident["severity"] == "CRITICAL")
    top = max(incidents, key=lambda incident: incident["score"], default=None)
    print(f"Events captured          : {total_events}")
    print(f"Log sources              : {len(sources)}")
    print(f"Alerts raised            : {len(alerts)}")
    print(f"Correlated incidents     : {len(incidents)}")
    print(f"Critical incidents       : {critical}")
    if top:
        print(f"Highest risk source      : {top['src_ip']} "
              f"(score {top['score']}, {top['related_events']} events)")
    print(f"Event stream             : {args.output / 'captured_events.jsonl'}")
    print(f"Evidence manifest        : {args.output / 'log_manifest.json'}")
    print(f"Correlation report       : {args.output / 'correlation_report.json'}")
    print("\nEvery source hash is recorded before correlation, so a change to")
    print("the original log files after capture can be detected.")

    write_outputs(events, sources, alerts, incidents, args.output)


if __name__ == "__main__":
    main()
