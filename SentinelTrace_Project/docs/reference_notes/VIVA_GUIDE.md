# Viva Guide

## Explain the design in 30 seconds

The application normalizes two authorized log formats into event dictionaries. A deterministic rule engine creates explainable findings, then a correlation layer aggregates weighted findings by source IP into a capped risk score. The dashboard displays evidence rather than treating alerts as facts. All processing occurs on `127.0.0.1`.

## Likely questions

1. **Why rules instead of only machine learning?** Rules are transparent, work with a small reproducible dataset, and let an analyst see exactly why an alert appeared. ML can be a future module once labelled data and evaluation controls are available.
2. **What is a false positive?** A benign event that triggers a rule. For example, a security researcher may request a sensitive path. Findings are therefore triage signals, not proof.
3. **How is risk calculated?** Each rule category has a documented weight. For an IP, the system adds each triggered category once and caps the result at 100. This avoids inflating the score just because a noisy source repeats identical requests. It is intentionally simple and auditable, not a universal security metric.
4. **How would you improve scale?** Stream logs, use a queue and persistent datastore, normalize timestamps, and add rate-window correlation.
5. **What are the ethical boundaries?** Analyze only logs that the user is authorized to inspect. The project does not scan, exploit, or transmit log data.

## Easy live modifications

- Change a rule weight in `src/sentineltrace/rules.py` and explain how prioritization changes.
- Add a new sensitive web path to `SENSITIVE_PATHS` in `src/sentineltrace/analyzer.py`.
- Replace the synthetic demo in `sample_data/demo.log` with an authorized sanitized log sample.
