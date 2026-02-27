from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.merchant_schema import MerchantInput
from app.schemas.decision_schema import UnderwritingDecision
from app.orchestrator.orchestrator import Orchestrator
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["underwriting"])


@router.post("/underwrite", response_model=UnderwritingDecision)
async def underwrite(
    merchant: MerchantInput,
    whatsapp_number: Optional[str] = Query(
        None,
        description="Optional WhatsApp number to send result (format: whatsapp:+91XXXXXXXXXX)"
    ),
    mode: Optional[str] = Query(
        None,
        description="Financial offer mode: 'credit', 'insurance', or None for both"
    ),
    db: Session = Depends(get_db)
) -> UnderwritingDecision:
    """
    Process merchant underwriting request with optional WhatsApp delivery and financial offers.
    
    Takes merchant financial data and returns underwriting decision
    with risk score, approval status, and optional financial offers.
    
    Optionally sends result via WhatsApp if whatsapp_number is provided.
    WhatsApp delivery failures do not affect API response.
    
    Args:
        merchant: MerchantInput containing merchant financial metrics
        whatsapp_number: Optional WhatsApp number to receive result message
        mode: Optional financial offer mode ('credit', 'insurance', or None for both)
        db: SQLAlchemy database session (injected via dependency)
        
    Returns:
        UnderwritingResult: Underwriting result with risk assessment, decision, and financial offer
    """
    orchestrator = Orchestrator()
    return orchestrator.process_underwriting(merchant, db, whatsapp_number, mode)
