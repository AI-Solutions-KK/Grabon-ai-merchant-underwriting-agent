from sqlalchemy.orm import Session
import json
from app.models.risk_score import RiskScore
from app.schemas.decision_schema import UnderwritingDecision


class RiskScoreService:
    """
    Service layer for risk score and underwriting decision persistence.
    
    Handles storage of risk assessment results and financial offers in the database.
    """
    
    @staticmethod
    def create_risk_record(db: Session, decision: UnderwritingDecision) -> RiskScore:
        """
        Create and persist a risk score record with financial offer.
        
        Args:
            db: SQLAlchemy database session
            decision: UnderwritingResult schema with assessment results and offer
            
        Returns:
            RiskScore: Created risk score record
        """
        # Serialize financial_offer to JSON if present
        financial_offer_json = None
        if decision.financial_offer:
            financial_offer_json = decision.financial_offer.model_dump_json()
        
        db_risk = RiskScore(
            merchant_id=decision.merchant_id,
            risk_score=decision.risk_score,
            risk_tier=decision.risk_tier,
            decision=decision.decision,
            explanation=decision.explanation,
            financial_offer=financial_offer_json
        )
        db.add(db_risk)
        db.commit()
        db.refresh(db_risk)
        return db_risk

