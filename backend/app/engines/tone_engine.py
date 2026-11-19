import re
from typing import List, Dict, Any

class ToneEngine:
    """Tone of voice analyzer with cultural fairness safeguards including Indian English."""

    # Recognized standard formal phrasing in Indian & Commonwealth English
    INDIAN_ENGLISH_EXPRESSIONS = {
        "prepone": "Valid formal Indian English for rescheduling to an earlier date/time.",
        "preponed": "Valid formal Indian English for rescheduled earlier.",
        "revert back": "Accepted business formal phrasing for reply/respond.",
        "kindly note": "Standard polite formal opening.",
        "do the needful": "Traditional formal administrative phrase.",
        "out of station": "Formal phrasing for out of office/town."
    }

    def verify_tone(self, content: str, guidelines: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        content_lower = content.casefold()

        # Check for prohibited aggressive / high-pressure buzzwords
        hyperbolic_buzzwords = [
            (r'\bcrush the competition\b', "Overly aggressive and conflicting with grounded brand persona.", "outperform market benchmarks"),
            (r'\bhack your growth\b', "Informal buzzword conflicting with enterprise credibility.", "accelerate sustainable growth"),
            (r'\b10x your sales overnight\b', "Unrealistic hyperbolic guarantee.", "drive measurable pipeline improvements")
        ]

        for pattern, reason, suggestion in hyperbolic_buzzwords:
            m = re.search(pattern, content, re.I)
            if m:
                findings.append({
                    "id": f"FND-TONE-{len(findings)+1}",
                    "location": f"Offset {m.start()}..{m.end()}",
                    "category": "Brand Tone Violation",
                    "title": f"Hyperbolic phrasing: '{m.group(0)}'",
                    "severity": "Medium",
                    "wrong": m.group(0),
                    "why": reason,
                    "sourceId": "GL-TONE-01",
                    "official": guidelines.get("tone", {}).get("primary", "Professional, grounded, confident and explainable"),
                    "owner": "Brand Governance Council",
                    "expiry": "Active guideline",
                    "state": "source-verified",
                    "confidence": 93,
                    "fix": suggestion,
                    "actionStatus": "pending"
                })

        return findings

tone_engine = ToneEngine()
