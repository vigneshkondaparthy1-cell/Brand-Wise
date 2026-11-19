"""Report deterministic detection and false-positive rates on the labelled set."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import run_brandwise_checks

cases = json.loads((Path(__file__).with_name("test_set.json")).read_text(encoding="utf-8"))
counts = {"compliant": [0, 0], "noncompliant": [0, 0]}
for case in cases:
    findings = run_brandwise_checks(case["text"], channel=case["channel"])["findings"]
    flagged = bool(findings)
    total, errors = counts[case["label"]]
    counts[case["label"]] = [total + 1, errors + int(flagged != (case["label"] == "noncompliant"))]
compliant_total, false_flags = counts["compliant"]
noncompliant_total, missed = counts["noncompliant"]
print(f"Cases: {len(cases)} ({compliant_total} compliant, {noncompliant_total} noncompliant)")
print(f"Detection rate: {(noncompliant_total - missed) / noncompliant_total:.0%}")
print(f"False-flag rate: {false_flags / compliant_total:.0%}")
