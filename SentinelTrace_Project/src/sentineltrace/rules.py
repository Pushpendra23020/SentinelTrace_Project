"""The auditable rule catalogue used by SentinelTrace.

Each entry is deliberately small and documented so a student can explain how a
finding is produced and change a rule during an evaluation without hidden logic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RuleDefinition:
    """Metadata and response guidance for one detection rule."""

    title: str
    severity: str
    weight: int
    mitre: str
    confidence: str
    description: str
    recommendation: str


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

RULES: dict[str, RuleDefinition] = {
    "SSH_BRUTE_FORCE": RuleDefinition(
        title="Repeated SSH password failures",
        severity="high",
        weight=35,
        mitre="T1110.001",
        confidence="high",
        description="Five or more failed SSH password attempts came from the same source IP.",
        recommendation="Temporarily block the source IP and review SSH authentication controls.",
    ),
    "LOGIN_AFTER_FAILURES": RuleDefinition(
        title="SSH login after repeated failures",
        severity="critical",
        weight=45,
        mitre="T1078",
        confidence="medium",
        description="A successful SSH login followed repeated failed passwords from the same source IP.",
        recommendation="Validate the account owner, rotate credentials if needed, and review the session.",
    ),
    "PATH_TRAVERSAL": RuleDefinition(
        title="Path traversal indicator",
        severity="high",
        weight=25,
        mitre="T1190",
        confidence="medium",
        description="A request contained path-traversal notation such as ../ or an encoded equivalent.",
        recommendation="Inspect file-access validation and preserve related web-server logs.",
    ),
    "SQLI_INDICATOR": RuleDefinition(
        title="SQL-injection indicator",
        severity="high",
        weight=25,
        mitre="T1190",
        confidence="low",
        description="A request contained a common SQL-injection-like pattern. This is a triage signal, not proof of compromise.",
        recommendation="Review parameterized-query use and validate application and database logs.",
    ),
    "COMMAND_INJECTION": RuleDefinition(
        title="Command-injection indicator",
        severity="critical",
        weight=35,
        mitre="T1059",
        confidence="medium",
        description="A request contained a shell separator or shell-utility indicator.",
        recommendation="If confirmed, isolate the affected service and inspect process and proxy logs.",
    ),
    "WEB_SCANNING": RuleDefinition(
        title="Sensitive-path web scanning",
        severity="medium",
        weight=15,
        mitre="T1595",
        confidence="medium",
        description="An IP requested several sensitive administrative or configuration paths.",
        recommendation="Rate-limit the source and verify that sensitive paths are not exposed.",
    ),
}


def public_rule_catalogue() -> dict[str, dict[str, str | int]]:
    """Return JSON-ready rule data without exposing implementation objects."""

    return {rule_id: asdict(rule) for rule_id, rule in RULES.items()}
