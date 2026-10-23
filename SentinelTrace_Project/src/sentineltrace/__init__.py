"""SentinelTrace package: local, explainable security-log triage."""

from .analyzer import analyze_logs, parse_log_line

__all__ = ["analyze_logs", "parse_log_line"]
