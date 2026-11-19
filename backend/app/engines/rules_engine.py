import re
from typing import List, Dict, Any

class RulesEngine:
    """Deterministic checks for prohibited phrasing, brand casing, superlatives, and required disclaimers."""

    def verify_rules(self, content: str, guidelines: Dict[str, Any], channel: str = "Website Copy") -> List[Dict[str, Any]]:
        findings = []
        content_lower = content.casefold()

        # 1. Prohibited & Discouraged Terminology
        prohibited_terms = guidelines.get("terminology", {}).get("prohibited", [])
        for p in prohibited_terms:
            raw_term = p["term"]
            term = raw_term.casefold()

            # Special brand name casing check
            if term == "brandwise":
                for bad in re.finditer(r'\bbrandwise\b', content, re.I):
                    if bad.group(0) != "BrandWise":
                        findings.append({
                            "id": f"FND-RUL-CAS-{len(findings)+1}",
                            "location": f"Offset {bad.start()}",
                            "category": "Brand Consistency",
                            "title": "Brand name capitalization error",
                            "severity": "Medium",
                            "wrong": bad.group(0),
                            "why": "Official brand identity requires camel-case capitalization: 'BrandWise'.",
                            "sourceId": "GL-STYLE-01",
                            "official": "Brand Identity Style Guide, Page 3: BrandWise.",
                            "owner": "Design Systems Team",
                            "expiry": "Active guideline",
                            "state": "source-verified",
                            "confidence": 100,
                            "fix": "BrandWise",
                            "actionStatus": "pending"
                        })
                continue

            if term in content_lower:
                start_idx = content_lower.find(term)
                actual_text = content[start_idx:start_idx+len(term)]
                findings.append({
                    "id": f"FND-RUL-TRM-{len(findings)+1}",
                    "location": f"Position {start_idx}",
                    "category": "Prohibited Terminology",
                    "title": f"Prohibited phrasing: '{actual_text}'",
                    "severity": p.get("severity", "High"),
                    "wrong": actual_text,
                    "why": p.get("reason", "Violates brand terminology policy."),
                    "sourceId": f"GL-TERM-{len(findings)+1}",
                    "official": f"Approved terminology guidance: replace '{actual_text}' with '{p.get('suggested')}'.",
                    "owner": "Brand Governance Council",
                    "expiry": "Active guideline",
                    "state": "source-verified",
                    "confidence": 97,
                    "fix": p.get("suggested", ""),
                    "actionStatus": "pending"
                })

        # 2. General Superlatives and Absolute Guarantees without Evidence (PDF Page 3 & 4)
        superlatives_pattern = r'\b(world[’\']?s\s+(?:leading|best|fastest|number\s*one)|#(?:1|one)\s+(?:provider|platform|solution)|100%\s+(?:guaranteed|accurate|reliable)|guaranteed\s+(?:results|success|growth)|trusted\s+by\s+every\s+(?:company|enterprise|team))\b'
        for match in re.finditer(superlatives_pattern, content, re.I):
            claim_snippet = match.group(0)
            if not any(f["wrong"].casefold() == claim_snippet.casefold() for f in findings):
                findings.append({
                    "id": f"FND-RUL-SUP-{len(findings)+1}",
                    "location": f"Offset {match.start()}..{match.end()}",
                    "category": "Unsupported Marketing Claim",
                    "title": f"Unsubstantiated claim: '{claim_snippet}'",
                    "severity": "High" if ("guarantee" in claim_snippet.lower() or "100%" in claim_snippet) else "Medium",
                    "wrong": claim_snippet,
                    "why": f"'{claim_snippet}' lacks an approved, current entry in the claims ledger. Superlatives require verifiable citations.",
                    "sourceId": "UNVERIFIED-CLAIM",
                    "official": "No matching approved claim found in the BrandWise ledger.",
                    "owner": "Legal & Brand Review",
                    "expiry": "N/A",
                    "state": "cannot verify - needs human check",
                    "confidence": 92,
                    "fix": "evidence-backed statement (e.g., 'proven enterprise platform')",
                    "actionStatus": "pending"
                })

        # 3. Mandatory Legal Disclaimer
        req_disc = guidelines.get("requiredDisclaimer", "").strip()
        if channel in ["Website Copy", "Digital Ad", "Marketing Email"] and req_disc:
            if "terms and conditions apply" not in content_lower and "terms & conditions" not in content_lower:
                findings.append({
                    "id": f"FND-RUL-DISC-{len(findings)+1}",
                    "location": "Document footer",
                    "category": "Missing Legal Notice",
                    "title": "Mandatory disclaimer missing",
                    "severity": "High",
                    "wrong": "No disclaimer appended",
                    "why": "Outward marketing copy for websites and campaigns must include the approved terms and performance disclaimer.",
                    "sourceId": "GL-LEGAL-01",
                    "official": req_disc,
                    "owner": "Compliance Team",
                    "expiry": "Active guideline",
                    "state": "source-verified",
                    "confidence": 100,
                    "fix": req_disc,
                    "actionStatus": "pending"
                })

        return findings

rules_engine = RulesEngine()
