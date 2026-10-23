# SentinelTrace Test Plan

Run the automated checks with `python3 -m unittest discover -s tests -v` from the project root. The live demo input is `sample_data/demo.log`; it contains only synthetic documentation-range IP addresses.

| ID | Input / action | Expected result |
|---|---|---|
| T01 | Load `sample_data/demo.log` and analyze. | 13 events parse; all six rule categories are represented. |
| T02 | Submit empty input. | Zero events and zero findings; no server error. |
| T03 | Submit normal `GET /home` access line. | One parsed event and no finding. |
| T04 | Submit five failed SSH entries from one IP. | One `SSH_BRUTE_FORCE` finding for that IP. |
| T05 | Add an accepted SSH login after T04. | A `LOGIN_AFTER_FAILURES` finding is added. |
| T06 | Request `../../etc/passwd`. | A `PATH_TRAVERSAL` finding is added. |
| T07 | Submit an unsupported random line. | It is counted as ignored and does not crash analysis. |
| T08 | Try input greater than 1 MB. | Server responds with a clear 413 size-limit error. |
| T09 | Click Download JSON report after a result. | Browser downloads valid JSON containing findings and entities. |
| T10 | Request `GET /health`. | Service returns a local-only status response. |
| T11 | Submit double-encoded `../` in a web request. | One `PATH_TRAVERSAL` finding is created. |
| T12 | Repeat a detection category many times for one IP. | Risk model counts its configured rule weight once, avoiding noisy-score inflation. |

## Acceptance criteria

All functional tests pass; the demo renders in a modern browser; every displayed finding contains source IP, severity, log-line number, evidence, explanation, MITRE identifier, and recommended next step. Test using only synthetic or authorized logs.
