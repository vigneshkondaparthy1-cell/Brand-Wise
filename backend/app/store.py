import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import settings

# Seed Data directly from the BrandWise Solution Proposal
SEED_CLAIMS = [
    {
        "id": "CLM-001",
        "statement": "Cuts onboarding time by up to 20%",
        "category": "Product Performance",
        "evidence": "2026 Enterprise Benchmark Study, Section 4.2; Verified by QA Operations",
        "owner": "Sarah Jenkins (VP Product)",
        "expiry": "2027-12-31",
        "status": "Active",
        "prohibitedPhrases": ["cuts onboarding by 30%", "cuts onboarding time by 50%", "instant onboarding"],
        "notes": "Approved in Q1 product review. Any claim exceeding 20% must be flagged as unsupported."
    },
    {
        "id": "CLM-002",
        "statement": "Acme Technologies was established in 2012",
        "category": "Company Identity",
        "evidence": "Delaware Certificate of Incorporation #4829104",
        "owner": "Marcus Vance (Chief Legal Counsel)",
        "expiry": "2030-01-01",
        "status": "Active",
        "prohibitedPhrases": ["founded in 2010", "founded in 2015", "established in 2008"],
        "notes": "Core legal fact. Strict year match required."
    },
    {
        "id": "CLM-003",
        "statement": "Over 500 enterprise customers across North America and Europe",
        "category": "Customer Traction",
        "evidence": "Q3 2026 Customer Ledger, Verified by Finance & Sales Ops",
        "owner": "Elena Rostova (Head of Growth)",
        "expiry": "2027-06-30",
        "status": "Active",
        "prohibitedPhrases": ["used by every Fortune 500", "trusted by millions", "universal enterprise adoption"],
        "notes": "Audited figure is 500+. Do not use universal or unsubstantiated superlatives."
    },
    {
        "id": "CLM-004",
        "statement": "Certified ISO 27001, SOC 2 Type II, and fully GDPR compliant",
        "category": "Security & Compliance",
        "evidence": "Coalfire Security Audit Certificate #CF-88291-2026",
        "owner": "Devon Miller (CISO)",
        "expiry": "2027-03-31",
        "status": "Active",
        "prohibitedPhrases": ["military-grade encryption", "unhackable security", "100% bug-free"],
        "notes": "Certifications must be cited verbatim with official names."
    },
    {
        "id": "CLM-005",
        "statement": "Starter tiers start at $49 per seat per month (Legacy 2024 pricing)",
        "category": "Pricing & Licensing",
        "evidence": "2024 Product Catalog (SUPERSEDED by 2026 Price Book $79/mo)",
        "owner": "Finance Operations",
        "expiry": "2025-01-01",
        "status": "Expired",
        "prohibitedPhrases": ["$49/month", "cheap plans", "lowest price in the world"],
        "notes": "EXPIRED CLAIM: When referenced in copy, system must flag 'Cannot verify - needs human check' due to expired evidence."
    },
    {
        "id": "CLM-006",
        "statement": "99.95% uptime SLA with 24/7 dedicated enterprise response",
        "category": "Service Level",
        "evidence": "Master Services Agreement v4.2, Section 8 SLA Addendum",
        "owner": "Site Reliability Team",
        "expiry": "2027-08-15",
        "status": "Active",
        "prohibitedPhrases": ["100% uptime guaranteed", "zero downtime forever", "never goes down"],
        "notes": "Guarantees of 100% or absolute zero downtime violate SLA guidelines."
    }
]

SEED_GUIDELINES = {
    "version": "3.2",
    "updatedAt": "2026-11-01T00:00:00Z",
    "brandName": "Acme Technologies",
    "productName": "BrandWise",
    "requiredDisclaimer": "Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.",
    "tone": {
        "primary": "Professional, grounded, confident and explainable",
        "avoid": "Over-promising, hyperbolic buzzwords, ungrounded superlatives",
        "rules": [
            "Use active voice and clear, factual declarations.",
            "Respect regional English variants: Indian English conventions (e.g., 'revert back', 'prepone', 'kindly note') are reviewed contextually without penalizing formal fluency.",
            "State measurable benefits instead of vague superlatives (e.g., 'cuts onboarding time by up to 20%' instead of 'fastest in the galaxy').",
            "Always include the mandatory legal disclaimer on outward customer-facing marketing material."
        ]
    },
    "terminology": {
        "approved": [
            {"term": "BrandWise", "note": "Always camel-case as BrandWise; never Brandwise or BRANDWISE in body copy."},
            {"term": "Client Workspace", "note": "Approved noun for tenant spaces."},
            {"term": "Claim Ledger", "note": "Capitalized when referring to the official repository."},
            {"term": "Source-backed", "note": "Hyphenated descriptor."},
            {"term": "Pre-publication review", "note": "Official platform definition."}
        ],
        "prohibited": [
            {"term": "Brandwise", "reason": "Incorrect brand casing. Must be 'BrandWise'.", "suggested": "BrandWise", "severity": "Medium"},
            {"term": "world's leading", "reason": "Unsupported market superlative. Risk of false advertising.", "suggested": "leading provider", "severity": "High"},
            {"term": "world's best", "reason": "Unsubstantiated superlative.", "suggested": "industry-standard", "severity": "High"},
            {"term": "#1 platform", "reason": "Unsubstantiated market ranking claim.", "suggested": "dedicated platform", "severity": "High"},
            {"term": "100% guaranteed", "reason": "Absolute legal liability guarantee. Strictly prohibited.", "suggested": "committed to SLA", "severity": "Critical"},
            {"term": "guaranteed results", "reason": "Legal liability risk without signed SLA.", "suggested": "proven outcomes", "severity": "Critical"},
            {"term": "cheap", "reason": "Diminishes brand perceived value.", "suggested": "cost-effective", "severity": "Low"},
            {"term": "foolproof", "reason": "Exaggerated claim.", "suggested": "robust", "severity": "Low"}
        ]
    },
    "visual": {
        "primaryColor": "#0879d1",
        "secondaryColor": "#138a69",
        "warningColor": "#e97821",
        "criticalColor": "#d9514d",
        "minContrastRatio": 4.5,
        "largeTextContrastRatio": 3.0,
        "fontFamily": "Inter, system-ui, sans-serif",
        "logoVariants": ["brandwise-lockup-dark.svg", "brandwise-lockup-light.svg", "brandwise-symbol.svg"]
    },
    "accessibility": {
        "standard": "WCAG 2.1 Level AA",
        "contrastNormalText": 4.5,
        "contrastLargeText": 3.0,
        "requireAltText": True,
        "maxFleschKincaidGrade": 12.0,
        "headingHierarchyStrict": True
    }
}

class LocalStore:
    def __init__(self):
        self.audits_file = settings.AUDITS_FILE
        self.claims_file = settings.CLAIMS_FILE
        self.guidelines_file = settings.GUIDELINES_FILE
        self._ensure_init()

    def _ensure_init(self):
        if not self.claims_file.exists():
            self.save_claims(SEED_CLAIMS)
        if not self.guidelines_file.exists():
            self.save_guidelines(SEED_GUIDELINES)
        if not self.audits_file.exists():
            self.save_audits([])

    def _read_json(self, path: Path, default: Any) -> Any:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            return default
        except Exception:
            return default

    def _write_json(self, path: Path, data: Any) -> bool:
        try:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def get_audits(self) -> List[Dict[str, Any]]:
        return self._read_json(self.audits_file, [])

    def save_audits(self, audits: List[Dict[str, Any]]) -> bool:
        return self._write_json(self.audits_file, audits)

    def get_claims(self) -> List[Dict[str, Any]]:
        return self._read_json(self.claims_file, SEED_CLAIMS)

    def save_claims(self, claims: List[Dict[str, Any]]) -> bool:
        return self._write_json(self.claims_file, claims)

    def get_guidelines(self) -> Dict[str, Any]:
        return self._read_json(self.guidelines_file, SEED_GUIDELINES)

    def save_guidelines(self, guidelines: Dict[str, Any]) -> bool:
        return self._write_json(self.guidelines_file, guidelines)

    def reset_all(self):
        self.save_claims(SEED_CLAIMS)
        self.save_guidelines(SEED_GUIDELINES)
        # Seed an initial audit record
        from .config import settings
        self.save_audits([])

store = LocalStore()
