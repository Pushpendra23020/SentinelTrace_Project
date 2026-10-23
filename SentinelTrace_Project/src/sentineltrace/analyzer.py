"""Parsing, detection, correlation, and explainable reporting for SentinelTrace."""
from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from typing import Any
from urllib.parse import unquote_plus

from .rules import RULES, public_rule_catalogue

# Apache combined/common-style access records. The project intentionally limits
# support to documented formats rather than guessing at every possible log type.
ACCESS_LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) '
    r'(?P<path>\S+) HTTP/[0-9.]+" (?P<status>\d{3})(?:\s+\S+)?'
)
AUTH_LOG_RE = re.compile(
    r'^(?P<time>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*?'
    r'\bsshd(?:\[\d+\])?:\s+(?P<outcome>Failed password|Accepted (?:password|publickey)) '
    r'for (?:invalid user )?(?P<user>\S+) from (?P<ip>\S+)'
)

FAILED_LOGIN_THRESHOLD = 5
SENSITIVE_PATHS = ("/.env", "/wp-admin", "/phpmyadmin", "/.git", "/admin")
SQLI_RE = re.compile(
    r"(?:\bunion\s+(?:all\s+)?select\b|\bselect\b.+\bfrom\b|['\"]\s*(?:or|and)\s+['\"]?\d+\s*=\s*['\"]?\d+|\bsleep\s*\()",
    re.IGNORECASE,
)
COMMAND_RE = re.compile(
    r"(?:[;&|]\s*(?:curl|wget|bash|sh|nc|netcat)\b|&&\s*(?:whoami|id|uname)\b|`)",
    re.IGNORECASE,
)


def parse_log_line(line: str, line_number: int) -> dict[str, Any] | None:
    """Normalize one supported Apache or SSH log line, or return ``None``.

    The original line remains in process memory only; findings contain the
    minimum useful evidence rather than returning every raw record to the UI.
    """

    access = ACCESS_LOG_RE.match(line)
    if access:
        fields = access.groupdict()
        return {
            "index": line_number,
            "source": "web",
            "ip": fields["ip"],
            "time": fields["time"],
            "action": fields["method"],
            "path": fields["path"],
            "status": int(fields["status"]),
            "raw": line,
        }

    auth = AUTH_LOG_RE.match(line)
    if auth:
        fields = auth.groupdict()
        return {
            "index": line_number,
            "source": "auth",
            "ip": fields["ip"],
            "time": fields["time"],
            "action": "login",
            "outcome": "failed" if fields["outcome"].startswith("Failed") else "accepted",
            "user": fields["user"],
            "raw": line,
        }
    return None


def _decoded_path(path: str) -> str:
    """Decode one and double-encoded URL text for safe pattern comparison."""

    return unquote_plus(unquote_plus(path)).lower()


def _build_finding(rule_id: str, event: dict[str, Any], evidence: str) -> dict[str, Any]:
    rule = RULES[rule_id]
    return {
        "id": f"ST-{event['index']:04d}-{rule_id}",
        "rule": rule_id,
        "title": rule.title,
        "severity": rule.severity,
        "weight": rule.weight,
        "mitre": rule.mitre,
        "confidence": rule.confidence,
        "recommendation": rule.recommendation,
        "explanation": rule.description,
        "ip": event["ip"],
        "time": event["time"],
        "line": event["index"],
        "source": event["source"],
        "evidence": evidence,
    }


def _detect_findings(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply bounded, explainable rules to normalized events."""

    findings: list[dict[str, Any]] = []
    failed_by_ip: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scan_state: dict[str, dict[str, Any]] = {}

    for event in events:
        if event["source"] == "auth":
            if event["outcome"] == "failed":
                failed_by_ip[event["ip"]].append(event)
            elif len(failed_by_ip[event["ip"]]) >= FAILED_LOGIN_THRESHOLD:
                attempt_count = len(failed_by_ip[event["ip"]])
                findings.append(
                    _build_finding(
                        "LOGIN_AFTER_FAILURES",
                        event,
                        f"Accepted login for {event['user']} after {attempt_count} failed SSH password attempts from the same IP.",
                    )
                )
            continue

        path = event["path"]
        decoded = _decoded_path(path)
        if "../" in decoded:
            findings.append(_build_finding("PATH_TRAVERSAL", event, f"Suspicious request path: {path}"))
        if SQLI_RE.search(decoded):
            findings.append(_build_finding("SQLI_INDICATOR", event, f"Possible SQL-injection indicator in: {path}"))
        if COMMAND_RE.search(decoded):
            findings.append(_build_finding("COMMAND_INJECTION", event, f"Possible command-injection indicator in: {path}"))

        matching_paths = {marker for marker in SENSITIVE_PATHS if marker in decoded}
        if matching_paths:
            state = scan_state.setdefault(
                event["ip"], {"paths": set(), "first_event": event, "lines": []}
            )
            state["paths"].update(matching_paths)
            state["lines"].append(event["index"])

    for ip, attempts in failed_by_ip.items():
        if len(attempts) >= FAILED_LOGIN_THRESHOLD:
            findings.append(
                _build_finding(
                    "SSH_BRUTE_FORCE",
                    attempts[-1],
                    f"{len(attempts)} failed SSH password attempts from {ip} (threshold: {FAILED_LOGIN_THRESHOLD}).",
                )
            )
    for ip, state in scan_state.items():
        if len(state["paths"]) >= 3:
            paths = ", ".join(sorted(state["paths"]))
            lines = ", ".join(str(line) for line in state["lines"])
            findings.append(
                _build_finding(
                    "WEB_SCANNING",
                    state["first_event"],
                    f"Requested {len(state['paths'])} sensitive path families ({paths}); evidence lines: {lines}.",
                )
            )

    # Findings are a source-line timeline. IP prioritization is handled separately.
    return sorted(findings, key=lambda finding: (finding["line"], finding["rule"]))


def _risk_level(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _correlate(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group findings by source IP and sum each rule category once.

    Deduplicating a repeated rule avoids inflating risk simply because a noisy
    scanner repeated the same request. The returned breakdown makes the score
    directly traceable in a viva.
    """

    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"rule_weights": {}, "finding_ids": [], "first_line": None}
    )
    for finding in findings:
        entity = grouped[finding["ip"]]
        entity["rule_weights"].setdefault(finding["rule"], finding["weight"])
        entity["finding_ids"].append(finding["id"])
        if entity["first_line"] is None or finding["line"] < entity["first_line"]:
            entity["first_line"] = finding["line"]

    entities = []
    for ip, data in grouped.items():
        score = min(100, sum(data["rule_weights"].values()))
        breakdown = [
            {"rule": rule, "weight": weight}
            for rule, weight in sorted(data["rule_weights"].items())
        ]
        entities.append(
            {
                "ip": ip,
                "risk": score,
                "risk_level": _risk_level(score),
                "rules": [item["rule"] for item in breakdown],
                "risk_breakdown": breakdown,
                "finding_count": len(data["finding_ids"]),
                "first_evidence_line": data["first_line"],
            }
        )
    return sorted(entities, key=lambda entity: (-entity["risk"], entity["ip"]))


def analyze_logs(log_text: str) -> dict[str, Any]:
    """Create a JSON-ready explainable incident report from authorized log text."""

    if not isinstance(log_text, str):
        raise TypeError("log_text must be a string")

    lines = log_text.splitlines()
    events = [
        event
        for line_number, line in enumerate(lines, start=1)
        if (event := parse_log_line(line, line_number)) is not None
    ]
    findings = _detect_findings(events)
    entities = _correlate(findings)
    source_counts = Counter(event["source"] for event in events)
    severity_counts = {severity: 0 for severity in ("critical", "high", "medium", "low")}
    severity_counts.update(Counter(finding["severity"] for finding in findings))

    return {
        "analysis_id": hashlib.sha256(log_text.encode("utf-8")).hexdigest()[:16],
        "engine": "SentinelTrace explainable rule engine v3",
        "input_summary": {
            "total_lines": len(lines),
            "parsed_events": len(events),
            "ignored_lines": len(lines) - len(events),
            "web_events": source_counts["web"],
            "auth_events": source_counts["auth"],
        },
        "findings": findings,
        "entities": entities,
        "severity_counts": severity_counts,
        "triggered_rules": sorted({finding["rule"] for finding in findings}),
        "rules": public_rule_catalogue(),
        "risk_model": {
            "formula": "For each source IP, add each triggered rule weight once and cap the total at 100.",
            "levels": {"critical": "75-100", "high": "50-74", "medium": "25-49", "low": "0-24"},
        },
        "limitations": [
            "Indicator matches require analyst validation and are not proof of compromise.",
            "The risk score is a transparent prioritization heuristic, not a probability of compromise.",
            "Only the documented Apache-style and SSH password log formats are supported in this prototype.",
        ],
    }
