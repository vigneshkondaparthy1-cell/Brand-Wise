from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Claim Ledger Schemas
class ClaimItem(BaseModel):
    id: str
    statement: str
    category: str
    evidence: str
    owner: str
    expiry: str
    status: str = "Active"
    prohibitedPhrases: Optional[List[str]] = []
    notes: Optional[str] = ""

class ClaimCreate(BaseModel):
    statement: str
    category: str
    evidence: str
    owner: str
    expiry: str
    status: Optional[str] = "Active"
    prohibitedPhrases: Optional[List[str]] = []
    notes: Optional[str] = ""

class ClaimUpdate(BaseModel):
    statement: Optional[str] = None
    category: Optional[str] = None
    evidence: Optional[str] = None
    owner: Optional[str] = None
    expiry: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# Guideline Schemas
class ProhibitedTerm(BaseModel):
    term: str
    reason: str
    suggested: str
    severity: str = "High"

class ApprovedTerm(BaseModel):
    term: str
    note: str

class ToneRules(BaseModel):
    primary: str
    avoid: str
    rules: List[str]

class VisualRules(BaseModel):
    primaryColor: str
    secondaryColor: str
    warningColor: str
    criticalColor: str
    minContrastRatio: float = 4.5
    largeTextContrastRatio: float = 3.0
    fontFamily: str
    logoVariants: List[str]

class GuidelinesData(BaseModel):
    version: str
    updatedAt: str
    brandName: str
    productName: str
    requiredDisclaimer: str
    tone: ToneRules
    terminology: Dict[str, Any]
    visual: VisualRules
    accessibility: Dict[str, Any]

# Findings & Audit Schemas
class Finding(BaseModel):
    id: str
    location: str
    category: str
    title: str
    severity: str  # Critical, High, Medium, Low
    wrong: str
    why: str
    sourceId: str
    official: str
    owner: str
    expiry: str
    state: str  # "source-verified" or "cannot verify - needs human check"
    confidence: int
    fix: str
    actionStatus: Optional[str] = "pending"  # pending, accepted, dismissed
    dismissalReason: Optional[str] = None
    appliedFix: Optional[str] = None
    reportedIncorrect: Optional[bool] = False
    incorrectFeedback: Optional[str] = None

class Revision(BaseModel):
    version: str
    author: str
    timestamp: str
    text: str
    notes: Optional[str] = ""

class Comment(BaseModel):
    id: str
    author: str
    role: str
    timestamp: str
    text: str

class AuditTrailEntry(BaseModel):
    action: str
    user: str
    timestamp: str
    note: Optional[str] = ""

class AuditCreate(BaseModel):
    content: str
    channel: Optional[str] = "Website Copy"
    title: Optional[str] = None
    creator: Optional[str] = "Alex Rivera (Content Creator)"
    agency: Optional[str] = "In-house Brand Team"
    role: Optional[str] = "Creator"
    reference: Optional[str] = None

class AuditActionRequest(BaseModel):
    action: str  # accept_fix, edit_fix, dismiss_fix, change_state, add_comment, report_incorrect_flag
    findingId: Optional[str] = None
    wrongText: Optional[str] = None
    fixText: Optional[str] = None
    reason: Optional[str] = None
    feedback: Optional[str] = None
    state: Optional[str] = None
    text: Optional[str] = None
    note: Optional[str] = None
    user: Optional[str] = "Current User"
    role: Optional[str] = "Reviewer"

class AuditRecord(BaseModel):
    id: str
    title: str
    channel: str
    type: str
    creator: str
    agency: str
    role: str
    status: str  # Draft, Auto-checked, In review, Changes requested, Approved, Published
    date: str
    score: int
    confidence: int
    content: str
    reference: str
    findings: List[Finding]
    revisions: List[Revision]
    comments: List[Comment]
    auditTrail: List[AuditTrailEntry]

# Visual and Accessibility Schemas
class ContrastRequest(BaseModel):
    fgColor: str
    bgColor: str

class ContrastResponse(BaseModel):
    ratio: float
    passesAANormalText: bool
    passesAALargeText: bool
    passesAAA: bool

class ReadabilityRequest(BaseModel):
    text: str

class ReadabilityResponse(BaseModel):
    readingEase: float
    gradeLevel: float
    readingLevelLabel: str
    sentenceCount: int
    wordCount: int

# Slack Webhook Simulation Schema
class SlackNotificationRequest(BaseModel):
    channel: str = "#brand-governance-alerts"
    status: str
    title: str
    docId: str
    actor: str
    message: str
