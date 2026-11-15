import accounts
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone, timedelta
import threading
import time
import os
import json
import re
import urllib.parse
import urllib.request
import urllib.error
import html as html_lib
from document_ingestion import extract_document
from gemini_review import review as gemini_review

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'audit-data.json'
CLAIMS_DB = ROOT / 'claims-data.json'
GUIDELINES_DB = ROOT / 'guidelines-data.json'
INSIGHTS_DB = ROOT / 'insights-data.json'
AUDIT_PREFERENCES_DB = ROOT / 'workspace-audit-preferences.json'
ENV_FILE = ROOT / '.env'
PAGE = 'The-Final-Draft-Hackathon-Updated.html'
LOGIN_FAILURES = {}
LOGIN_FAILURES_LOCK = threading.Lock()
LOGIN_WINDOW_SECONDS = 900
LOGIN_MAX_FAILURES = 8
OTP_REQUESTS = {}
OTP_REQUESTS_LOCK = threading.Lock()
OTP_REQUEST_WINDOW_SECONDS = 600
OTP_REQUEST_MAXIMUM = 5
AUDIT_PREFERENCES_LOCK = threading.Lock()
DEFAULT_AUDIT_PREFERENCES = {'strictness': 'balanced', 'passingThreshold': 80}


def login_is_limited(client_ip):
    now = time.monotonic()
    with LOGIN_FAILURES_LOCK:
        recent = [stamp for stamp in LOGIN_FAILURES.get(client_ip, []) if now - stamp < LOGIN_WINDOW_SECONDS]
        LOGIN_FAILURES[client_ip] = recent
        return len(recent) >= LOGIN_MAX_FAILURES


def record_login_failure(client_ip):
    with LOGIN_FAILURES_LOCK:
        LOGIN_FAILURES.setdefault(client_ip, []).append(time.monotonic())


def clear_login_failures(client_ip):
    with LOGIN_FAILURES_LOCK:
        LOGIN_FAILURES.pop(client_ip, None)

def allow_otp_request(client_ip):
    now = time.monotonic()
    with OTP_REQUESTS_LOCK:
        recent = [stamp for stamp in OTP_REQUESTS.get(client_ip, []) if now - stamp < OTP_REQUEST_WINDOW_SECONDS]
        if len(recent) >= OTP_REQUEST_MAXIMUM:
            OTP_REQUESTS[client_ip] = recent
            return False
        recent.append(now)
        OTP_REQUESTS[client_ip] = recent
        return True


def session_cleanup_loop():
    while True:
        try:
            accounts.cleanup_expired_sessions()
        except Exception:
            pass
        time.sleep(3600)

def load_env():
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and not os.environ.get(k):
                        os.environ[k] = v
        except Exception:
            pass

load_env()

def get_masked_keys():
    def mask(val, prefix_len=7, suffix_len=4):
        if not val:
            return {"configured": False, "masked": "Not configured"}
        if len(val) <= prefix_len + suffix_len:
            return {"configured": True, "masked": "••••••••"}
        return {"configured": True, "masked": f"{val[:prefix_len]}...{val[-suffix_len:]}"}

    return {
        "anthropic": {
            **mask(os.environ.get("ANTHROPIC_API_KEY", "").strip(), 7, 4),
            "service": "Claude 3.5 Sonnet",
            "role": "Deep Claim Reasoning & Tone Analysis"
        },
        "gemini": {
            **mask(os.environ.get("GEMINI_API_KEY", "").strip(), 6, 4),
            "service": f"Google Gemini {os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash').strip() or 'gemini-2.5-flash'}",
            "role": "Optional text review"
        },
        "openai": {
            **mask(os.environ.get("OPENAI_API_KEY", "").strip(), 7, 4),
            "service": "OpenAI GPT-4o",
            "role": "Structured JSON & Format Normalization"
        },
        "slack": {
            **mask(os.environ.get("SLACK_WEBHOOK_URL", "").strip(), 12, 5),
            "service": "Slack Incoming Webhook",
            "role": "#brand-governance-alerts Channel Notifications"
        }
    }

def save_env_keys(keys_dict):
    for k, v in keys_dict.items():
        if v is not None and v != "••••••••":
            os.environ[k] = v.strip()
    try:
        lines = [
            "# BrandWise Platform Configuration & API Keys",
            f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', '')}",
            f"GEMINI_API_KEY={os.environ.get('GEMINI_API_KEY', '')}",
            f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY', '')}",
            f"SLACK_WEBHOOK_URL={os.environ.get('SLACK_WEBHOOK_URL', '')}",
            "BRANDWISE_PORT=8765",
            "BRANDWISE_ENV=production"
        ]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False

def test_external_api_key(provider, api_key):
    provider = provider.lower().strip()
    api_key = api_key.strip()
    if not api_key:
        return {"valid": False, "provider": provider, "error": "API key cannot be empty"}
    try:
        if provider == "anthropic":
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({"model": "claude-3-5-sonnet-20241022", "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]}).encode("utf-8"),
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                return {"valid": True, "provider": "Anthropic Claude", "status": resp.status, "model": "claude-3-5-sonnet-20241022"}
        elif provider == "openai":
            req = urllib.request.Request("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"}, method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                return {"valid": True, "provider": "OpenAI", "status": resp.status, "model": "gpt-4o"}
        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                return {"valid": True, "provider": "Google Gemini", "status": resp.status, "model": "gemini-3.5-flash-lite"}
        elif provider == "slack":
            if not api_key.startswith("https://hooks.slack.com/"):
                return {"valid": False, "provider": "Slack", "error": "Invalid Slack webhook URL format (must start with https://hooks.slack.com/)"}
            return {"valid": True, "provider": "Slack Webhook", "status": 200, "note": "Valid webhook URL format"}
        return {"valid": False, "provider": provider, "error": f"Unknown provider: {provider}"}
    except urllib.error.HTTPError as e:
        err_msg = f"HTTP {e.code}: {e.reason}"
        try:
            raw = e.read().decode("utf-8")
            err_data = json.loads(raw)
            if "error" in err_data:
                err_msg = str(err_data["error"])
        except Exception:
            pass
        return {"valid": False, "provider": provider, "error": err_msg, "code": e.code}
    except urllib.error.URLError as e:
        return {"valid": False, "provider": provider, "error": f"Connection error: {e.reason}"}
    except Exception as e:
        return {"valid": False, "provider": provider, "error": str(e)}

# Default Seed Data matching the BrandWise Solution Proposal (PDF)
DEFAULT_CLAIMS = [
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
        "status": "Needs Review",
        "prohibitedPhrases": ["military-grade encryption", "unhackable security", "100% bug-free", "fully GDPR compliant", "GDPR compliant"],
        "notes": "Pending legal review. The local evidence entry does not substantiate a blanket GDPR compliance claim. Do not use that wording until counsel reviews the actual processing practices and any relevant certification evidence."
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
    },
    {
        "id": "CLM-007",
        "statement": "Starter tiers start at $79 per seat per month",
        "category": "Pricing & Licensing",
        "evidence": "2026 Price Book (current pricing reference recorded in the demo claim ledger)",
        "owner": "Finance Operations",
        "expiry": "2027-12-31",
        "status": "Active",
        "prohibitedPhrases": ["$99/month", "$79 per month per user"],
        "notes": "Current demo pricing reference. Confirm against the Finance-owned Price Book before publication."
    }
]

DEFAULT_GUIDELINES = {
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

DEFAULT_AUDITS = [
    {
        "id": "BW-2026-001",
        "title": "Q4 SaaS Enterprise Launch Announcement",
        "channel": "Website Copy",
        "type": "Website Copy",
        "creator": "Alex Rivera (Senior Content Lead)",
        "agency": "In-house Brand Team",
        "role": "Creator",
        "status": "In review",
        "date": "2026-11-12T14:30:00Z",
        "score": 68,
        "confidence": 93,
        "content": "Acme Technologies was founded in 2010 to empower high-velocity teams. Our BrandWise platform is the world's leading pre-publication review engine, trusted by every enterprise on the planet. Independent audits show BrandWise cuts onboarding time by 30% with guaranteed results.\n\nEnjoy our flexible plans starting at $49/month with zero hassle.",
        "reference": "Acme Technologies was established in 2012. BrandWise cuts onboarding time by up to 20% (CLM-001). Disclaimer required. Superlatives and guarantees prohibited.",
        "findings": [
            {
                "id": "FND-001",
                "location": "Paragraph 1, Sentence 1",
                "category": "Outdated / Conflicting Fact",
                "title": "Founding year mismatch",
                "severity": "High",
                "wrong": "founded in 2010",
                "why": "The submitted copy states 2010, which conflicts with official corporate records (2012).",
                "sourceId": "CLM-002",
                "official": "Delaware Certificate of Incorporation #4829104: Established in 2012.",
                "owner": "Marcus Vance (Chief Legal Counsel)",
                "expiry": "2030-01-01",
                "state": "source-verified",
                "confidence": 98,
                "fix": "founded in 2012",
                "actionStatus": "pending"
            },
            {
                "id": "FND-002",
                "location": "Paragraph 1, Sentence 2",
                "category": "Unsupported Superlative",
                "title": "Unsupported market leadership claim",
                "severity": "High",
                "wrong": "world's leading pre-publication review engine",
                "why": "Unsubstantiated superlative ranking without documented independent market share citation.",
                "sourceId": "GL-TERM-02",
                "official": "Prohibited phrase: 'world's leading'. Use specific, evidence-backed capabilities.",
                "owner": "Brand Governance Council",
                "expiry": "Active guideline",
                "state": "source-verified",
                "confidence": 94,
                "fix": "dedicated pre-publication review platform",
                "actionStatus": "pending"
            },
            {
                "id": "FND-003",
                "location": "Paragraph 1, Sentence 2",
                "category": "Exaggerated Customer Claim",
                "title": "Unsubstantiated universal claim",
                "severity": "Medium",
                "wrong": "trusted by every enterprise on the planet",
                "why": "Universal claim lacks proof. Official approved ledger supports 500+ enterprise clients.",
                "sourceId": "CLM-003",
                "official": "Claim CLM-003: 'Over 500 enterprise customers across North America and Europe'.",
                "owner": "Elena Rostova (Head of Growth)",
                "expiry": "2027-06-30",
                "state": "source-verified",
                "confidence": 91,
                "fix": "trusted by over 500 enterprise customers worldwide",
                "actionStatus": "pending"
            },
            {
                "id": "FND-004",
                "location": "Paragraph 1, Sentence 3",
                "category": "Unsupported Performance Claim",
                "title": "Unsubstantiated percentage metric (30% vs approved 20%)",
                "severity": "High",
                "wrong": "cuts onboarding time by 30%",
                "why": "Approved claim benchmark is 20%. No approved source in the ledger validates 30%.",
                "sourceId": "CLM-001",
                "official": "CLM-001: Cuts onboarding time by up to 20% (Benchmark Study Section 4.2).",
                "owner": "Sarah Jenkins (VP Product)",
                "expiry": "2027-12-31",
                "state": "source-verified",
                "confidence": 96,
                "fix": "cuts onboarding time by up to 20%",
                "actionStatus": "pending"
            },
            {
                "id": "FND-005",
                "location": "Paragraph 1, Sentence 3",
                "category": "Prohibited Guarantee",
                "title": "Illegal outcome guarantee",
                "severity": "Critical",
                "wrong": "with guaranteed results",
                "why": "Strict legal liability risk. Guarantees of performance are prohibited without custom contract terms.",
                "sourceId": "GL-TERM-06",
                "official": "Legal policy #4: Prohibited absolute guarantees.",
                "owner": "Marcus Vance (Chief Legal Counsel)",
                "expiry": "Active guideline",
                "state": "source-verified",
                "confidence": 99,
                "fix": "with proven customer outcomes",
                "actionStatus": "pending"
            },
            {
                "id": "FND-006",
                "location": "Paragraph 2, Sentence 1",
                "category": "Expired Pricing Reference",
                "title": "Pricing claim cannot be verified (Source expired)",
                "severity": "High",
                "wrong": "$49/month",
                "why": "The referenced pricing catalog (CLM-005) expired on 2025-01-01. Current pricing requires human check.",
                "sourceId": "CLM-005",
                "official": "Claim CLM-005: Expired 2025-01-01. Current list price is $79/seat/mo.",
                "owner": "Finance Operations",
                "expiry": "2025-01-01 (EXPIRED)",
                "state": "cannot verify - needs human check",
                "confidence": 95,
                "fix": "starting at $79 per seat per month (confirm with sales)",
                "actionStatus": "pending"
            },
            {
                "id": "FND-007",
                "location": "End of Document",
                "category": "Missing Legal Notice",
                "title": "Required legal disclaimer missing",
                "severity": "High",
                "wrong": "No disclaimer appended",
                "why": "Official guidelines mandate the standardized performance & terms disclaimer on all website landing pages.",
                "sourceId": "GL-LEGAL-01",
                "official": "Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.",
                "owner": "Compliance Team",
                "expiry": "Active guideline",
                "state": "source-verified",
                "confidence": 100,
                "fix": "Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.",
                "actionStatus": "pending"
            }
        ],
        "revisions": [
            {
                "version": "v1",
                "author": "Alex Rivera",
                "timestamp": "2026-11-12T14:30:00Z",
                "text": "Acme Technologies was founded in 2010 to empower high-velocity teams. Our BrandWise platform is the world's leading pre-publication review engine, trusted by every enterprise on the planet. Independent audits show BrandWise cuts onboarding time by 30% with guaranteed results.\n\nEnjoy our flexible plans starting at $49/month with zero hassle.",
                "notes": "Initial draft submitted for pre-publication audit."
            }
        ],
        "comments": [
            {
                "id": "COM-01",
                "author": "Jessica Taylor (Brand Compliance Reviewer)",
                "role": "Reviewer",
                "timestamp": "2026-11-12T15:10:00Z",
                "text": "Alex, please review findings #1, #4, and #5 before we can approve. The 30% figure cannot go out on the homepage since legal signed off on 20% maximum."
            }
        ],
        "auditTrail": [
            {"action": "Draft Created", "user": "Alex Rivera", "timestamp": "2026-11-12T14:30:00Z", "note": "Uploaded text via Review Studio"},
            {"action": "Automated Check Completed", "user": "BrandWise Hybrid Engine", "timestamp": "2026-11-12T14:30:04Z", "note": "7 findings detected; 1 flagged as 'cannot verify'"},
            {"action": "State Changed to In Review", "user": "System", "timestamp": "2026-11-12T14:30:05Z", "note": "Submitted to Brand Governance Queue"}
        ]
    },
    {
        "id": "BW-2026-002",
        "title": "Agency Partner Social Campaign - Indian English Nuance Test",
        "channel": "Social Media",
        "type": "Social Media Post",
        "creator": "Rohan Sharma (Apex Digital Agency)",
        "agency": "Apex Digital Agency",
        "role": "External Agency",
        "status": "Approved",
        "date": "2026-11-10T11:15:00Z",
        "score": 92,
        "confidence": 96,
        "content": "Kindly note: We have preponed the webinar on governance workflows to Friday. BrandWise cuts onboarding time by up to 20% for modern content teams. Please revert back with your questions. Terms and conditions apply.",
        "reference": "BrandWise guidelines support regional English variations including Indian English without false flagging. Claim CLM-001 supported.",
        "findings": [],
        "revisions": [
            {
                "version": "v1",
                "author": "Rohan Sharma",
                "timestamp": "2026-11-10T11:15:00Z",
                "text": "Kindly note: We have preponed the webinar on governance workflows to Friday. BrandWise cuts onboarding time by up to 20% for modern content teams. Please revert back with your questions. Terms and conditions apply.",
                "notes": "Submitted with localized phrasing for India & APAC tech audiences."
            }
        ],
        "comments": [
            {
                "id": "COM-02",
                "author": "Sarah Jenkins (VP Product / Brand Manager)",
                "role": "Brand Manager",
                "timestamp": "2026-11-10T11:45:00Z",
                "text": "Tone check validated: 'prepone' and 'revert back' correctly recognized as formal Indian English standard, not penalized. Claim 20% is citation-backed. Approved for release."
            }
        ],
        "auditTrail": [
            {"action": "Draft Created", "user": "Rohan Sharma", "timestamp": "2026-11-10T11:15:00Z", "note": "Agency submission"},
            {"action": "Automated Check Completed", "user": "BrandWise Hybrid Engine", "timestamp": "2026-11-10T11:15:03Z", "note": "Score 92/100 · 0 blocking issues"},
            {"action": "Approved", "user": "Sarah Jenkins", "timestamp": "2026-11-10T11:45:00Z", "note": "Signed off by Brand Manager"}
        ]
    },
    {
        "id": "BW-2026-003",
        "title": "Corporate Overview & Fact Sheet 2026",
        "channel": "Company Profile",
        "type": "Company Profile",
        "creator": "Rachel Green",
        "agency": "In-house Brand Team",
        "role": "Creator",
        "status": "Published",
        "date": "2026-11-08T09:00:00Z",
        "score": 100,
        "confidence": 99,
        "content": "Acme Technologies was established in 2012. We serve over 500 enterprise customers across North America and Europe. Certified ISO 27001, SOC 2 Type II, and fully GDPR compliant. Terms and conditions apply.",
        "reference": "Established 2012. 500+ enterprises. ISO 27001 & SOC 2 certified. Mandatory disclaimer included.",
        "findings": [],
        "revisions": [
            {
                "version": "v1",
                "author": "Rachel Green",
                "timestamp": "2026-11-08T09:00:00Z",
                "text": "Acme Technologies was established in 2012. We serve over 500 enterprise customers across North America and Europe. Certified ISO 27001, SOC 2 Type II, and fully GDPR compliant. Terms and conditions apply.",
                "notes": "Final production fact sheet."
            }
        ],
        "comments": [],
        "auditTrail": [
            {"action": "Draft Created", "user": "Rachel Green", "timestamp": "2026-11-08T09:00:00Z", "note": "Standard corporate overview"},
            {"action": "Automated Check Completed", "user": "BrandWise Hybrid Engine", "timestamp": "2026-11-08T09:00:02Z", "note": "Score 100/100 · 100% citation verified"},
            {"action": "Approved", "user": "Marcus Vance", "timestamp": "2026-11-08T09:20:00Z", "note": "Approved by Legal"},
            {"action": "Published", "user": "Rachel Green", "timestamp": "2026-11-08T09:30:00Z", "note": "Published to public investor portal"}
        ]
    }
]


def load_json(path, fallback):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        return fallback
    except Exception:
        return fallback


def save_json(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except Exception:
        return False


def get_audits():
    return load_json(DB, DEFAULT_AUDITS)


def get_workspace_audit_preferences():
    with AUDIT_PREFERENCES_LOCK:
        saved = load_json(AUDIT_PREFERENCES_DB, DEFAULT_AUDIT_PREFERENCES)
    if not isinstance(saved, dict):
        saved = {}
    strictness = saved.get('strictness')
    if strictness not in ('lenient', 'balanced', 'strict'):
        strictness = DEFAULT_AUDIT_PREFERENCES['strictness']
    try:
        threshold = int(saved.get('passingThreshold', DEFAULT_AUDIT_PREFERENCES['passingThreshold']))
    except (TypeError, ValueError):
        threshold = DEFAULT_AUDIT_PREFERENCES['passingThreshold']
    return {'strictness': strictness, 'passingThreshold': max(50, min(95, threshold))}


def set_workspace_audit_preferences(data):
    strictness = data.get('strictness', 'balanced')
    if strictness not in ('lenient', 'balanced', 'strict'):
        raise ValueError('Choose Lenient, Balanced, or Strict review mode.')
    try:
        threshold = int(data.get('passingThreshold', 80))
    except (TypeError, ValueError):
        raise ValueError('The passing threshold must be a number between 50% and 95%.') from None
    if threshold < 50 or threshold > 95:
        raise ValueError('The passing threshold must be between 50% and 95%.')
    settings = {'strictness': strictness, 'passingThreshold': threshold}
    with AUDIT_PREFERENCES_LOCK:
        if not save_json(AUDIT_PREFERENCES_DB, settings):
            raise ValueError('Could not save the shared workspace audit preferences.')
    return settings


def compliance_score(findings, strictness='balanced'):
    penalties = {
        'lenient': {'Critical': 20, 'High': 10, 'Medium': 5, 'Low': 2},
        'balanced': {'Critical': 25, 'High': 15, 'Medium': 8, 'Low': 4},
        'strict': {'Critical': 30, 'High': 20, 'Medium': 10, 'Low': 5},
    }.get(strictness, {'Critical': 25, 'High': 15, 'Medium': 8, 'Low': 4})
    deductions = sum(penalties.get(f.get('severity', 'Medium'), 8) for f in findings if f.get('category') != 'Accessibility - Readability')
    return max(0, min(100, 100 - deductions))


def get_claims():
    return load_json(CLAIMS_DB, DEFAULT_CLAIMS)


def get_current_ai_reference_claims():
    today = datetime.now(timezone.utc).date().isoformat()
    return [
        claim for claim in get_claims()
        if claim.get('status') == 'Active' and claim.get('expiry', '') >= today
    ]


def get_guidelines():
    return load_json(GUIDELINES_DB, DEFAULT_GUIDELINES)


def check_text_accessibility(content, guidelines=None):
    guidelines = guidelines or get_guidelines()
    accessibility = guidelines.get('accessibility', {})
    required_disclaimer = guidelines.get('requiredDisclaimer', '').strip()
    text_for_grade = re.sub(re.escape(required_disclaimer), ' ', content, flags=re.I) if required_disclaimer else content
    plain = html_lib.unescape(re.sub(r'<[^>]*>', ' ', text_for_grade))
    words = re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", plain)
    sentences = [s for s in re.split(r'[.!?]+', plain) if re.search(r'[A-Za-z]', s)]
    grade = None
    if words and sentences:
        def syllables(word):
            lower = word.casefold().replace('’', "'")
            groups = len(re.findall(r'[aeiouy]+', lower))
            if lower.endswith('e') and not lower.endswith(('le', 'ye')) and groups > 1:
                groups -= 1
            return max(1, groups)

        syllable_total = sum(syllables(word) for word in words)
        grade = round(0.39 * (len(words) / len(sentences)) + 11.8 * (syllable_total / len(words)) - 15.59, 1)

    headings = []
    for match in re.finditer(r'(?m)^\s*(#{1,6})\s+[^\n]+', content):
        headings.append((match.start(), len(match.group(1)), match.group(0).strip()))
    for match in re.finditer(r'<h([1-6])\b[^>]*>.*?</h\1\s*>', content, re.I | re.S):
        headings.append((match.start(), int(match.group(1)), match.group(0).strip()))
    headings.sort(key=lambda item: item[0])
    issues = []
    if accessibility.get('headingHierarchyStrict') and headings:
        if headings[0][1] > 1:
            issues.append({'text': headings[0][2], 'message': 'The first heading should start at level 1.'})
        for previous, current in zip(headings, headings[1:]):
            if current[1] > previous[1] + 1:
                issues.append({'text': current[2], 'message': f'Heading level skips from level {previous[1]} to level {current[1]}.'})

    maximum = float(accessibility.get('maxFleschKincaidGrade', 12.0))
    return {
        'readingGrade': grade,
        'maxGrade': maximum,
        'readabilityPass': grade is None or grade <= maximum,
        'headingCount': len(headings),
        'headingIssues': issues,
    }


# Run multi-dimensional checks (Claims, Tone, Terminology, Banned words, Visual, WCAG, Uncertainty)
def run_brandwise_checks(content, channel="Website Copy", reference=None, strictness="balanced"):
    claims = get_claims()
    guidelines = get_guidelines()
    findings = []
    content_lower = content.casefold()
    accessibility_result = check_text_accessibility(content, guidelines)

    # Check all exact prohibited phrases supplied by the approved claim ledger.
    for claim in claims:
        for phrase in claim.get("prohibitedPhrases", []):
            if not phrase:
                continue
            for match in re.finditer(re.escape(phrase), content, re.I):
                if any(f.get("wrong", "").casefold() == match.group(0).casefold() for f in findings):
                    continue
                active = claim.get("status") == "Active" and claim.get("expiry", "") >= datetime.now(timezone.utc).date().isoformat()
                findings.append({
                    "id": f"FND-CLM-{len(findings)+1}",
                    "location": f"Offset {match.start()}..{match.end()}",
                    "category": "Prohibited Claim Wording",
                    "title": f"{'Expired demo claim — cannot verify' if not active and claim.get('id') == 'CLM-005' else 'Prohibited phrase'}: {match.group(0)}",
                    "severity": "High",
                    "wrong": match.group(0),
                    "why": claim.get("notes", "This wording is prohibited by the claim ledger."),
                    "sourceId": claim.get("id", ""),
                    "official": claim.get("evidence", "") if active else "No current approved evidence verified",
                    "owner": claim.get("owner", ""),
                    "expiry": claim.get("expiry", ""),
                    "state": "source-verified" if active else "cannot verify - needs human check",
                    "confidence": 100,
                    "fix": claim.get("statement", ""),
                    "actionStatus": "pending"
                })

    active_pricing = [
        claim for claim in claims
        if 'pricing' in claim.get('category', '').casefold()
        and claim.get('status') == 'Active'
        and claim.get('expiry', '') >= datetime.now(timezone.utc).date().isoformat()
    ]
    for match in re.finditer(r'\$\s*(\d+(?:\.\d{1,2})?)\s*(?:/\s*(?:seat|user|month|mo|year|yr)|per\s+(?:seat|user|month|year))?', content, re.I):
        amount = match.group(1)
        if any(amount in re.findall(r'\d+(?:\.\d+)?', claim.get('statement', '')) for claim in active_pricing):
            continue
        if any(f.get('wrong', '').casefold() == match.group(0).casefold() for f in findings):
            continue
        expired_match = next((claim for claim in claims if 'pricing' in claim.get('category', '').casefold() and claim.get('status') != 'Active' and amount in re.findall(r'\d+(?:\.\d+)?', claim.get('statement', ''))), None)
        findings.append({
            'id': f"FND-PRICE-{len(findings)+1}",
            'location': f"Offset {match.start()}..{match.end()}",
            'category': 'Expired Claim / Missing Current Proof',
            'title': 'Expired demo price — cannot verify' if expired_match else 'Price not found in active claim ledger',
            'severity': 'High',
            'wrong': match.group(0),
            'why': 'A price mention must match a current approved pricing claim. Confirm this amount with Finance before publication.',
            'sourceId': expired_match.get('id', '') if expired_match else 'UNVERIFIED-PRICE',
            'official': expired_match.get('evidence', 'No active approved pricing claim matches this amount.') if expired_match else 'No active approved pricing claim matches this amount.',
            'owner': expired_match.get('owner', 'Finance Operations') if expired_match else 'Finance Operations',
            'expiry': expired_match.get('expiry', '') if expired_match else '',
            'state': 'cannot verify - needs human check',
            'confidence': 100,
            'fix': '',
            'actionStatus': 'pending'
        })

    # 1. Check Founding Year / Legal Establishment
    founding_matches = list(re.finditer(r'(?:founded|established|founding\s*year)\s*(?:in|—|-|:)?\s*(\b(?:18|19|20)\d{2}\b)', content, re.I))
    for m in founding_matches:
        year_claimed = m.group(1)
        if year_claimed != "2012":
            findings.append({
                "id": f"FND-YR-{len(findings)+1}",
                "location": f"Offset {m.start()}..{m.end()}",
                "category": "Outdated / Conflicting Fact",
                "title": "Founding year mismatch",
                "severity": "High",
                "wrong": m.group(0),
                "why": f"Founding year claimed ({year_claimed}) conflicts with official incorporation records (2012).",
                "sourceId": "CLM-002",
                "official": "Delaware Certificate of Incorporation #4829104: Established in 2012.",
                "owner": "Marcus Vance (Chief Legal Counsel)",
                "expiry": "2030-01-01",
                "state": "source-verified",
                "confidence": 98,
                "fix": m.group(0).replace(year_claimed, "2012"),
                "actionStatus": "pending"
            })

    # 2. Check Onboarding / Performance Metric Claim (from PDF Example page 6)
    perf_match = re.search(r'cuts?\s+onboarding(?:\s+time)?\s+by\s+(\d+)%', content, re.I)
    if perf_match:
        pct_num = int(perf_match.group(1))
        if pct_num > 20:
            findings.append({
                "id": f"FND-PRF-{len(findings)+1}",
                "location": f"Offset {perf_match.start()}..{perf_match.end()}",
                "category": "Unsupported Performance Claim",
                "title": f"Unsubstantiated onboarding reduction claim ({pct_num}% vs approved 20%)",
                "severity": "High",
                "wrong": perf_match.group(0),
                "why": f"Approved claim benchmark is up to 20%. No approved source in the claims ledger validates {pct_num}%.",
                "sourceId": "CLM-001",
                "official": "Claim CLM-001: Cuts onboarding time by up to 20% (Benchmark Study Section 4.2).",
                "owner": "Sarah Jenkins (VP Product)",
                "expiry": "2027-12-31",
                "state": "source-verified",
                "confidence": 96,
                "fix": "cuts onboarding time by up to 20%",
                "actionStatus": "pending"
            })

    # 3. Check for Expired Claims (e.g. $49 pricing) -> Triggers explicit "Cannot verify - needs human check"
    if ("$49" in content or "49/month" in content_lower or "49 dollars" in content_lower) and not any(f.get("sourceId") == "CLM-005" for f in findings):
        findings.append({
            "id": f"FND-EXP-{len(findings)+1}",
            "location": "Pricing section",
            "category": "Expired Claim / Missing Current Proof",
            "title": "Pricing claim cannot be verified (Source expired)",
            "severity": "High",
            "wrong": "$49/month",
            "why": "The referenced pricing catalog (CLM-005) expired on 2025-01-01. As required by BrandWise reliability standards, expired evidence cannot be accepted and requires human verification.",
            "sourceId": "CLM-005",
            "official": "Claim CLM-005: Starter tier was $49/mo (EXPIRED 2025-01-01). Current 2026 catalog is $79/mo.",
            "owner": "Finance Operations",
            "expiry": "2025-01-01 (EXPIRED)",
            "state": "cannot verify - needs human check",
            "confidence": 95,
            "fix": "starting at $79 per seat per month (verify with pricing desk)",
            "actionStatus": "pending"
        })

    # 4. Prohibited Terminology & Superlatives Checks (Deterministic + AI Style Rules)
    prohibited_terms = guidelines.get("terminology", {}).get("prohibited", [])
    for p in prohibited_terms:
        raw_term = p["term"]
        term = raw_term.casefold()

        # Special case: brand name casing (e.g. "Brandwise" should only flag if NOT "BrandWise")
        if term == "brandwise":
            for bad_casing in re.finditer(r'\bbrandwise\b', content, re.I):
                if bad_casing.group(0) != "BrandWise":
                    findings.append({
                        "id": f"FND-TRM-{len(findings)+1}",
                        "location": f"Offset {bad_casing.start()}",
                        "category": "Brand Consistency",
                        "title": "Brand name capitalization error",
                        "severity": "Medium",
                        "wrong": bad_casing.group(0),
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
                "id": f"FND-TRM-{len(findings)+1}",
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

    # 5. Generic Superlatives & Guarantees without Evidence (PDF page 3, 4, 6)
    superlatives_pattern = r'\b(world[’\']?s\s+(?:leading|best|fastest|number\s*one)|#(?:1|one)\s+(?:provider|platform|solution)|100%\s+(?:guaranteed|accurate|reliable)|guaranteed\s+(?:results|success|growth)|trusted\s+by\s+every\s+(?:company|enterprise|team))\b'
    for match in re.finditer(superlatives_pattern, content, re.I):
        claim_snippet = match.group(0)
        # Check if already caught
        if not any(f["wrong"].casefold() == claim_snippet.casefold() for f in findings):
            findings.append({
                "id": f"FND-SUP-{len(findings)+1}",
                "location": f"Offset {match.start()}..{match.end()}",
                "category": "Unsupported Marketing Claim",
                "title": f"Unsubstantiated claim: '{claim_snippet}'",
                "severity": "High" if "guarantee" in claim_snippet.lower() or "100%" in claim_snippet else "Medium",
                "wrong": claim_snippet,
                "why": f"'{claim_snippet}' lacks an approved, current entry in the claims ledger. Under BrandWise governance, superlatives require documented proof.",
                "sourceId": "UNVERIFIED-CLAIM",
                "official": "No matching approved claim found in the BrandWise ledger.",
                "owner": "Legal & Brand Review",
                "expiry": "N/A",
                "state": "cannot verify - needs human check",
                "confidence": 92,
                "fix": "evidence-backed statement (e.g., 'proven enterprise platform')",
                "actionStatus": "pending"
            })

    # 6. Brand Name Capitalization Check ("Brandwise" vs "BrandWise")
    for bad_casing in re.finditer(r'\bBrandwise\b', content):
        if not any(f["wrong"] == "Brandwise" for f in findings):
            findings.append({
                "id": f"FND-CAS-{len(findings)+1}",
                "location": f"Offset {bad_casing.start()}",
                "category": "Brand Consistency",
                "title": "Brand name capitalization error",
                "severity": "Medium",
                "wrong": "Brandwise",
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

    # 7. Check Mandatory Disclaimer for Marketing Copy / Websites (if applicable)
    req_disc = guidelines.get("requiredDisclaimer", "").strip()
    if channel in ["Website Copy", "Digital Ad", "Marketing Email", "Social Post"] and req_disc:
        normalized_copy = re.sub(r"\s+", " ", content_lower).strip()
        normalized_disclaimer = re.sub(r"\s+", " ", req_disc.casefold()).strip()
        if normalized_disclaimer not in normalized_copy:
            findings.append({
                "id": f"FND-DISC-{len(findings)+1}",
                "location": "Document footer",
                "category": "Missing Legal Notice",
                "title": "Mandatory disclaimer missing or incomplete",
                "severity": "High",
                "wrong": "No disclaimer appended",
                "why": "Outward marketing copy must contain the full approved terms and performance disclaimer, not only a shortened terms notice.",
                "sourceId": "GL-LEGAL-01",
                "official": req_disc,
                "owner": "Compliance Team",
                "expiry": "Active guideline",
                "state": "source-verified",
                "confidence": 100,
                "fix": req_disc,
                "actionStatus": "pending"
            })

    if accessibility_result['readingGrade'] is not None and not accessibility_result['readabilityPass']:
        findings.append({
            'id': f"FND-READ-{len(findings)+1}",
            'location': 'Full copy',
            'category': 'Accessibility - Readability',
            'title': f"Estimated reading grade exceeds {accessibility_result['maxGrade']:g}",
            'severity': 'Medium',
            'wrong': content[:160],
            'why': f"Estimated Flesch-Kincaid grade is {accessibility_result['readingGrade']}; simplify long sentences and words to meet the configured limit.",
            'sourceId': 'GL-A11Y-READABILITY',
            'official': f"Guideline maximum: grade {accessibility_result['maxGrade']:g}. Syllables are estimated heuristically.",
            'owner': 'Accessibility Guidelines',
            'expiry': 'Active guideline',
            'state': 'source-verified',
            'confidence': 85,
            'confidenceBasis': 'Heuristic Flesch-Kincaid estimate; syllables approximated',
            'actionStatus': 'pending'
        })
    for heading_issue in accessibility_result['headingIssues']:
        findings.append({
            'id': f"FND-HEAD-{len(findings)+1}",
            'location': 'Heading hierarchy',
            'category': 'Accessibility - Heading order',
            'title': 'Heading hierarchy needs review',
            'severity': 'Medium',
            'wrong': heading_issue['text'],
            'why': heading_issue['message'],
            'sourceId': 'GL-A11Y-HEADINGS',
            'official': 'Configured guidance requires heading levels to follow a logical hierarchy.',
            'owner': 'Accessibility Guidelines',
            'expiry': 'Active guideline',
            'state': 'source-verified',
            'confidence': 100,
            'actionStatus': 'pending'
        })

    # Clear, deterministic risk patterns for absolute outcomes that a ledger cannot substantiate.
    # These are deliberately framed as human-review flags, not factual conclusions.
    absolute_patterns = [
        r'\b\d+(?:\.\d+)?\s*x\s+(?:faster|more|higher|greater|increase|improvement|engagement|growth|results?)\b',
        r'\b100\s*%\s*(?:safe|effective|risk[- ]free|accurate|reliable)\b',
        r'\b(?:permanently|instantly|in\s+(?:\d+|one|two|three)\s+days?)\b',
        r'\brecommended\s+by\s+every\b',
        r'\bguarantee[sd]?\s+(?:an?\s+)?(?:job|employment|success|growth|results?)\b',
    ]
    for pattern in absolute_patterns:
        for match in re.finditer(pattern, content, re.I):
            if any(f.get('wrong', '').casefold() == match.group(0).casefold() for f in findings):
                continue
            findings.append({
                'id': f'FND-ABS-{len(findings)+1}',
                'location': f'Offset {match.start()}..{match.end()}',
                'category': 'Unsupported Guarantee / Absolute Claim',
                'title': 'Outcome claim needs supporting evidence',
                'severity': 'High',
                'wrong': match.group(0),
                'why': 'This quantified, universal, or guaranteed outcome is not supported by an active matching claim in the local ledger. Treat it as unverified until a reviewer confirms evidence.',
                'sourceId': 'UNVERIFIED-CLAIM',
                'official': 'No current approved ledger claim substantiates this wording.',
                'owner': 'Brand / Legal Review',
                'expiry': 'No active evidence linked',
                'state': 'cannot verify - needs human check',
                'confidence': 88,
                'confidenceBasis': 'Deterministic risk pattern; evidence still needs human review',
                'fix': 'Remove or qualify this outcome unless current evidence supports it.',
                'actionStatus': 'pending'
            })

    # Compute Compliance Score: deductions based on severity
    for finding in findings:
        if finding.get('category') == 'Accessibility - Readability':
            continue
        finding['confidence'] = 100
        finding['confidenceBasis'] = 'Exact deterministic rule match'

    score = compliance_score(findings, strictness)
    # Calculate average confidence
    conf = int(sum(f.get("confidence", 90) for f in findings) / len(findings)) if findings else 98

    return {
        "score": score,
        "confidence": conf,
        "findings": findings,
        "accessibility": accessibility_result,
        "strictness": strictness,
    }


class Handler(BaseHTTPRequestHandler):
    def send_error(self, code, message=None, explain=None):
        if urllib.parse.urlparse(self.path).path.startswith('/api/'):
            return self.send_json(code, {'error': message or 'API request could not be completed.'})
        return super().send_error(code, message, explain)

    def send_json(self, status, value, cookie=None):
        payload = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/auth/roles':
            return self.send_json(200, accounts.ROLES)
        if path == '/api/auth/me':
            user = accounts.current_user(self.headers)
            return self.send_json(200, user) if user else self.send_json(401, {'error': 'Sign in first.'})
        if path.startswith('/api/') and path != '/api/health':
            user = accounts.current_user(self.headers)
            if not user:
                return self.send_json(401, {'error': 'Sign in first.'})
            if path == '/api/admin/team':
                if user['role'] != 'Admin':
                    return self.send_json(403, {'error': 'Administrator access required.'})
                return self.send_json(200, {'users': accounts.list_users()})
            if path == '/api/keys' and user['role'] != 'Admin':
                return self.send_json(403, {'error': 'Administrator access required.'})

        if path == '/api/audit-preferences':
            return self.send_json(200, get_workspace_audit_preferences())

        if path == '/api/health':
            return self.send_json(200, {
                'ok': True,
                'service': 'BrandWise Governance Platform API',
                'version': '2.4.0',
                'workingTitle': 'BrandWise',
                'preparedBy': 'Brand Wise',
                'engines': {
                    'rules': 'Deterministic WCAG 2.1 & Terminology Engine',
                    'claims': 'Claims Ledger & Expiry Verification Engine',
                    'llm': 'Disclosed External AI (Claude 3.5 Sonnet / Vision)',
                    'uncertaintyMode': 'Active ("Cannot verify - needs human check" enabled)'
                }
            })

        if path == '/api/audits':
            audits = get_audits()
            # Support filters: status, channel, role, agency, search
            if 'status' in query:
                st = query['status'][0]
                if st != 'all':
                    audits = [a for a in audits if a.get('status', '').casefold() == st.casefold()]
            if 'agency' in query:
                ag = query['agency'][0]
                if ag != 'all':
                    audits = [a for a in audits if a.get('agency', '').casefold() == ag.casefold()]
            if 'q' in query:
                q = query['q'][0].casefold()
                audits = [a for a in audits if q in a.get('title', '').casefold() or q in a.get('content', '').casefold() or q in a.get('id', '').casefold()]
            return self.send_json(200, {'records': audits, 'total': len(audits)})

        if path.startswith('/api/audits/'):
            audit_id = path.replace('/api/audits/', '').strip()
            audits = get_audits()
            found = next((a for a in audits if a.get('id') == audit_id), None)
            if found:
                return self.send_json(200, found)
            return self.send_json(404, {'error': f'Audit {audit_id} not found'})

        if path == '/api/claims':
            claims = get_claims()
            return self.send_json(200, {'claims': claims, 'total': len(claims)})

        if path == '/api/guidelines':
            guidelines = get_guidelines()
            return self.send_json(200, guidelines)

        if path == '/api/keys':
            return self.send_json(200, {'status': 'ok', 'keys': get_masked_keys()})

        if path == '/api/insights':
            audits = get_audits()
            claims = get_claims()
            # Aggregate Insights as described in PDF Section 03 & 06
            all_findings = [f for a in audits for f in a.get('findings', [])]
            category_counts = {}
            for f in all_findings:
                cat = f.get('category', 'Other')
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # Ambiguous guidelines detection (PDF Page 6: "unclear-guideline detection highlights rules frequently disputed or dismissed")
            dismissed_findings = [f for f in all_findings if f.get('actionStatus') == 'dismissed']
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

            return self.send_json(200, {
                "totalAudits": len(audits),
                "totalFindings": len(all_findings),
                "categoryBreakdown": category_counts,
                "ambiguousRules": ambiguous_rules,
                "agencyStats": agency_stats,
                "impactEvidence": impact_evidence
            })

        # Serve static HTML or assets
        if path in ('/', '/' + PAGE, '/index.html'):
            target_file = ROOT / PAGE
            if not target_file.exists():
                target_file = ROOT / 'index.html'
            if target_file.exists():
                body = target_file.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

        self.send_error(404, "Page or endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.send_json(400, {'error': 'Invalid request length'})
        if size < 0 or size > 15 * 1024 * 1024:
            return self.send_json(413, {'error': 'Request exceeds 15 MB'})
        body_bytes = self.rfile.read(size) if size > 0 else b'{}'
        try:
            data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
        except Exception:
            return self.send_json(400, {'error': 'Invalid JSON request payload'})

        if not isinstance(data, dict):
            return self.send_json(400, {'error': 'Expected a JSON object'})
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            return self.send_json(403, {'error': 'Open BrandWise to submit this request.'})
        origin = self.headers.get('Origin')
        if origin and urllib.parse.urlparse(origin).netloc.casefold() != self.headers.get('Host', '').casefold():
            return self.send_json(403, {'error': 'Request origin is not allowed.'})
        if path == '/api/auth/password-reset/send':
            if not allow_otp_request(self.client_address[0]):
                return self.send_json(429, {'error': 'Too many verification requests. Wait 10 minutes and try again.'})
            try:
                accounts.send_password_reset_otp(data.get('email'))
            except accounts.EmailDeliveryError as exc:
                return self.send_json(503, {'error': str(exc)})
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True, 'message': 'If an account uses that email, a reset code has been sent.'})
        if path == '/api/auth/password-reset':
            try:
                accounts.reset_password_with_email_otp(data.get('email'), data.get('code'), data.get('newPassword'))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True})
        if path == '/api/auth/send-otp':
            if not allow_otp_request(self.client_address[0]):
                return self.send_json(429, {'error': 'Too many verification requests. Wait 10 minutes and try again.'})
            try:
                accounts.send_email_otp(data.get('email'))
            except accounts.EmailDeliveryError as exc:
                return self.send_json(503, {'error': str(exc)})
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True})
        if path == '/api/auth/verify-otp':
            try:
                accounts.verify_email_otp(data.get('email'), data.get('code'))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True})
        if path == '/api/auth/register':
            try:
                accounts.register(data)
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(201, {'ok': True})
        if path == '/api/auth/login':
            client_ip = self.client_address[0]
            if login_is_limited(client_ip):
                return self.send_json(429, {'error': 'Too many failed sign-in attempts. Wait 15 minutes and try again.'})
            token = accounts.login(data)
            if not token:
                record_login_failure(client_ip)
                return self.send_json(401, {'error': 'Username or password is incorrect.'})
            clear_login_failures(client_ip)
            secure = '; Secure' if self.headers.get('X-Forwarded-Proto', '').casefold() == 'https' else ''
            return self.send_json(200, {'ok': True}, f'brandwise_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={accounts.SESSION_AGE}{secure}')
        user = accounts.current_user(self.headers)
        if not user:
            return self.send_json(401, {'error': 'Sign in first.'})
        if path == '/api/auth/profile':
            try:
                return self.send_json(200, accounts.update_profile(self.headers, data))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/auth/change-password':
            try:
                accounts.change_password(self.headers, data.get('currentPassword'), data.get('newPassword'))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True})
        if path == '/api/auth/delete':
            try:
                accounts.delete_account(self.headers, data.get('password'))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True}, 'brandwise_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0')
        if path == '/api/audit-preferences':
            try:
                return self.send_json(200, set_workspace_audit_preferences(data))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/auth/logout':
            accounts.logout(self.headers)
            return self.send_json(200, {'ok': True}, 'brandwise_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0')
        if path in ('/api/keys', '/api/keys/test', '/api/reset') and user['role'] != 'Admin':
            return self.send_json(403, {'error': 'Administrator access required.'})
        if path in ('/api/claims', '/api/guidelines') and user['role'] not in ('Brand Manager', 'Admin'):
            return self.send_json(403, {'error': 'Brand Manager or Admin access required.'})
        if path == '/api/import':
            try:
                return self.send_json(200, extract_document(data))
            except Exception as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/accessibility':
            content = data.get('content')
            if not isinstance(content, str) or not content.strip():
                return self.send_json(400, {'error': 'Enter copy before running accessibility checks.'})
            return self.send_json(200, check_text_accessibility(content, get_guidelines()))

        # 1. Create a new audit / Run Automated Check
        if path == '/api/audits':
            content = data.get('content', '').strip()
            if not content:
                return self.send_json(400, {'error': 'content is required'})

            channel = data.get('channel', 'Website Copy')
            title = data.get('title') or content.splitlines()[0][:70] or 'Brand Review Draft'
            creator = user['name']
            agency = user['organization']
            role = user['role']

            # Run BrandWise Multi-Engine Evaluation
            audit_settings = get_workspace_audit_preferences()
            strictness = audit_settings['strictness']
            passing_threshold = audit_settings['passingThreshold']
            check_result = run_brandwise_checks(content, channel=channel, strictness=strictness)
            if strictness == 'strict':
                for multiplier in re.finditer(r'\b\d+(?:\.\d+)?\s*x\b', content, re.I):
                    if not any(multiplier.group(0).casefold() in f.get('wrong', '').casefold() for f in check_result['findings']):
                        check_result['findings'].append({
                            'id': f"FND-MULT-{len(check_result['findings'])+1}",
                            'location': f'Offset {multiplier.start()}..{multiplier.end()}',
                            'category': 'Unverified Performance Multiplier',
                            'title': 'Performance multiplier requires a matching source',
                            'severity': 'High', 'wrong': multiplier.group(0),
                            'why': 'Strict mode flags quantified multipliers unless a current approved ledger claim supports the figure.',
                            'sourceId': 'UNVERIFIED-CLAIM',
                            'official': 'No matching multiplier is present in the active claims ledger.',
                            'owner': 'Brand / Legal Review', 'expiry': 'No active evidence linked',
                            'state': 'cannot verify - needs human check', 'confidence': 88,
                            'confidenceBasis': 'Strict-mode deterministic pattern; evidence needs human review',
                            'fix': 'Replace with a quantified statement supported by an approved source.',
                            'actionStatus': 'pending'
                        })
            ai_findings, ai_status = gemini_review(content, get_current_ai_reference_claims(), get_guidelines()) if data.get('useAI') is True else ([], 'AI review not requested; deterministic checks only.')
            check_result['findings'].extend(ai_findings)
            check_result['score'] = compliance_score(check_result['findings'], strictness)
            confidence_values = [f.get('confidence') if isinstance(f.get('confidence'), (int, float)) else 100 for f in check_result['findings']]
            check_result['confidence'] = int(sum(confidence_values) / len(confidence_values)) if confidence_values else 98

            audit_id = 'BW-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
            now_iso = datetime.now(timezone.utc).isoformat()

            new_record = {
                'id': audit_id,
                'title': title,
                'channel': channel,
                'type': channel,
                'creator': creator,
                'agency': agency,
                'role': role,
                'status': 'Review required' if check_result['score'] < passing_threshold else 'Ready for review',
                'date': now_iso,
                'score': check_result['score'],
                'confidence': check_result['confidence'],
                'passingThreshold': passing_threshold,
                'passedThreshold': check_result['score'] >= passing_threshold,
                'settings': {'strictness': strictness, 'passingThreshold': passing_threshold, 'useAI': data.get('useAI') is True},
                'aiStatus': ai_status,
                'accessibility': check_result['accessibility'],
                'content': content,
                'reference': data.get('reference', 'BrandWise Standard Corporate Claims & Guidelines v3.2'),
                'findings': check_result['findings'],
                'revisions': [
                    {
                        'version': 'v1',
                        'author': creator,
                        'timestamp': now_iso,
                        'text': content,
                        'notes': 'Initial submission for automated brand audit'
                    }
                ],
                'comments': [],
                'auditTrail': [
                    {'action': 'Draft Submitted', 'user': creator, 'timestamp': now_iso, 'note': f'Channel: {channel}'},
                    {'action': 'Automated Checks Completed', 'user': 'BrandWise Hybrid Engine', 'timestamp': now_iso, 'note': f'{len(check_result["findings"])} issues · {strictness.title()} mode · {passing_threshold}% pass threshold · score {check_result["score"]}%'}
                ]
            }

            audits = get_audits()
            audits.insert(0, new_record)
            save_json(DB, audits)
            return self.send_json(201, new_record)

        # 2. Audit Actions: Accept, Edit, Dismiss, Report Incorrect Flag, Change State, Add Comment
        if path.startswith('/api/audits/') and path.endswith('/action'):
            audit_id = path.replace('/api/audits/', '').replace('/action', '').strip()
            audits = get_audits()
            target_audit = next((a for a in audits if a.get('id') == audit_id), None)
            if not target_audit:
                return self.send_json(404, {'error': f'Audit {audit_id} not found'})

            action_type = data.get('action') # 'accept_fix', 'edit_fix', 'dismiss_fix', 'change_state', 'add_comment', 'report_incorrect_flag'
            now_iso = datetime.now(timezone.utc).isoformat()
            user_name = user['name']
            if action_type == 'change_state' and user['role'] not in ('Reviewer', 'Brand Manager', 'Admin'):
                return self.send_json(403, {'error': 'Reviewer, Brand Manager, or Admin access required.'})

            if action_type in ('accept_fix', 'edit_fix'):
                finding_id = data.get('findingId')
                finding = next((f for f in target_audit.get('findings', []) if f.get('id') == finding_id), None)
                if not finding:
                    return self.send_json(404, {'error': 'Finding not found.'})
                fix_text = data.get('fixText', finding.get('fix', '')).strip()
                if not fix_text:
                    return self.send_json(400, {'error': 'Provide replacement wording.'})
                current_text = target_audit.get('content', '')
                wrong = finding.get('wrong', '')
                if wrong and fix_text and wrong in current_text:
                    new_text = current_text.replace(wrong, fix_text, 1)
                    target_audit['content'] = new_text
                    revisions = target_audit.setdefault('revisions', [])
                    revisions.append({
                        'version': f"v{len(revisions)+1}",
                        'author': user_name,
                        'timestamp': now_iso,
                        'text': new_text,
                        'notes': f"{'Edited' if action_type == 'edit_fix' else 'Accepted'} fix for finding {finding_id}: '{wrong}' -> '{fix_text}'"
                    })
                finding['actionStatus'] = 'edited' if action_type == 'edit_fix' else 'accepted'
                finding['appliedFix'] = fix_text
                target_audit['auditTrail'].append({
                    'action': 'Fix Edited' if action_type == 'edit_fix' else 'Fix Accepted',
                    'user': user_name,
                    'timestamp': now_iso,
                    'note': f"{'Edited' if action_type == 'edit_fix' else 'Accepted'} suggested fix for {finding_id}"
                })

            elif action_type == 'dismiss_fix':
                finding_id = data.get('findingId')
                reason = data.get('reason', 'Dismissed by creator')
                for f in target_audit.get('findings', []):
                    if f.get('id') == finding_id:
                        f['actionStatus'] = 'dismissed'
                        f['dismissalReason'] = reason
                target_audit['auditTrail'].append({
                    'action': 'Finding Dismissed',
                    'user': user_name,
                    'timestamp': now_iso,
                    'note': f"Dismissed {finding_id}. Reason: {reason}"
                })

            elif action_type == 'report_incorrect_flag':
                finding_id = data.get('findingId')
                feedback = data.get('feedback', 'Reported as false positive')
                target_finding = next((f for f in target_audit.get('findings', []) if f.get('id') == finding_id), None)
                if not target_finding:
                    return self.send_json(404, {'error': 'Finding not found.'})
                target_finding['reportedIncorrect'] = True
                target_finding['incorrectFeedback'] = str(feedback)[:500]
                target_audit['auditTrail'].append({
                    'action': 'Reported Incorrect Flag',
                    'user': user_name,
                    'timestamp': now_iso,
                    'note': f"False positive reported on {finding_id}: {str(feedback)[:500]}"
                })

            elif action_type == 'change_state':
                new_state = data.get('state') # 'Draft', 'Auto-checked', 'In review', 'Changes requested', 'Approved', 'Published'
                note = data.get('note', '')
                valid_states = ['Draft', 'Auto-checked', 'In review', 'Changes requested', 'Approved', 'Published']
                if new_state in valid_states:
                    old_state = target_audit.get('status')
                    target_audit['status'] = new_state
                    target_audit['auditTrail'].append({
                        'action': f"State Changed: {old_state} -> {new_state}",
                        'user': user_name,
                        'timestamp': now_iso,
                        'note': note or f"Moved to {new_state}"
                    })

            elif action_type == 'add_comment':
                comment_text = data.get('text', '').strip()
                if comment_text:
                    cid = f"COM-{len(target_audit.get('comments', []))+1}"
                    target_audit.setdefault('comments', []).append({
                        'id': cid,
                        'author': user_name,
                        'role': data.get('role', 'Reviewer'),
                        'timestamp': now_iso,
                        'text': comment_text
                    })
                    target_audit['auditTrail'].append({
                        'action': 'Comment Added',
                        'user': user_name,
                        'timestamp': now_iso,
                        'note': comment_text[:60]
                    })

            save_json(DB, audits)
            return self.send_json(200, target_audit)

        # 3. Add or Update Claim in Ledger
        if path == '/api/claims':
            statement = data.get('statement', '').strip()
            if not statement:
                return self.send_json(400, {'error': 'statement is required'})
            claims = get_claims()
            cid = data.get('id') or f"CLM-{len(claims)+1:03d}"
            existing = next((c for c in claims if c['id'] == cid), None)
            if existing:
                existing.update(data)
            else:
                data['id'] = cid
                data.setdefault('status', 'Active')
                claims.append(data)
            save_json(CLAIMS_DB, claims)
            return self.send_json(200, {'success': True, 'claim': data})

        # 4. Update Guidelines
        if path == '/api/guidelines':
            save_json(GUIDELINES_DB, data)
            return self.send_json(200, {'success': True, 'guidelines': data})

        # 5. Simulated Slack Webhook Notification (PDF Page 8, Phase 2)
        if path == '/api/notify/slack':
            channel_name = data.get('channel', '#brand-approvals')
            title = data.get('title', 'Brand Review Update')
            status_text = data.get('status', 'In Review')
            doc_id = data.get('docId', 'BW-2026-001')
            actor = data.get('actor', 'Alex Rivera')
            message = data.get('message', 'Content review update triggered.')

            slack_payload = {
                "channel": channel_name,
                "username": "BrandWise Bot",
                "icon_emoji": ":shield:",
                "attachments": [
                    {
                        "color": "#0879d1" if status_text == "Approved" else "#e97821" if status_text == "Changes requested" else "#138a69",
                        "title": f"[{status_text.upper()}] {title} ({doc_id})",
                        "title_link": f"http://127.0.0.1:8765/#workspace?id={doc_id}",
                        "text": f"*{actor}*: {message}",
                        "fields": [
                            {"title": "Review State", "value": status_text, "short": True},
                            {"title": "Platform", "value": "BrandWise Governance", "short": True}
                        ],
                        "footer": "BrandWise Pre-Publication Governance · Notification Engine",
                        "ts": int(datetime.now(timezone.utc).timestamp())
                    }
                ]
            }
            webhook = os.environ.get('SLACK_WEBHOOK_URL', '').strip()
            if not webhook:
                return self.send_json(503, {'sent': False, 'error': 'Configure SLACK_WEBHOOK_URL locally before sending notifications.'})
            if not webhook.startswith('https://hooks.slack.com/services/'):
                return self.send_json(400, {'sent': False, 'error': 'Invalid Slack webhook URL'})
            try:
                request = urllib.request.Request(webhook, data=json.dumps(slack_payload).encode(), headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request, timeout=10) as response:
                    delivered = response.status == 200 and response.read().strip() == b'ok'
                return self.send_json(200 if delivered else 502, {'sent': delivered})
            except Exception:
                return self.send_json(502, {'sent': False, 'error': 'Slack delivery failed. Check webhook configuration and retry.'})

        # 6. API Keys Configuration & Management
        if path == '/api/keys':
            updates = {}
            if 'anthropicApiKey' in data: updates['ANTHROPIC_API_KEY'] = data['anthropicApiKey']
            if 'geminiApiKey' in data: updates['GEMINI_API_KEY'] = data['geminiApiKey']
            if 'openaiApiKey' in data: updates['OPENAI_API_KEY'] = data['openaiApiKey']
            if 'slackWebhookUrl' in data: updates['SLACK_WEBHOOK_URL'] = data['slackWebhookUrl']
            saved = save_env_keys(updates)
            return self.send_json(200 if saved else 500, {'success': saved, 'message': 'API keys updated and saved to .env', 'keys': get_masked_keys()})

        if path == '/api/keys/test':
            provider = data.get('provider', '')
            api_key = data.get('apiKey', '')
            res = test_external_api_key(provider, api_key)
            return self.send_json(200, res)

        # 7. Reset Database to Default Proposal Seeds
        if path == '/api/reset':
            save_json(DB, DEFAULT_AUDITS)
            save_json(CLAIMS_DB, DEFAULT_CLAIMS)
            save_json(GUIDELINES_DB, DEFAULT_GUIDELINES)
            save_json(AUDIT_PREFERENCES_DB, DEFAULT_AUDIT_PREFERENCES)
            return self.send_json(200, {'ok': True, 'message': 'Demo data reset to official BrandWise proposal seed'})

        self.send_error(404, "Endpoint not found")

    def log_message(self, fmt, *args):
        # Concise logging
        print('%s - %s' % (self.address_string(), fmt % args))


def init_storage():
    if not DB.exists():
        save_json(DB, DEFAULT_AUDITS)
    if not CLAIMS_DB.exists():
        save_json(CLAIMS_DB, DEFAULT_CLAIMS)
    if not GUIDELINES_DB.exists():
        save_json(GUIDELINES_DB, DEFAULT_GUIDELINES)
    if not AUDIT_PREFERENCES_DB.exists():
        save_json(AUDIT_PREFERENCES_DB, DEFAULT_AUDIT_PREFERENCES)


if __name__ == '__main__':
    init_storage()
    threading.Thread(target=session_cleanup_loop, name='session-cleanup', daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    print('========================================================')
    print('  BrandWise — Brand Governance Platform Backend')
    print('  Running at: http://127.0.0.1:8765')
    print('========================================================')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
