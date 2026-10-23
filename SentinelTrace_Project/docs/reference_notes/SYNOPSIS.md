# Project Synopsis

## Title

**SentinelTrace: An Explainable Local Log-Based Threat Triage and Alert Prioritization System**

## Student details

Name: ____________________  
Roll No.: ____________________  
Branch/Semester: ____________________  
Mentor: ____________________

## Introduction and background

Security incidents often leave their earliest traces in web-server and authentication logs. Small organizations and student labs may collect these records but lack a simple, privacy-preserving way to prioritize them. Manual review is slow, and opaque alerting tools make it difficult for a student analyst to justify why an event was flagged. SentinelTrace is a local, browser-accessed log triage application that detects selected attack indicators and explains each result using the exact rule and log evidence that produced it.

## Problem statement

System and web logs contain high volumes of routine events mixed with potentially risky activity. Reviewing every line manually delays response and makes correlation across log sources difficult. Existing enterprise SIEM products can be expensive or complex for a small learning environment. The proposed system will parse authorized Apache-style web logs and Linux SSH authentication logs, detect a bounded set of transparent threat indicators, correlate them by source IP address, and present an ordered, explainable incident view. It will not scan targets, execute log content, or claim that an indicator alone proves compromise.

## Objectives

- Parse supported web and SSH log entries into normalized security events.
- Detect at least six explainable indicators: SSH brute force, login after failures, path traversal, SQL injection, command injection, and web scanning.
- Correlate findings by source IP and calculate a documented risk score from 0 to 100.
- Present an analyst-friendly timeline with evidence, severity, and rule rationale.
- Export a JSON incident report and evaluate the system with synthetic, non-sensitive test logs.

## Methodology

1. Collect only authorized or synthetic access and authentication log samples.
2. Parse source-specific lines using regular expressions into normalized event dictionaries.
3. Apply deterministic detection rules to URLs and authentication outcomes.
4. Aggregate rule weights by IP address, cap the score at 100, and rank entities by risk.
5. Render findings in a local dashboard and verify expected results through documented test cases.

## Tools and technologies

Python 3 standard library; HTML, CSS, and JavaScript; JSON; Git. The implementation intentionally avoids mandatory cloud APIs or proprietary data. A local HTTP server delivers the dashboard at `127.0.0.1`.

## Expected outcome and scope

The outcome is a working local demonstrator with synthetic data, rule explanations, incident export, source code, tests, and screenshots. It is a triage aid for an authorized analyst, not a replacement for a production SIEM or a forensic conclusion. Future work can add structured log formats, authentication, a database, and calibrated anomaly detection.

## Ten-week plan

| Week | Deliverable |
|---|---|
| 1 | Finalize domain, title alternatives, and problem statement. |
| 2 | Submit this synopsis with initial references. |
| 3 | Incorporate mentor feedback; lock approved title. |
| 4 | Literature review, requirements, architecture, and rule catalogue. |
| 5 | Implement parser and first three detection rules. |
| 6 | Demonstrate at least 30% progress: parsing and initial dashboard. |
| 7 | Add correlation, scoring, export, and remaining rules. |
| 8 | Integrate modules; execute functional and boundary tests. |
| 9 | Draft report, screenshots, citations, and plagiarism check. |
| 10 | Final demo, source submission, report, PPT, and viva. |

## Initial references

1. OWASP Foundation, “Logging Cheat Sheet.”
2. NIST, *SP 800-92: Guide to Computer Security Log Management*, 2006.
3. MITRE ATT&CK, “Brute Force: Password Guessing (T1110.001).”
4. OWASP Foundation, “SQL Injection Prevention Cheat Sheet.”

