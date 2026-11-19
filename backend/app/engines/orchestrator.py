from typing import Dict, Any, List
from .claims_engine import claims_engine
from .rules_engine import rules_engine
from .tone_engine import tone_engine
from ..store import store

class ReviewOrchestrator:
    """Orchestrates multi-engine verification runs and computes grounded compliance scores."""

    def run_full_audit(self, content: str, channel: str = "Website Copy") -> Dict[str, Any]:
        claims = store.get_claims()
        guidelines = store.get_guidelines()

        findings: List[Dict[str, Any]] = []

        # 1. Claims Ledger Verification
        claims_findings = claims_engine.verify_claims(content, claims)
        findings.extend(claims_findings)

        # 2. Deterministic Terminology & Rules
        rules_findings = rules_engine.verify_rules(content, guidelines, channel=channel)
        findings.extend(rules_findings)

        # 3. Tone & Voice Verification
        tone_findings = tone_engine.verify_tone(content, guidelines)
        findings.extend(tone_findings)

        # Compute Scoring Deductions:
        # Critical: -25, High: -15, Medium: -8, Low: -4
        deductions = 0
        for f in findings:
            sev = f.get("severity", "Medium")
            if sev == "Critical":
                deductions += 25
            elif sev == "High":
                deductions += 15
            elif sev == "Medium":
                deductions += 8
            else:
                deductions += 4

        score = max(0, min(100, 100 - deductions))
        confidence = int(sum(f.get("confidence", 95) for f in findings) / len(findings)) if findings else 98

        return {
            "score": score,
            "confidence": confidence,
            "findings": findings
        }

orchestrator = ReviewOrchestrator()
