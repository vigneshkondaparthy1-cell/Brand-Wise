import accounts
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone, timedelta
import threading
import time
import os
import json
import gzip
import re
import urllib.parse
import urllib.request
import urllib.error
import html as html_lib
import uuid
import database
from document_ingestion import extract_document
from gemini_review import review as gemini_review
import review_validation

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'audit-data.json'
CLAIMS_DB = ROOT / 'claims-data.json'
GUIDELINES_DB = ROOT / 'guidelines-data.json'
INSIGHTS_DB = ROOT / 'insights-data.json'
AUDIT_PREFERENCES_DB = ROOT / 'workspace-audit-preferences.json'
ENV_FILE = ROOT / '.env'
PAGE = 'The-Final-Draft-Hackathon-Updated.html'
PAGE_CACHE = {}
PAGE_CACHE_LOCK = threading.Lock()
OTP_REQUESTS = {}
OTP_REQUESTS_LOCK = threading.Lock()
OTP_REQUEST_WINDOW_SECONDS = 600
OTP_REQUEST_MAXIMUM = 5
AUDIT_PREFERENCES_LOCK = threading.Lock()
JSON_STORAGE_LOCK = threading.RLock()
DEFAULT_AUDIT_PREFERENCES = {'strictness': 'balanced', 'passingThreshold': 80}

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
    }

def save_env_keys(keys_dict):
    for k, v in keys_dict.items():
        if v is not None and v != "••••••••":
            os.environ[k] = v.strip()
    try:
        updates = {key: os.environ.get(key, '') for key in keys_dict}
        lines = ENV_FILE.read_text(encoding='utf-8').splitlines() if ENV_FILE.exists() else []
        written = set()
        output = []
        for line in lines:
            match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=', line)
            if match and match.group(1) in updates:
                key = match.group(1)
                output.append(f'{key}={updates[key]}')
                written.add(key)
            else:
                output.append(line)
        for key, value in updates.items():
            if key not in written:
                output.append(f'{key}={value}')
        ENV_FILE.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
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
    if database.uses_postgres():
        return database.get_json(path.name, fallback, path)
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        return fallback
    except Exception:
        return fallback


def save_json(path, data):
    if database.uses_postgres():
        return database.save_json(path.name, data)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        with JSON_STORAGE_LOCK:
            temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
            temporary.write_text(payload, encoding='utf-8')
            os.replace(temporary, path)
        return True
    except Exception:
        return False


def get_audits():
    audits = load_json(DB, DEFAULT_AUDITS)
    sample_ids = {item.get('id') for item in DEFAULT_AUDITS}
    for audit in audits:
        if audit.get('id') in sample_ids:
            audit.setdefault('sampleData', True)
    return audits


def audits_visible_to_user(audits, user):
    """Enforce workspace membership; agency drafts stay private to their submitter."""
    username = (user.get('username') or '').casefold()
    company_id = user.get('activeCompanyId')
    member = bool(company_id and user.get('companyRole'))
    if user.get('role') == 'External Agency':
        return [a for a in audits if (a.get('creatorUsername') or '').casefold() == username]
    if member:
        return [a for a in audits if a.get('companyId') == company_id or
                (not a.get('companyId') and (a.get('creatorUsername') or '').casefold() == username)]
    return [a for a in audits if (a.get('creatorUsername') or '').casefold() == username]


def company_data_path(company_id, filename):
    safe_id = re.sub(r'[^A-Za-z0-9_-]', '_', str(company_id))[:100]
    folder = ROOT / 'workspace-data' / safe_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename


def claims_for_user(user):
    company_id = user.get('activeCompanyId')
    return load_json(company_data_path(company_id, 'claims-data.json'), load_json(CLAIMS_DB, DEFAULT_CLAIMS)) if company_id else get_claims()


def guidelines_for_user(user):
    company_id = user.get('activeCompanyId')
    return load_json(company_data_path(company_id, 'guidelines-data.json'), load_json(GUIDELINES_DB, DEFAULT_GUIDELINES)) if company_id else get_guidelines()


def save_company_json(user, filename, fallback_path, value):
    company_id = user.get('activeCompanyId')
    path = company_data_path(company_id, filename) if company_id else fallback_path
    return save_json(path, value)


def recheck_saved_audit(audit):
    prior = audit.get('findings', [])
    strictness = (audit.get('settings') or {}).get('strictness', 'balanced')
    checked = run_brandwise_checks(
        audit.get('content', ''), channel=audit.get('channel', 'Website Copy'),
        strictness=strictness, _claims=audit.get('claimsSnapshot', get_claims()),
        _guidelines=audit.get('guidelinesSnapshot', get_guidelines())
    )
    prior_state = {(f.get('wrong'), f.get('sourceId')): f for f in prior}
    for finding in checked['findings']:
        old = prior_state.get((finding.get('wrong'), finding.get('sourceId')))
        if old and old.get('actionStatus') in ('dismissed', 'reported-incorrect'):
            finding['actionStatus'] = old['actionStatus']
            if old.get('dismissalReason'):
                finding['dismissalReason'] = old['dismissalReason']
    audit['findings'] = checked['findings']
    audit['accessibility'] = checked['accessibility']
    audit['score'] = compliance_score(audit['findings'], strictness)
    threshold = int(audit.get('passingThreshold', 80))
    audit['passedThreshold'] = audit['score'] >= threshold
    audit['status'] = 'Review required' if not audit['passedThreshold'] else 'Ready for review'


def get_workspace_audit_preferences(company_id=None):
    with AUDIT_PREFERENCES_LOCK:
        path = company_data_path(company_id, 'audit-preferences.json') if company_id else AUDIT_PREFERENCES_DB
        saved = load_json(path, load_json(AUDIT_PREFERENCES_DB, DEFAULT_AUDIT_PREFERENCES) if company_id else DEFAULT_AUDIT_PREFERENCES)
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


def set_workspace_audit_preferences(data, company_id=None):
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
        path = company_data_path(company_id, 'audit-preferences.json') if company_id else AUDIT_PREFERENCES_DB
        if not save_json(path, settings):
            raise ValueError('Could not save the shared workspace audit preferences.')
    return settings


def compliance_score(findings, strictness='balanced'):
    penalties = {
        'lenient': {'Critical': 20, 'High': 10, 'Medium': 5, 'Low': 2},
        'balanced': {'Critical': 25, 'High': 15, 'Medium': 8, 'Low': 4},
        'strict': {'Critical': 30, 'High': 20, 'Medium': 10, 'Low': 5},
    }.get(strictness, {'Critical': 25, 'High': 15, 'Medium': 8, 'Low': 4})
    deductions = sum(penalties.get(f.get('severity', 'Medium'), 8) for f in findings)
    score = max(0, min(100, 100 - deductions))
    # Content with unresolved issues cannot receive a perfect score
    unresolved = any((f.get('actionStatus') or 'pending') == 'pending' for f in findings)
    if unresolved and score >= 100:
        score = 95
    return score


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


def evaluate_labelled_ruleset():
    """Measure the checked-in synthetic labeled set; never present it as production accuracy."""
    cases_path = ROOT / 'evaluation' / 'test_set.json'
    try:
        cases = json.loads(cases_path.read_text(encoding='utf-8'))
        claims = get_claims()
        guidelines = get_guidelines()
        by_label = {'compliant': [0, 0], 'noncompliant': [0, 0]}
        for case in cases:
            label = case.get('label')
            if label not in by_label or not isinstance(case.get('text'), str):
                continue
            flagged = bool(run_brandwise_checks(case['text'], channel=case.get('channel', 'Website Copy'), _claims=claims, _guidelines=guidelines)['findings'])
            total, errors = by_label[label]
            by_label[label] = [total + 1, errors + int(flagged != (label == 'noncompliant'))]
        compliant_count, false_flags = by_label['compliant']
        noncompliant_count, missed = by_label['noncompliant']
        return {
            'dataset': 'Checked-in synthetic labeled evaluation set',
            'caseCount': compliant_count + noncompliant_count,
            'compliantCases': compliant_count,
            'noncompliantCases': noncompliant_count,
            'detectionRate': round(100 * (noncompliant_count - missed) / noncompliant_count, 1) if noncompliant_count else None,
            'falseFlagRate': round(100 * false_flags / compliant_count, 1) if compliant_count else None,
            'productionBenchmark': False
        }
    except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError):
        return None


# Run multi-dimensional checks (Claims, Tone, Terminology, Banned words, Visual, WCAG, Uncertainty)
def run_brandwise_checks(content, channel="Website Copy", reference=None, strictness="balanced", _claims=None, _guidelines=None):
    claims = _claims if _claims is not None else get_claims()
    guidelines = _guidelines if _guidelines is not None else get_guidelines()
    findings = []
    content_lower = content.casefold()
    accessibility_result = check_text_accessibility(content, guidelines)

    # Check all exact prohibited phrases supplied by the approved claim ledger.
    for claim in claims:
        for phrase in claim.get("prohibitedPhrases", []):
            if not phrase:
                continue
            for match in re.finditer(re.escape(phrase), content, re.I):
                if any(f.get("location") == f"Offset {match.start()}..{match.end()}" for f in findings):
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
        if any(amount in re.findall(r'\$\s*(\d+(?:\.\d{1,2})?)', claim.get('statement', '')) for claim in active_pricing):
            continue
        if any(f.get('wrong', '').casefold() == match.group(0).casefold() for f in findings):
            continue
        expired_match = next((claim for claim in claims if 'pricing' in claim.get('category', '').casefold() and claim.get('status') != 'Active' and amount in re.findall(r'\$\s*(\d+(?:\.\d{1,2})?)', claim.get('statement', ''))), None)
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

    # Read identity facts from the current claim ledger rather than embedding demo facts.
    identity_claim = next((claim for claim in claims
                           if 'company identity' in claim.get('category', '').casefold()
                           and claim.get('status') == 'Active'
                           and claim.get('expiry', '') >= datetime.now(timezone.utc).date().isoformat()), None)
    identity_year_match = re.search(r'(?:founded|established|founding\s*year)\s*(?:in|—|-|:)?\s*(\b(?:18|19|20)\d{2}\b)', identity_claim.get('statement', ''), re.I) if identity_claim else None
    identity_year = identity_year_match.group(1) if identity_year_match else None
    founding_matches = list(re.finditer(r'(?:founded|established|founding\s*year)\s*(?:in|—|-|:)?\s*(\b(?:18|19|20)\d{2}\b)', content, re.I))
    for m in founding_matches:
        year_claimed = m.group(1)
        if identity_year and year_claimed != identity_year:
            findings.append({
                "id": f"FND-YR-{len(findings)+1}",
                "location": f"Offset {m.start()}..{m.end()}",
                "category": "Outdated / Conflicting Fact",
                "title": "Founding year mismatch",
                "severity": "High",
                "wrong": m.group(0),
                "why": f"Founding year claimed ({year_claimed}) conflicts with the current company identity claim ({identity_year}).",
                "sourceId": identity_claim.get('id', ''),
                "official": f"{identity_claim.get('statement', '')}. Evidence: {identity_claim.get('evidence', 'No evidence recorded')}.",
                "owner": identity_claim.get('owner', ''),
                "expiry": identity_claim.get('expiry', ''),
                "state": "source-verified",
                "confidence": 100,
                "fix": m.group(0).replace(year_claimed, identity_year),
                "actionStatus": "pending"
            })

    # Compare numeric onboarding assertions with the current active ledger evidence.
    performance_claim = next((claim for claim in claims
                              if 'product performance' in claim.get('category', '').casefold()
                              and claim.get('status') == 'Active'
                              and claim.get('expiry', '') >= datetime.now(timezone.utc).date().isoformat()), None)
    benchmark_match = re.search(r'(?:cuts?|reduces?)\s+onboarding(?:\s+time)?\s+by\s+(?:up\s+to\s+)?(\d+(?:\.\d+)?)\s*%', performance_claim.get('statement', ''), re.I) if performance_claim else None
    max_supported = float(benchmark_match.group(1)) if benchmark_match else None
    perf_matches = list(re.finditer(r'cuts?\s+onboarding(?:\s+time)?\s+by\s+(\d+(?:\.\d+)?)\s*%', content, re.I))
    if max_supported is not None and performance_claim:
      for perf_match in perf_matches:
        pct_num = float(perf_match.group(1))
        if pct_num > max_supported:
            findings.append({
                "id": f"FND-PRF-{len(findings)+1}",
                "location": f"Offset {perf_match.start()}..{perf_match.end()}",
                "category": "Unsupported Performance Claim",
                "title": f"Unsubstantiated onboarding reduction claim ({pct_num:g}% vs approved {max_supported:g}%)",
                "severity": "High",
                "wrong": perf_match.group(0),
                "why": f"The current approved benchmark is up to {max_supported:g}%. No current ledger source validates {pct_num:g}%.",
                "sourceId": performance_claim.get('id', ''),
                "official": f"{performance_claim.get('statement', '')}. Evidence: {performance_claim.get('evidence', 'No evidence recorded')}.",
                "owner": performance_claim.get('owner', ''),
                "expiry": performance_claim.get('expiry', ''),
                "state": "source-verified",
                "confidence": 96,
                "fix": performance_claim.get('statement', ''),
                "actionStatus": "pending"
            })

    # 4. Prohibited Terminology & Superlatives Checks (Deterministic + AI Style Rules)
    prohibited_terms = guidelines.get("terminology", {}).get("prohibited", [])
    for p in prohibited_terms:
        raw_term = p["term"]
        term = raw_term.casefold()

        # Dynamic brand name casing from guidelines
        product_name = guidelines.get("productName", "BrandWise")
        if term == product_name.casefold():
            for bad_casing in re.finditer(r'\b' + re.escape(product_name) + r'\b', content, re.I):
                if bad_casing.group(0) != product_name:
                    if not any(f.get("location") == f"Offset {bad_casing.start()}..{bad_casing.end()}" for f in findings):
                        findings.append({
                            "id": f"FND-TRM-{len(findings)+1}",
                            "location": f"Offset {bad_casing.start()}..{bad_casing.end()}",
                            "category": "Brand Consistency",
                            "title": "Brand name capitalization error",
                            "severity": "Medium",
                            "wrong": bad_casing.group(0),
                            "why": f"Official brand identity requires camel-case capitalization: '{product_name}'.",
                            "sourceId": "GL-STYLE-01",
                            "official": f"Brand Identity Style Guide, Page 3: {product_name}.",
                            "owner": "Design Systems Team",
                            "expiry": "Active guideline",
                            "state": "source-verified",
                            "confidence": 100,
                            "confidenceBasis": "Exact deterministic rule match against guidelines",
                            "fix": product_name,
                            "actionStatus": "pending"
                        })
            continue

        for term_match in re.finditer(re.escape(raw_term), content, re.I):
            start_idx = term_match.start()
            actual_text = term_match.group(0)
            if any(f.get("location") == f"Offset {term_match.start()}..{term_match.end()}" for f in findings):
                continue
            findings.append({
                "id": f"FND-TRM-{len(findings)+1}",
                "location": f"Offset {term_match.start()}..{term_match.end()}",
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
                "confidence": 100,
                "confidenceBasis": "Exact deterministic rule match",
                "fix": p.get("suggested", ""),
                "actionStatus": "pending"
            })

    # 5. Generic Superlatives & Guarantees without Evidence (PDF page 3, 4, 6)
    superlatives_pattern = r'\b(world[’\']?s\s+(?:leading|best|fastest|number\s*one)|#(?:1|one)\s+(?:provider|platform|solution)|100%\s+(?:guaranteed|accurate|reliable)|guaranteed\s+(?:results|success|growth)|trusted\s+by\s+every\s+(?:company|enterprise|team))\b'
    for match in re.finditer(superlatives_pattern, content, re.I):
        claim_snippet = match.group(0)
        # Check if already caught
        if not any(f.get("location") == f"Offset {match.start()}..{match.end()}" for f in findings):
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

    # Compute Compliance Score: every active finding, including readability, counts.
    for finding in findings:
        if finding.get('confidence') is None:
            finding['confidence'] = 100
            finding['confidenceBasis'] = 'Exact deterministic rule match'

    score = compliance_score(findings, strictness)
    # Calculate average confidence
    conf = int(sum(f.get("confidence", 90) for f in findings) / len(findings)) if findings else None

    return {
        "score": score,
        "confidence": conf,
        "findings": findings,
        "accessibility": accessibility_result,
        "strictness": strictness,
    }


def storage_errors_as_503(handler):
    def wrapped(self, *args, **kwargs):
        try:
            return handler(self, *args, **kwargs)
        except database.DatabaseUnavailable:
            self.log_error('Configured PostgreSQL storage is unavailable.')
            return self.send_json(503, {'error': 'Workspace storage is temporarily unavailable. Please try again.'})
    return wrapped


class Handler(BaseHTTPRequestHandler):
    @staticmethod
    def _secure_session_cookie():
        # Never trust X-Forwarded-Proto from the request itself: clients can
        # supply it. Render terminates TLS upstream; local dev remains HTTP.
        return bool(os.environ.get('RENDER')) or os.environ.get('BRANDWISE_ENV', '').strip().casefold() == 'production'

    def _session_cookie(self, token, max_age=None):
        secure = '; Secure' if self._secure_session_cookie() else ''
        age = accounts.SESSION_AGE if max_age is None else max_age
        return f'brandwise_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}{secure}'

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
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_error(405, 'Cross-origin API requests are not supported.')

    @storage_errors_as_503
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
            if path == '/api/ai/context':
                today = datetime.now(timezone.utc).date().isoformat()
                compact_claims = [
                    {
                        'id': claim.get('id', ''),
                        'statement': claim.get('statement', ''),
                        'prohibitedPhrases': claim.get('prohibitedPhrases', []),
                    }
                    for claim in claims_for_user(user)
                    if claim.get('status') == 'Active' and (not claim.get('expiry') or claim.get('expiry', '') >= today)
                ]
                guidelines = guidelines_for_user(user)
                terminology = guidelines.get('terminology', {})
                compact_guidelines = {
                    'tone': {
                        'primary': guidelines.get('tone', {}).get('primary', ''),
                        'avoid': guidelines.get('tone', {}).get('avoid', ''),
                        'rules': guidelines.get('tone', {}).get('rules', []),
                    },
                    'prohibitedTerms': [
                        {key: item.get(key, '') for key in ('term', 'reason', 'suggested', 'severity')}
                        for item in terminology.get('prohibited', []) if isinstance(item, dict)
                    ],
                }
                providers = {'browser': True, 'gemini': bool(os.environ.get('GEMINI_API_KEY', '').strip())}
                return self.send_json(200, {'claims': compact_claims, 'guidelines': compact_guidelines, 'providers': providers})
            if path == '/api/workspaces':
                return self.send_json(200, {'workspaces': accounts.list_workspaces(self.headers), 'activeCompanyId': user.get('activeCompanyId')})
            if path in ('/api/company-data/brand-assets', '/api/company-data/calendar-events'):
                company_id = user.get('activeCompanyId')
                if not company_id or not user.get('companyRole'):
                    return self.send_json(403, {'error': 'Choose or create a company workspace first.'})
                filename = 'brand-assets.json' if path.endswith('brand-assets') else 'calendar-events.json'
                rows = load_json(company_data_path(company_id, filename), [])
                return self.send_json(200, {'items': rows if isinstance(rows, list) else []})
            if path == '/api/alerts':
                visible = audits_visible_to_user(get_audits(), user)
                alerts = []
                for audit in visible:
                    if audit.get('sampleData'):
                        continue
                    if audit.get('status') in ('Ready for review', 'Changes requested', 'Review required'):
                        alerts.append({'id': audit.get('id'), 'title': audit.get('title') or 'Untitled audit', 'status': audit.get('status'), 'updatedAt': audit.get('updatedAt') or audit.get('date') or ''})
                return self.send_json(200, {'alerts': alerts, 'count': len(alerts)})
            if path == '/api/admin/team':
                try:
                    return self.send_json(200, {'users': accounts.list_workspace_users(self.headers)})
                except PermissionError as exc:
                    return self.send_json(403, {'error': str(exc)})
            if path == '/api/keys' and user['role'] != 'Admin':
                return self.send_json(403, {'error': 'Administrator access required.'})

        if path == '/api/audit-preferences':
            return self.send_json(200, get_workspace_audit_preferences(user.get('activeCompanyId')))

        if path == '/api/health':
            storage = database.ping()
            return self.send_json(200 if storage['connected'] else 503, {
                'ok': True,
                'service': 'BrandWise Governance Platform API',
                'version': '2.4.0',
                'workingTitle': 'BrandWise',
                'preparedBy': 'Brand Wise',
                'storage': storage,
                'engines': {
                    'rules': 'Deterministic WCAG 2.1 & Terminology Engine',
                    'claims': 'Claims Ledger & Expiry Verification Engine',
                    'llm': 'Optional in-browser Llama 3.2 review; optional Gemini only when configured; no image or OCR review',
                    'uncertaintyMode': 'Active ("Cannot verify - needs human check" enabled)'
                }
            })

        if path == '/api/audits':
            audits = audits_visible_to_user(get_audits(), user)
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
            if 'reviewer' in query:
                reviewer = query['reviewer'][0].casefold()
                audits = [a for a in audits if reviewer in str(a.get('creator', '')).casefold() or reviewer in str(a.get('creatorUsername', '')).casefold() or any(reviewer in str(entry.get('user', '')).casefold() for entry in a.get('auditTrail', []) if isinstance(entry, dict))]
            if 'from' in query:
                audits = [a for a in audits if str(a.get('date', a.get('updatedAt', '')))[:10] >= query['from'][0]]
            if 'to' in query:
                audits = [a for a in audits if str(a.get('date', a.get('updatedAt', '')))[:10] <= query['to'][0]]
            return self.send_json(200, {'records': audits, 'total': len(audits)})

        if path.startswith('/api/audits/'):
            audit_id = path.replace('/api/audits/', '').strip()
            audits = audits_visible_to_user(get_audits(), user)
            found = next((a for a in audits if a.get('id') == audit_id), None)
            if found:
                return self.send_json(200, found)
            return self.send_json(404, {'error': f'Audit {audit_id} not found'})

        if path == '/api/claims':
            claims = claims_for_user(user)
            return self.send_json(200, {'claims': claims, 'total': len(claims)})

        if path == '/api/guidelines':
            guidelines = guidelines_for_user(user)
            return self.send_json(200, guidelines)

        if path == '/api/keys':
            return self.send_json(200, {'status': 'ok', 'keys': get_masked_keys()})

        if path == '/api/insights':
            audits = [item for item in audits_visible_to_user(get_audits(), user) if not item.get('sampleData')]
            all_findings = [f for a in audits for f in a.get('findings', [])]
            category_counts = {}
            for f in all_findings:
                cat = f.get('category', 'Other')
                category_counts[cat] = category_counts.get(cat, 0) + 1

            flagged_by_rule = {}
            grouped_agencies = {}
            for audit in audits:
                org = audit.get('agency') or 'Unassigned organization'
                group = grouped_agencies.setdefault(org, {'name': org, 'submissions': 0, 'scores': [], 'approved': 0})
                group['submissions'] += 1
                if isinstance(audit.get('score'), (int, float)):
                    group['scores'].append(audit['score'])
                group['approved'] += audit.get('status') in ('Approved', 'Published')
                for finding in audit.get('findings', []):
                    if finding.get('actionStatus') == 'dismissed' or finding.get('reportedIncorrect'):
                        rule_id = finding.get('sourceId') or finding.get('category', 'Unattributed rule')
                        item = flagged_by_rule.setdefault(rule_id, {'ruleId': rule_id, 'ruleTitle': finding.get('title', 'Finding'), 'dismissalCount': 0, 'recommendation': 'Review the finding and rule wording.'})
                        item['dismissalCount'] += 1
            ambiguous_rules = sorted(flagged_by_rule.values(), key=lambda item: item['dismissalCount'], reverse=True)
            agency_stats = [
                {'name': group['name'], 'submissions': group['submissions'],
                 'avgCompliance': round(sum(group['scores']) / len(group['scores'])) if group['scores'] else None,
                 'approvalRate': round(100 * group['approved'] / group['submissions']) if group['submissions'] else None}
                for group in grouped_agencies.values()
            ]
            source_linked = sum(bool(f.get('sourceId') and f.get('official') and f.get('state') == 'source-verified') for f in all_findings)
            impact_evidence = {
                'measurementStatus': 'Saved audit counts are operational data. Detection/false-flag rates below use the checked-in synthetic labeled set and are not production benchmarks.',
                'savedAuditCount': len(audits),
                'savedFindingCount': len(all_findings),
                'sourceLinkedFindingCount': source_linked,
                'sourceLinkedDefinition': 'Findings marked source-verified with a source ID and evidence text',
                'incorrectFlagReports': sum(bool(f.get('reportedIncorrect')) for f in all_findings),
                'labelledEvaluation': evaluate_labelled_ruleset()
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
                stamp = target_file.stat().st_mtime_ns
                with PAGE_CACHE_LOCK:
                    if PAGE_CACHE.get('stamp') != stamp or PAGE_CACHE.get('path') != target_file:
                        body = target_file.read_bytes()
                        PAGE_CACHE.update(path=target_file, stamp=stamp, plain=body,
                                          gzip=gzip.compress(body, compresslevel=6))
                    compressed = 'gzip' in self.headers.get('Accept-Encoding', '').lower()
                    body = PAGE_CACHE['gzip' if compressed else 'plain']
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Vary', 'Accept-Encoding')
                if compressed:
                    self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('X-Frame-Options', 'DENY')
                self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
                self.end_headers()
                self.wfile.write(body)
                return

        self.send_error(404, "Page or endpoint not found")

    @storage_errors_as_503
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
        if path.startswith('/api/'):
            fetch_site = (self.headers.get('Sec-Fetch-Site') or '').casefold()
            if fetch_site == 'cross-site':
                return self.send_json(403, {'error': 'Open BrandWise to submit this request.'})
            origin = self.headers.get('Origin')
            host = (self.headers.get('Host') or '').casefold()
            parsed_origin = urllib.parse.urlparse(origin or '')
            if (not origin or parsed_origin.scheme not in ('http', 'https') or
                    not parsed_origin.netloc or parsed_origin.username or parsed_origin.password or
                    parsed_origin.path not in ('', '/') or parsed_origin.params or
                    parsed_origin.query or parsed_origin.fragment or
                    parsed_origin.netloc.casefold() != host):
                return self.send_json(403, {'error': 'Request origin is not allowed.'})
        if path == '/api/auth/send-otp':
            client_ip = self.client_address[0]
            if not allow_otp_request(client_ip):
                return self.send_json(429, {'error': 'Too many verification requests. Wait 10 minutes and try again.'})
            try:
                res = accounts.send_email_otp(data.get('email'), client_ip=client_ip)
            except accounts.EmailDeliveryError as exc:
                return self.send_json(503, {'error': str(exc)})
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            dev_code = res.get('dev_code') if isinstance(res, dict) else None
            return self.send_json(200, {'ok': True, 'dev_code': dev_code})
        if path == '/api/auth/verify-otp':
            try:
                accounts.verify_email_otp(data.get('email'), data.get('code'))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True})
        if path == '/api/auth/password-reset/send':
            client_ip = self.client_address[0]
            if not allow_otp_request(client_ip):
                return self.send_json(429, {'error': 'Too many verification requests. Wait 10 minutes and try again.'})
            try:
                res = accounts.send_password_reset_otp(data.get('email'), client_ip=client_ip)
            except accounts.EmailDeliveryError as exc:
                return self.send_json(503, {'error': str(exc)})
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            dev_code = res.get('dev_code') if isinstance(res, dict) else None
            msg = f'Reset code: {dev_code} (Local development mode)' if dev_code else 'If an account uses that email, a reset code has been sent via Resend.'
            return self.send_json(200, {'ok': True, 'message': msg, 'dev_code': dev_code})
        if path == '/api/auth/password-reset':
            try:
                accounts.reset_password_with_email_otp(data.get('email'), data.get('code'), data.get('newPassword'))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(200, {'ok': True})
        if path == '/api/auth/register':
            try:
                token = accounts.register(data)
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
            return self.send_json(201, {'ok': True}, self._session_cookie(token))
        if path == '/api/auth/login':
            client_ip = self.client_address[0]
            local_dev = accounts.is_local_dev(client_ip)
            identifier = data.get('username')
            rate_identifier = accounts.email_for_login(identifier) or identifier
            if not local_dev and accounts.login_is_limited(client_ip, rate_identifier):
                return self.send_json(429, {'error': 'Too many sign-in attempts. Try again later.'})
            token = accounts.login(data)
            if not token:
                if not local_dev:
                    accounts.record_login_failure(client_ip, rate_identifier)
                return self.send_json(401, {'error': 'Username, email, or password is incorrect.'})
            accounts.clear_login_failures(client_ip, rate_identifier)
            return self.send_json(200, {'ok': True}, self._session_cookie(token))
        user = accounts.current_user(self.headers)
        if not user:
            return self.send_json(401, {'error': 'Sign in first.'})
        if path == '/api/workspaces':
            try:
                workspace = accounts.create_workspace(self.headers, data.get('name'))
                return self.send_json(201, {'workspace': workspace, 'activeCompanyId': workspace['id']})
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/workspaces/switch':
            try:
                switched = accounts.switch_workspace(self.headers, data.get('companyId'))
                return self.send_json(200, switched)
            except ValueError as exc:
                return self.send_json(403, {'error': str(exc)})
        if path == '/api/workspaces/invite':
            try:
                return self.send_json(201, accounts.create_workspace_invitation(self.headers, data.get('email'), data.get('role')))
            except PermissionError as exc:
                return self.send_json(403, {'error': str(exc)})
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/workspaces/join':
            try:
                return self.send_json(200, accounts.join_workspace_invitation(self.headers, data.get('code')))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
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
            return self.send_json(200, {'ok': True}, self._session_cookie('', max_age=0))
        if path == '/api/audit-preferences':
            membership = accounts.active_membership(self.headers)
            if not membership:
                return self.send_json(403, {'error': 'Join a company workspace before changing shared audit preferences.'})
            try:
                return self.send_json(200, set_workspace_audit_preferences(data, user.get('activeCompanyId')))
            except ValueError as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/auth/logout':
            accounts.logout(self.headers)
            return self.send_json(200, {'ok': True}, self._session_cookie('', max_age=0))
        if path in ('/api/keys', '/api/keys/test', '/api/reset') and user['role'] != 'Admin':
            return self.send_json(403, {'error': 'Administrator access required.'})
        membership = accounts.active_membership(self.headers)
        if path in ('/api/claims', '/api/guidelines') and (not membership or membership['role'] not in ('Brand Manager', 'Admin')):
            return self.send_json(403, {'error': 'Brand Manager or Admin access required.'})
        if path == '/api/import':
            try:
                accounts.ensure_private_workspace(self.headers)
                return self.send_json(200, extract_document(data))
            except Exception as exc:
                return self.send_json(400, {'error': str(exc)})
        if path == '/api/accessibility':
            content = data.get('content')
            if not isinstance(content, str) or not content.strip():
                return self.send_json(400, {'error': 'Enter copy before running accessibility checks.'})
            return self.send_json(200, check_text_accessibility(content, guidelines_for_user(user)))

        if path in ('/api/company-data/brand-assets', '/api/company-data/calendar-events'):
            membership = accounts.active_membership(self.headers)
            if not membership:
                return self.send_json(403, {'error': 'Choose or create a company workspace first.'})
            items = data.get('items')
            if not isinstance(items, list) or len(items) > 500:
                return self.send_json(400, {'error': 'Expected a list of at most 500 workspace items.'})
            try:
                if len(json.dumps(items, ensure_ascii=False).encode('utf-8')) > 8 * 1024 * 1024:
                    return self.send_json(413, {'error': 'Workspace files exceed the 8 MB shared storage limit. Remove large assets and retry.'})
            except (TypeError, ValueError):
                return self.send_json(400, {'error': 'Workspace items must contain JSON-compatible data.'})
            filename = 'brand-assets.json' if path.endswith('brand-assets') else 'calendar-events.json'
            if not save_json(company_data_path(membership['companyId'], filename), items):
                return self.send_json(503, {'error': 'Could not save shared workspace data. Please retry.'})
            return self.send_json(200, {'items': items})

        # 1. Create a new audit / Run Automated Check
        if path == '/api/audits':
            content = data.get('content', '').strip()
            if not content:
                return self.send_json(400, {'error': 'content is required'})

            title = data.get('title') or content.splitlines()[0][:70] or 'Brand Review Draft'
            channel = data.get('channel', 'Website Copy')
            if not isinstance(channel, str) or len(channel) > 100:
                return self.send_json(400, {'error': 'Choose a valid content type.'})
            if len(content) > 250000:
                return self.send_json(413, {'error': 'Draft is too large to check. Use a text-only file under 250,000 characters.'})
            if not isinstance(title, str) or len(title) > 150:
                return self.send_json(400, {'error': 'Audit name must be 150 characters or fewer.'})
            company_id = accounts.ensure_private_workspace(self.headers)
            user = accounts.current_user(self.headers) or user
            # Backfill only records whose creatorUsername unambiguously identifies this account.
            audits = get_audits()
            changed_legacy = False
            for prior in audits:
                if not prior.get('companyId') and (prior.get('creatorUsername') or '').casefold() == user['username'].casefold():
                    prior['companyId'] = company_id
                    changed_legacy = True
            if changed_legacy and not save_json(DB, audits):
                return self.send_json(503, {'error': 'Could not preserve the existing audit history. Please retry.'})
            creator = user['name']
            agency = user['organization']
            role = user['role']

            # Run BrandWise Multi-Engine Evaluation
            audit_settings = get_workspace_audit_preferences(company_id)
            strictness = audit_settings['strictness']
            passing_threshold = audit_settings['passingThreshold']
            active_claims = claims_for_user(user)
            active_guidelines = guidelines_for_user(user)
            check_result = run_brandwise_checks(content, channel=channel, strictness=strictness, _claims=active_claims, _guidelines=active_guidelines)
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
            ai_findings = []
            ai_status = 'AI review not requested; deterministic checks only.'
            ai_used = False
            if data.get('useAI') is True and data.get('aiProvider') == 'browser':
                model_ids = {
                    'Llama-3.2-1B-Instruct-q4f16_1-MLC': 'In-browser Llama 3.2 1B (WebLLM)',
                    'Llama-3.2-1B-Instruct-q4f32_1-MLC': 'In-browser Llama 3.2 1B (WebLLM, q4f32 fallback)',
                    'Llama-3.2-3B-Instruct-q4f16_1-MLC': 'In-browser Llama 3.2 3B (WebLLM)',
                    'Llama-3.2-3B-Instruct-q4f32_1-MLC': 'In-browser Llama 3.2 3B (WebLLM, q4f32 fallback)',
                }
                client_ai = data.get('clientAi')
                if isinstance(client_ai, dict) and isinstance(client_ai.get('model'), str) and client_ai.get('model') in model_ids and isinstance(client_ai.get('findings'), list):
                    safe_findings = []
                    for finding in client_ai['findings'][:15]:
                        if not isinstance(finding, dict):
                            continue
                        safe = {}
                        for field in ('title', 'category', 'wrong', 'why', 'sourceId', 'fix'):
                            value = finding.get(field, '')
                            safe[field] = str(value)[:500] if value is not None else ''
                        severity = str(finding.get('severity', 'Medium'))[:20]
                        safe['severity'] = severity if severity in ('Low', 'Medium', 'High', 'Critical') else 'Medium'
                        safe_findings.append(safe)
                    ai_findings = review_validation.validate_findings(
                        safe_findings, content, [c for c in active_claims if c.get('status') == 'Active'], 'In-browser Llama', model_ids[client_ai['model']]
                    )
                    for item in ai_findings:
                        phrase = item.get('wrong', '')
                        occurrences = len(re.findall(re.escape(phrase), content, re.I)) if phrase else 0
                        if occurrences != 1:
                            item['fix'] = ''
                            item['automaticFixAllowed'] = False
                            item['needsHumanReview'] = True
                    ai_used = True
                    ai_status = f"{model_ids[client_ai['model']]}; subjective findings require human review."
                else:
                    ai_status = 'Browser AI response was unavailable or invalid; deterministic checks only.'
            elif data.get('useAI') is True and data.get('aiProvider') == 'gemini':
                if os.environ.get('GEMINI_API_KEY', '').strip():
                    ai_findings, ai_status, ai_used = gemini_review(content, [c for c in active_claims if c.get('status') == 'Active'], active_guidelines)
                    for item in ai_findings:
                        phrase = item.get('wrong', '')
                        if not phrase or len(re.findall(re.escape(phrase), content, re.I)) != 1:
                            item['fix'] = ''
                            item['automaticFixAllowed'] = False
                            item['needsHumanReview'] = True
                else:
                    ai_status = 'Gemini is not configured; deterministic checks only.'
            check_result['findings'].extend(ai_findings)
            check_result['score'] = compliance_score(check_result['findings'], strictness)
            confidence_values = [f.get('confidence') if isinstance(f.get('confidence'), (int, float)) else 100 for f in check_result['findings']]
            check_result['confidence'] = int(sum(confidence_values) / len(confidence_values)) if confidence_values else None

            audit_id = 'BW-' + uuid.uuid4().hex[:16].upper()
            revision_id = uuid.uuid4().hex
            now_iso = datetime.now(timezone.utc).isoformat()

            new_record = {
                'id': audit_id,
                'companyId': company_id,
                'title': title,
                'channel': channel,
                'type': channel,
                'creator': creator,
                'creatorUsername': user['username'],
                'agency': agency,
                'role': role,
                'status': 'Review required' if check_result['score'] < passing_threshold else 'Ready for review',
                'date': now_iso,
                'score': check_result['score'],
                'confidence': check_result['confidence'],
                'passingThreshold': passing_threshold,
                'passedThreshold': check_result['score'] >= passing_threshold,
                'settings': {'strictness': strictness, 'passingThreshold': passing_threshold, 'useAI': ai_used, 'aiProvider': data.get('aiProvider') if ai_used else None},
                'aiProvider': data.get('aiProvider') if ai_used else 'rules',
                'aiStatus': ai_status,
                'accessibility': check_result['accessibility'],
                'content': content,
                'reference': data.get('reference', 'BrandWise Standard Corporate Claims & Guidelines v3.2'),
                'findings': check_result['findings'],
                'claimsSnapshot': active_claims,
                'guidelinesSnapshot': active_guidelines,
                'currentRevisionId': revision_id,
                'approvedRevisionId': None,
                'revisions': [
                    {
                        'version': 'v1',
                        'id': revision_id,
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
            if not save_json(DB, audits):
                return self.send_json(503, {'error': 'The audit could not be saved. Your draft is still available in the editor; retry the check.'})
            return self.send_json(201, new_record)

        # 2. Audit Actions: Accept, Edit, Dismiss, Report Incorrect Flag, Change State, Add Comment
        if path.startswith('/api/audits/') and path.endswith('/action'):
            audit_id = path.replace('/api/audits/', '').replace('/action', '').strip()
            audits = get_audits()
            target_audit = next((a for a in audits if a.get('id') == audit_id), None)
            if not target_audit or target_audit not in audits_visible_to_user(audits, user):
                return self.send_json(404, {'error': f'Audit {audit_id} not found'})

            action_type = data.get('action') # 'accept_fix', 'edit_fix', 'dismiss_fix', 'change_state', 'add_comment', 'report_incorrect_flag'
            now_iso = datetime.now(timezone.utc).isoformat()
            user_name = user['name']
            membership = accounts.active_membership(self.headers)
            effective_role = membership.get('role', '') if membership else ''
            current_revision = target_audit.get('currentRevisionId')
            if data.get('baseRevisionId') != current_revision:
                return self.send_json(409, {'error': 'This audit changed since you opened it. Reload the saved revision before applying this action.', 'currentRevisionId': current_revision})
            if action_type == 'change_state' and effective_role not in ('Reviewer', 'Brand Manager', 'Admin'):
                return self.send_json(403, {'error': 'Reviewer, Brand Manager, or Admin access required.'})

            if action_type in ('accept_fix', 'edit_fix'):
                finding_id = data.get('findingId')
                finding = next((f for f in target_audit.get('findings', []) if f.get('id') == finding_id), None)
                if not finding:
                    return self.send_json(404, {'error': 'Finding not found.'})
                fix_text = data.get('fixText', finding.get('fix', '')).strip()
                if not fix_text:
                    return self.send_json(400, {'error': 'Provide replacement wording.'})
                if action_type == 'accept_fix' and finding.get('automaticFixAllowed') is False:
                    return self.send_json(409, {'error': 'This wording is repeated or could not be matched uniquely. Select the intended occurrence and edit it manually.'})
                current_text = target_audit.get('content', '')
                wrong = finding.get('wrong', '')
                positions = [m.start() for m in re.finditer(re.escape(wrong), current_text, re.I)] if wrong else []
                try:
                    occurrence_index = int(data.get('occurrenceIndex', 0))
                except (TypeError, ValueError):
                    occurrence_index = -1
                if wrong and fix_text and 0 <= occurrence_index < len(positions):
                    start = positions[occurrence_index]
                    new_text = current_text[:start] + fix_text + current_text[start + len(wrong):]
                    if new_text != current_text:
                        target_audit['content'] = new_text
                        target_audit['currentRevisionId'] = uuid.uuid4().hex
                        target_audit['approvedRevisionId'] = None
                        revisions = target_audit.setdefault('revisions', [])
                        revisions.append({
                            'version': f"v{len(revisions)+1}",
                            'id': target_audit['currentRevisionId'],
                            'author': user_name,
                            'timestamp': now_iso,
                            'text': new_text,
                            'notes': f"{'Edited' if action_type == 'edit_fix' else 'Accepted'} fix for finding {finding_id} at occurrence {occurrence_index + 1}"
                        })
                        recheck_saved_audit(target_audit)
                    else:
                        target_audit['content'] = new_text
                elif wrong:
                    return self.send_json(409, {'error': 'The selected occurrence no longer exists in the saved draft. Reload the audit and try again.'})
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
                old_state = target_audit.get('status')
                allowed = {'Ready for review', 'Review required', 'In review', 'Changes requested', 'Auto-checked'}
                if new_state == 'Changes requested':
                    if effective_role not in ('Reviewer', 'Brand Manager', 'Admin') or old_state not in allowed:
                        return self.send_json(403, {'error': 'Only a reviewer or brand manager can request changes on an active review.'})
                elif new_state == 'Approved':
                    if effective_role not in ('Reviewer', 'Brand Manager', 'Admin'):
                        return self.send_json(403, {'error': 'Reviewer or Brand Manager approval is required.'})
                    if old_state not in allowed:
                        return self.send_json(409, {'error': 'This audit is not in a state that can be approved.'})
                    threshold = int(target_audit.get('passingThreshold', get_workspace_audit_preferences(user.get('activeCompanyId'))['passingThreshold']))
                    pending = [f for f in target_audit.get('findings', []) if f.get('actionStatus', 'pending') == 'pending']
                    if float(target_audit.get('score', 0)) < threshold or pending:
                        return self.send_json(409, {'error': f"Disposition every finding and meet the {threshold}% passing threshold before approval."})
                elif new_state == 'Published':
                    if effective_role not in ('Reviewer', 'Brand Manager', 'Admin'):
                        return self.send_json(403, {'error': 'Reviewer or Brand Manager publishing permission is required.'})
                    pending = [f for f in target_audit.get('findings', []) if f.get('actionStatus', 'pending') == 'pending']
                    if old_state != 'Approved' or target_audit.get('approvedRevisionId') != target_audit.get('currentRevisionId') or pending:
                        return self.send_json(409, {'error': 'Approve this audit and resolve or disposition every finding before publishing.'})
                else:
                    return self.send_json(400, {'error': 'Unsupported audit state transition.'})
                target_audit['status'] = new_state
                if new_state == 'Approved':
                    target_audit['approvedRevisionId'] = target_audit.get('currentRevisionId')
                target_audit.setdefault('auditTrail', []).append({
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

            if not save_json(DB, audits):
                return self.send_json(503, {'error': 'This action could not be saved. Please retry.'})
            return self.send_json(200, target_audit)

        # 3. Add or Update Claim in Ledger
        if path == '/api/claims':
            statement = data.get('statement', '').strip()
            if not statement:
                return self.send_json(400, {'error': 'statement is required'})
            claims = claims_for_user(user)
            cid = data.get('id') or f"CLM-{len(claims)+1:03d}"
            existing = next((c for c in claims if c['id'] == cid), None)
            if existing:
                existing.update(data)
            else:
                data['id'] = cid
                data.setdefault('status', 'Active')
                claims.append(data)
            if not save_company_json(user, 'claims-data.json', CLAIMS_DB, claims):
                return self.send_json(503, {'error': 'Could not save claims. Retry without closing this page.'})
            return self.send_json(200, {'success': True, 'claim': data})

        # 4. Update Guidelines
        if path == '/api/guidelines':
            if not save_company_json(user, 'guidelines-data.json', GUIDELINES_DB, data):
                return self.send_json(503, {'error': 'Could not save guidelines. Retry without closing this page.'})
            return self.send_json(200, {'success': True, 'guidelines': data})

        # 5. API Keys Configuration & Management
        if path == '/api/keys':
            updates = {}
            if 'anthropicApiKey' in data: updates['ANTHROPIC_API_KEY'] = data['anthropicApiKey']
            if 'geminiApiKey' in data: updates['GEMINI_API_KEY'] = data['geminiApiKey']
            if 'openaiApiKey' in data: updates['OPENAI_API_KEY'] = data['openaiApiKey']
            saved = save_env_keys(updates)
            return self.send_json(200 if saved else 500, {'success': saved, 'message': 'API keys updated and saved to .env', 'keys': get_masked_keys()})

        if path == '/api/keys/test':
            provider = data.get('provider', '')
            api_key = data.get('apiKey', '')
            res = test_external_api_key(provider, api_key)
            return self.send_json(200, res)

        # 7. Reset Database to Default Proposal Seeds
        if path == '/api/reset':
            audits = get_audits()
            real_audits = [item for item in audits if not item.get('sampleData')]
            if not save_json(DB, DEFAULT_AUDITS + real_audits):
                return self.send_json(503, {'error': 'Demo reset failed; saved audits were preserved.'})
            if not save_company_json(user, 'claims-data.json', CLAIMS_DB, DEFAULT_CLAIMS) or not save_company_json(user, 'guidelines-data.json', GUIDELINES_DB, DEFAULT_GUIDELINES):
                return self.send_json(503, {'error': 'Demo data reset did not finish; saved audits were preserved.'})
            company_id = user.get('activeCompanyId')
            preference_path = company_data_path(company_id, 'audit-preferences.json') if company_id else AUDIT_PREFERENCES_DB
            save_json(preference_path, DEFAULT_AUDIT_PREFERENCES)
            return self.send_json(200, {'ok': True, 'message': 'Demo data reset. Real audit records were preserved.'})

        self.send_error(404, "Endpoint not found")

    def log_message(self, fmt, *args):
        # Concise logging
        print('%s - %s' % (self.address_string(), fmt % args))


def init_storage():
    if database.uses_postgres():
        database.initialize()
        imported_accounts = accounts.migrate_local_accounts()
        datasets = (
            (DB, DEFAULT_AUDITS),
            (CLAIMS_DB, DEFAULT_CLAIMS),
            (GUIDELINES_DB, DEFAULT_GUIDELINES),
            (AUDIT_PREFERENCES_DB, DEFAULT_AUDIT_PREFERENCES),
        )
        for path, fallback in datasets:
            database.get_json(path.name, fallback, path)
        print(f'PostgreSQL storage ready; imported {imported_accounts} local account record(s) when the database was empty.')
        return
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
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    port = int(os.environ.get('PORT', '8765'))
    server = ThreadingHTTPServer((host, port), Handler)
    print('========================================================')
    print('  BrandWise — Brand Governance Platform Backend')
    print(f'  Running at: http://{host}:{port}')
    print('========================================================')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
