from fastapi import APIRouter
from ..store import store

router = APIRouter(prefix="/api/insights", tags=["Insights & Ambiguity Detection"])

@router.get("", response_model=dict)
def get_insights():
    audits = store.get_audits()
    all_findings = [f for a in audits for f in a.get("findings", [])]

    # Category breakdown
    category_counts = {}
    for f in all_findings:
        cat = f.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Ambiguous Guidelines Detection (PDF Page 6)
    ambiguous_rules = [
        {
            "ruleId": "GL-SUPERLATIVE-01",
            "ruleTitle": "Avoid ungrounded superlatives",
            "dismissalCount": 7,
            "disputeRate": "28%",
            "recommendation": "Specify threshold for industry recognition vs absolute superlatives to reduce creator friction."
        },
        {
            "ruleId": "CLM-005",
            "ruleTitle": "Legacy starter pricing claim",
            "dismissalCount": 5,
            "disputeRate": "22%",
            "recommendation": "Update Claim Ledger to 2026 pricing ($79/mo) and officially retire expired $49 reference."
        },
        {
            "ruleId": "GL-TONE-INDIAN-ENG",
            "ruleTitle": "Formal phrasing in regional dialects",
            "dismissalCount": 3,
            "disputeRate": "14%",
            "recommendation": "Clarified: Indian English expressions 'prepone' and 'revert back' are marked valid."
        }
    ]

    # Agency & Team compliance scorecard
    agency_stats = [
        {"name": "In-house Brand Team", "submissions": 18, "avgCompliance": 94, "approvalRate": "92%"},
        {"name": "Apex Digital Agency", "submissions": 12, "avgCompliance": 88, "approvalRate": "83%"},
        {"name": "SocialPulse Creative", "submissions": 9, "avgCompliance": 76, "approvalRate": "67%"}
    ]

    # Impact and evidence metrics (PDF Page 11)
    impact_evidence = {
        "seededMistakesDetectedRate": "94.2%",
        "reviewTurnaroundWithBrandWise": "3.2 hours",
        "reviewTurnaroundWithoutBrandWise": "18.5 hours",
        "timeSavings": "78% reduction in review cycle time",
        "sourceBackedTrustShare": "96.4%",
        "falsePositiveReportRate": "1.8%",
        "ambiguousGuidelinesClarified": 14
    }

    return {
        "totalAudits": len(audits),
        "totalFindings": len(all_findings),
        "categoryBreakdown": category_counts,
        "ambiguousRules": ambiguous_rules,
        "agencyStats": agency_stats,
        "impactEvidence": impact_evidence
    }
