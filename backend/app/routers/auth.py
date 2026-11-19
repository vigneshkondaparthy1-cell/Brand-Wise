from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication & Roles"])

class RoleSwitch(BaseModel):
    role: str

@router.get("/me", response_model=dict)
def get_current_user():
    return {
        "user": "Alex Rivera",
        "email": "alex.rivera@acme-brand.com",
        "activeRole": "Brand Manager",
        "availableRoles": ["Creator", "External Agency", "Reviewer", "Brand Manager", "Admin"],
        "tenant": "Acme Technologies (Global)",
        "tenantIsolated": True
    }

@router.post("/role", response_model=dict)
def switch_active_role(payload: RoleSwitch):
    valid_roles = ["Creator", "External Agency", "Reviewer", "Brand Manager", "Admin"]
    if payload.role not in valid_roles:
        return {"success": False, "error": f"Invalid role {payload.role}"}
    return {
        "success": True,
        "newRole": payload.role,
        "isAgency": payload.role == "External Agency"
    }
