from fastapi import APIRouter
from ..schemas import ContrastRequest, ContrastResponse, ReadabilityRequest, ReadabilityResponse
from ..engines.visual_engine import visual_engine

router = APIRouter(prefix="/api/visual", tags=["Visual & Accessibility"])

@router.post("/contrast", response_model=ContrastResponse)
def compute_contrast(req: ContrastRequest):
    return visual_engine.calculate_contrast(req.fgColor, req.bgColor)

@router.post("/readability", response_model=ReadabilityResponse)
def compute_readability(req: ReadabilityRequest):
    return visual_engine.calculate_readability(req.text)
