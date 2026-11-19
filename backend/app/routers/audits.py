from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from ..schemas import AuditCreate, AuditRecord, AuditActionRequest
from ..store import store
from ..engines.orchestrator import orchestrator

router = APIRouter(prefix="/api/audits", tags=["Audits & Review Flow"])

@router.get("", response_model=dict)
def list_audits(
    status: Optional[str] = Query(None, description="Filter by status (Draft, In review, Approved, etc)"),
    agency: Optional[str] = Query(None, description="Filter by agency / team"),
    q: Optional[str] = Query(None, description="Search term in title or content")
):
    audits = store.get_audits()
    if status and status != "all":
        audits = [a for a in audits if a.get("status", "").casefold() == status.casefold()]
    if agency and agency != "all":
        audits = [a for a in audits if a.get("agency", "").casefold() == agency.casefold()]
    if q:
        term = q.casefold()
        audits = [a for a in audits if term in a.get("title", "").casefold() or term in a.get("content", "").casefold() or term in a.get("id", "").casefold()]

    return {"records": audits, "total": len(audits)}

@router.post("", status_code=201, response_model=dict)
def create_audit(payload: AuditCreate):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content cannot be empty")

    channel = payload.channel or "Website Copy"
    title = payload.title or content.splitlines()[0][:70] or "Brand Review Draft"
    creator = payload.creator or "Alex Rivera (Content Creator)"
    agency = payload.agency or "In-house Brand Team"
    role = payload.role or "Creator"

    # Run check orchestrator
    check_result = orchestrator.run_full_audit(content, channel=channel)

    audit_id = "BW-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    now_iso = datetime.now(timezone.utc).isoformat()

    new_record = {
        "id": audit_id,
        "title": title,
        "channel": channel,
        "type": channel,
        "creator": creator,
        "agency": agency,
        "role": role,
        "status": "Auto-checked" if check_result["findings"] else "In review",
        "date": now_iso,
        "score": check_result["score"],
        "confidence": check_result["confidence"],
        "content": content,
        "reference": payload.reference or "BrandWise Standard Corporate Claims & Guidelines v3.2",
        "findings": check_result["findings"],
        "revisions": [
            {
                "version": "v1",
                "author": creator,
                "timestamp": now_iso,
                "text": content,
                "notes": "Initial submission for automated brand audit"
            }
        ],
        "comments": [],
        "auditTrail": [
            {"action": "Draft Submitted", "user": creator, "timestamp": now_iso, "note": f"Channel: {channel}"},
            {"action": "Automated Checks Completed", "user": "BrandWise Hybrid Engine", "timestamp": now_iso, "note": f"{len(check_result['findings'])} issues identified"}
        ]
    }

    audits = store.get_audits()
    audits.insert(0, new_record)
    store.save_audits(audits)
    return new_record

@router.get("/{audit_id}", response_model=dict)
def get_audit(audit_id: str):
    audits = store.get_audits()
    found = next((a for a in audits if a.get("id") == audit_id), None)
    if not found:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")
    return found

@router.post("/{audit_id}/action", response_model=dict)
def perform_audit_action(audit_id: str, action: AuditActionRequest):
    audits = store.get_audits()
    target_audit = next((a for a in audits if a.get("id") == audit_id), None)
    if not target_audit:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")

    action_type = action.action
    now_iso = datetime.now(timezone.utc).isoformat()
    user_name = action.user or "Current User"

    if action_type == "accept_fix":
        fid = action.findingId
        fix_text = action.fixText
        for f in target_audit.get("findings", []):
            if f.get("id") == fid:
                f["actionStatus"] = "accepted"
                f["appliedFix"] = fix_text
        current_text = target_audit.get("content", "")
        wrong = action.wrongText or ""
        if wrong and fix_text and wrong in current_text:
            new_text = current_text.replace(wrong, fix_text, 1)
            target_audit["content"] = new_text
            target_audit["revisions"].append({
                "version": f"v{len(target_audit['revisions'])+1}",
                "author": user_name,
                "timestamp": now_iso,
                "text": new_text,
                "notes": f"Accepted fix for finding {fid}: '{wrong}' -> '{fix_text}'"
            })
        target_audit["auditTrail"].append({
            "action": "Fix Accepted",
            "user": user_name,
            "timestamp": now_iso,
            "note": f"Accepted suggested fix for {fid}"
        })

    elif action_type == "dismiss_fix":
        fid = action.findingId
        reason = action.reason or "Dismissed by creator"
        for f in target_audit.get("findings", []):
            if f.get("id") == fid:
                f["actionStatus"] = "dismissed"
                f["dismissalReason"] = reason
        target_audit["auditTrail"].append({
            "action": "Finding Dismissed",
            "user": user_name,
            "timestamp": now_iso,
            "note": f"Dismissed {fid}. Reason: {reason}"
        })

    elif action_type == "report_incorrect_flag":
        fid = action.findingId
        feedback = action.feedback or "Reported as false positive"
        for f in target_audit.get("findings", []):
            if f.get("id") == fid:
                f["reportedIncorrect"] = True
                f["incorrectFeedback"] = feedback
        target_audit["auditTrail"].append({
            "action": "Reported Incorrect Flag",
            "user": user_name,
            "timestamp": now_iso,
            "note": f"False positive reported on {fid}: {feedback}"
        })

    elif action_type == "change_state":
        new_state = action.state
        valid_states = ["Draft", "Auto-checked", "In review", "Changes requested", "Approved", "Published"]
        if new_state in valid_states:
            old_state = target_audit.get("status")
            target_audit["status"] = new_state
            target_audit["auditTrail"].append({
                "action": f"State Changed: {old_state} -> {new_state}",
                "user": user_name,
                "timestamp": now_iso,
                "note": action.note or f"Moved to {new_state}"
            })

    elif action_type == "add_comment":
        comment_text = (action.text or "").strip()
        if comment_text:
            cid = f"COM-{len(target_audit.get('comments', []))+1}"
            target_audit.setdefault("comments", []).append({
                "id": cid,
                "author": user_name,
                "role": action.role or "Reviewer",
                "timestamp": now_iso,
                "text": comment_text
            })
            target_audit["auditTrail"].append({
                "action": "Comment Added",
                "user": user_name,
                "timestamp": now_iso,
                "note": comment_text[:60]
            })

    store.save_audits(audits)
    return target_audit
