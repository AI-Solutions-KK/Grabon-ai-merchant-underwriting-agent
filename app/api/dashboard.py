"""
Dashboard routes for merchant underwriting UI

Provides:
- Merchant list view
- Merchant detail view
- Accept offer simulation
"""

import logging
import os
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.merchant import Merchant
from app.models.risk_score import RiskScore
from app.schemas.decision_schema import FinancialOffer

logger = logging.getLogger(__name__)

# Initialize templates with absolute path
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Add custom Jinja2 global function for now
templates.env.globals.update(now=datetime.now)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard_home(request: Request, db: Session = Depends(get_db)):
    """
    Dashboard home page with merchant list
    """
    merchants = db.query(Merchant).all()
    
    # Enrich with latest risk scores
    merchants_data = []
    for merchant in merchants:
        risk_score = db.query(RiskScore).filter(
            RiskScore.merchant_id == merchant.merchant_id
        ).order_by(RiskScore.id.desc()).first()
        
        merchants_data.append({
            "merchant": merchant,
            "risk_score": risk_score
        })
    
    return templates.TemplateResponse(
        "merchant_list.html",
        {
            "request": request,
            "merchants_data": merchants_data,
            "page_title": "Merchant Dashboard"
        }
    )


@router.get("/{merchant_id}")
def merchant_detail(merchant_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Merchant detail page with full underwriting info and financial offers
    """
    merchant = db.query(Merchant).filter(
        Merchant.merchant_id == merchant_id
    ).first()
    
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    risk_score = db.query(RiskScore).filter(
        RiskScore.merchant_id == merchant_id
    ).order_by(RiskScore.id.desc()).first()
    
    if not risk_score:
        raise HTTPException(status_code=404, detail="No underwriting record found")
    
    # Deserialize financial_offer from JSON if present
    risk_score_dict = {
        "id": risk_score.id,
        "merchant_id": risk_score.merchant_id,
        "risk_score": risk_score.risk_score,
        "risk_tier": risk_score.risk_tier,
        "decision": risk_score.decision,
        "explanation": risk_score.explanation,
        "offer_status": risk_score.offer_status,
        "financial_offer": None
    }
    
    if risk_score.financial_offer:
        try:
            offer_data = json.loads(risk_score.financial_offer)
            risk_score_dict["financial_offer"] = offer_data
        except json.JSONDecodeError:
            logger.warning(f"Failed to deserialize financial_offer for merchant {merchant_id}")
            risk_score_dict["financial_offer"] = None
    
    return templates.TemplateResponse(
        "merchant_detail.html",
        {
            "request": request,
            "merchant": merchant,
            "risk_score": risk_score_dict,
            "page_title": f"Merchant {merchant_id} - Details"
        }
    )


@router.post("/{merchant_id}/accept")
def accept_offer(merchant_id: str, db: Session = Depends(get_db)):
    """
    Accept offer for merchant (simulation)
    Updates offer_status to ACCEPTED and redirects back to detail page
    """
    risk_score = db.query(RiskScore).filter(
        RiskScore.merchant_id == merchant_id
    ).order_by(RiskScore.id.desc()).first()
    
    if not risk_score:
        raise HTTPException(status_code=404, detail="Underwriting record not found")
    
    # Mark offer as accepted
    risk_score.offer_status = "ACCEPTED"
    db.commit()
    
    logger.info(f"Offer accepted for merchant {merchant_id}")
    
    # Redirect back to detail page with success indicator
    return RedirectResponse(url=f"/dashboard/{merchant_id}", status_code=303)
