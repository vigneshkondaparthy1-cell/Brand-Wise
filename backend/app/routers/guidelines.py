from fastapi import APIRouter
from typing import Dict, Any
from ..store import store

router = APIRouter(prefix="/api/guidelines", tags=["Brand Sources & Guidelines"])

@router.get("", response_model=dict)
def get_guidelines():
    return store.get_guidelines()

@router.post("", response_model=dict)
def update_guidelines(guidelines: Dict[str, Any]):
    store.save_guidelines(guidelines)
    return {"success": True, "guidelines": guidelines}
