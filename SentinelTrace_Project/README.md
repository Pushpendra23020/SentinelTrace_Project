# SentinelTrace

**SentinelTrace: Explainable Local Security Log Threat Triage** is an evaluation-ready fourth-year cybersecurity mini project. It accepts authorised Apache-style access logs and Linux SSH password logs, detects selected indicators using transparent rules, groups related findings by source IP address, and explains each result to the reviewer.

## Evaluation highlights

- Six rule categories: SSH brute force, login after repeated failures, path traversal, SQL-injection indicators, command-injection indicators, and sensitive-path web scanning.
- Explainable result cards: matched evidence, source line, severity, confidence, MITRE ATT&CK identifier, and recommended next step.
- Transparent correlation: each rule category contributes its documented weight once per source IP; the total is capped at 100.
- Professional local dashboard, JSON incident-report download, health endpoint, and automated tests.
- Local-only and safe by design: no scanning, exploitation, external upload, database, cloud API, or execution of log content.
- Python standard library only for runtime and testing.

## Run the project

Open a terminal in this folder:

~~~bash
python3 run.py
~~~

Then open http://127.0.0.1:8080 in a browser.

For the live demonstration:

1. Select **Load synthetic demo**.
2. Select **Analyse logs**.
3. Explain the prioritised entities, evidence timeline, and risk-model breakdown.
4. Select **Download JSON report** to show reproducible output.

Stop the server with Ctrl+C.

## Run automated tests

~~~bash
python3 -m unittest discover -s tests -v
~~~

The test suite uses only the bundled synthetic sample data. It verifies all six detection categories, transparent risk calculation, normal traffic, encoded path traversal, unsupported lines, and source-specific parsing.

## Project structure

~~~text
SentinelTrace_Project/
├── run.py                         # One-command local launcher
├── src/sentineltrace/
│   ├── analyzer.py                # Parsing, rules, correlation, JSON-ready report
│   ├── rules.py                   # Central documented rule catalogue
│   └── server.py                  # Local HTTP routes and input validation
├── web/index.html                 # Dashboard user interface
├── sample_data/demo.log           # Synthetic, repeatable live-demo input
├── tests/test_analyzer.py         # Automated functional tests
├── docs/reference_notes/          # Synopsis source, test plan, viva guide
├── deliverables/
│   ├── 01_Synopsis/               # Final synopsis files
│   ├── 02_Project_Report/         # Final report
│   └── 03_Presentation/           # Final PPT; drafts kept separately
└── tools/document_builders/       # Optional document-generation source scripts
~~~

## Architecture

~~~text
Authorised web / SSH logs
          ↓
Parser and normaliser
          ↓
Explainable rule catalogue
          ↓
IP correlation and capped risk score
          ↓
Local dashboard and JSON incident report
~~~

## Supported input and rules

| Input | What is extracted |
|---|---|
| Apache-style access log | Source IP, timestamp, method, path, and HTTP status |
| Linux sshd password log | Source IP, timestamp, user, and accepted/failed outcome |

| Rule ID | Trigger | Severity | Weight |
|---|---|---:|---:|
| SSH_BRUTE_FORCE | At least five failed SSH password attempts from one IP | High | 35 |
| LOGIN_AFTER_FAILURES | Accepted SSH login after the failure threshold | Critical | 45 |
| PATH_TRAVERSAL | ../ or encoded path traversal in a request | High | 25 |
| SQLI_INDICATOR | Common SQL-injection-like request pattern | High | 25 |
| COMMAND_INJECTION | Shell separator or utility pattern in a request | Critical | 35 |
| WEB_SCANNING | Three or more sensitive path families requested by one IP | Medium | 15 |

## API routes

| Route | Purpose |
|---|---|
| GET / | Local dashboard |
| GET /health | Simple local health check |
| GET /demo | Bundled synthetic demonstration logs |
| GET /rules | Public rule catalogue for evaluation |
| POST /analyze | Analyse a JSON object with a logs field and return the report |

The input limit is 1 MB for this classroom prototype.

## Risk model

For each source IP, SentinelTrace adds the weight of each triggered **rule category once** and caps the result at 100. This prevents repeated copies of the same noisy event from artificially inflating risk. The score prioritises analyst attention only; it is not a probability of compromise, business-impact value, or automatic incident verdict.

| Score | Risk level |
|---:|---|
| 75–100 | Critical |
| 50–74 | High |
| 25–49 | Medium |
| 0–24 | Low |

## Boundaries and ethics

Use only logs you are authorised to inspect. A matched indicator requires analyst validation. This prototype does not replace a SIEM, forensic investigation, secure log retention system, or production incident-response workflow.
