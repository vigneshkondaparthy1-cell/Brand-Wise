"""Shared validation for structured AI review findings."""
from datetime import date
import re

STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "the", "to", "with", "our", "this", "that"}


def _tokens(value):
    return {token for token in re.findall(r"[\w%$]+", value.casefold()) if len(token) > 1 and token not in STOP_WORDS}


def citation_matches(excerpt, claim):
    """Check that cited claim has meaningful overlap with the flagged wording."""
    excerpt_tokens = _tokens(excerpt)
    claim_text = " ".join([claim.get("statement", ""), *claim.get("prohibitedPhrases", [])])
    claim_tokens = _tokens(claim_text)
    if not excerpt_tokens or not claim_tokens:
        return False
    overlap = excerpt_tokens & claim_tokens
    # Numeric claims must share a number with the source or its prohibited examples.
    excerpt_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", excerpt.casefold()))
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", claim_text.casefold()))
    if excerpt_numbers and source_numbers and not excerpt_numbers.intersection(source_numbers):
        return False
    return len(overlap) >= 2 and len(overlap) / min(len(excerpt_tokens), len(claim_tokens)) >= 0.35


def validate_findings(findings, content, claims, provider, model):
    """Reject invalid excerpts and unrelated citations, and estimate AI confidence."""
    sources = {claim.get("id"): claim for claim in claims}
    accepted = []
    for finding in findings[:15]:
        if not isinstance(finding, dict):
            continue
        excerpt = finding.get("wrong", "")
        if not isinstance(excerpt, str) or not excerpt or excerpt not in content:
            continue
        source_id = finding.get("sourceId", "")
        source = sources.get(source_id)
        relevant = bool(source and citation_matches(excerpt, source))
        current = bool(relevant and source.get("status") == "Active" and source.get("evidence") and source.get("expiry", "") >= date.today().isoformat())
        if source_id and not relevant:
            finding["citationIssue"] = "The cited claim does not match the flagged wording. Human verification is required."
            finding["sourceId"] = ""
        finding.update({
            "id": f"AI-{len(accepted)+1}",
            "location": f"Offset {content.index(excerpt)}",
            "state": "source-verified" if current else "cannot verify - needs human check",
            "official": source.get("evidence", "") if current else "No relevant current approved evidence verified",
            "owner": source.get("owner", "") if source else "",
            "expiry": source.get("expiry", "") if source else "",
            "confidence": 88 if current else 72,
            "confidenceBasis": "AI estimate; not calibrated",
            "engine": f"{provider} / {model}",
            "actionStatus": "pending",
        })
        accepted.append(finding)
    return accepted
