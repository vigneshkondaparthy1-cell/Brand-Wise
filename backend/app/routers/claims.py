from fastapi import APIRouter, HTTPException
from ..schemas import ClaimCreate, ClaimUpdate
from ..store import store

router = APIRouter(prefix="/api/claims", tags=["Claim Ledger"])

@router.get("", response_model=dict)
def get_claims():
    claims = store.get_claims()
    return {"claims": claims, "total": len(claims)}

@router.post("", response_model=dict)
def add_or_update_claim(claim: ClaimCreate):
    claims = store.get_claims()
    cid = f"CLM-{len(claims)+1:03d}"
    claim_dict = claim.dict()
    claim_dict["id"] = cid
    claims.append(claim_dict)
    store.save_claims(claims)
    return {"success": True, "claim": claim_dict}

@router.put("/{claim_id}", response_model=dict)
def update_claim(claim_id: str, claim_update: ClaimUpdate):
    claims = store.get_claims()
    target = next((c for c in claims if c["id"] == claim_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    update_data = {k: v for k, v in claim_update.dict().items() if v is not None}
    target.update(update_data)
    store.save_claims(claims)
    return {"success": True, "claim": target}

@router.delete("/{claim_id}", response_model=dict)
def delete_claim(claim_id: str):
    claims = store.get_claims()
    filtered = [c for c in claims if c["id"] != claim_id]
    if len(filtered) == len(claims):
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    store.save_claims(filtered)
    return {"success": True, "message": f"Claim {claim_id} removed"}
