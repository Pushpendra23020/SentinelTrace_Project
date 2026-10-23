"""Automated functional checks for the SentinelTrace analysis engine."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sentineltrace.analyzer import analyze_logs, parse_log_line  # noqa: E402


class AnalyzerTests(unittest.TestCase):
    """Tests use only the bundled synthetic or harmless example text."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.demo_logs = (PROJECT_ROOT / "sample_data" / "demo.log").read_text(encoding="utf-8")

    def test_demo_triggers_the_six_documented_rule_categories(self) -> None:
        report = analyze_logs(self.demo_logs)

        self.assertEqual(report["input_summary"]["parsed_events"], 13)
        self.assertEqual(
            set(report["triggered_rules"]),
            {
                "SSH_BRUTE_FORCE",
                "LOGIN_AFTER_FAILURES",
                "PATH_TRAVERSAL",
                "SQLI_INDICATOR",
                "COMMAND_INJECTION",
                "WEB_SCANNING",
            },
        )

    def test_login_burst_is_prioritized_with_a_transparent_score(self) -> None:
        report = analyze_logs(self.demo_logs)
        entity = next(item for item in report["entities"] if item["ip"] == "203.0.113.45")

        self.assertEqual(entity["risk"], 80)
        self.assertEqual(entity["risk_level"], "critical")
        self.assertEqual(
            {item["rule"] for item in entity["risk_breakdown"]},
            {"SSH_BRUTE_FORCE", "LOGIN_AFTER_FAILURES"},
        )

    def test_benign_access_line_has_no_finding(self) -> None:
        log = '192.0.2.10 - - [14/Sep/2026:10:06:00 +0000] "GET /home HTTP/1.1" 200 2120'
        report = analyze_logs(log)

        self.assertEqual(report["input_summary"]["parsed_events"], 1)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["entities"], [])

    def test_url_encoded_path_traversal_is_detected(self) -> None:
        log = '192.0.2.30 - - [14/Sep/2026:10:06:00 +0000] "GET /download?file=%252e%252e%252fetc%252fpasswd HTTP/1.1" 403 120'
        report = analyze_logs(log)

        self.assertEqual([finding["rule"] for finding in report["findings"]], ["PATH_TRAVERSAL"])

    def test_unknown_line_is_counted_but_never_crashes_analysis(self) -> None:
        report = analyze_logs("this is not a supported log line")

        self.assertEqual(report["input_summary"], {
            "total_lines": 1,
            "parsed_events": 0,
            "ignored_lines": 1,
            "web_events": 0,
            "auth_events": 0,
        })

    def test_parser_keeps_supported_source_categories_separate(self) -> None:
        web = parse_log_line('192.0.2.10 - - [14/Sep/2026:10:06:00 +0000] "GET /home HTTP/1.1" 200 2120', 1)
        auth = parse_log_line('Sep 14 10:02:01 lab sshd[1101]: Failed password for root from 203.0.113.45 port 51621 ssh2', 2)

        self.assertEqual(web["source"], "web")
        self.assertEqual(auth["source"], "auth")
        self.assertEqual(auth["outcome"], "failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
