from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base import Base


class RiskScore(Base):
    """
    SQLAlchemy model for risk assessment results.
    
    Stores underwriting decision and risk scoring for a merchant.
    Tracks offer acceptance status for dashboard simulation.
    """
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.merchant_id"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_tier = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    offer_status = Column(String, default="PENDING", nullable=False)  # PENDING | ACCEPTED | REJECTED

