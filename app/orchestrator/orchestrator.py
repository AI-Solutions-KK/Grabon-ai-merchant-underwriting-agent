import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.engines.risk_engine import RiskEngine
from app.engines.decision_engine import DecisionEngine
from app.engines.offer_engine import OfferEngine
from app.schemas.merchant_schema import MerchantInput
from app.schemas.decision_schema import UnderwritingDecision
from app.services.merchant_service import MerchantService
from app.services.application_service import RiskScoreService
from app.services.underwriting_agent import ClaudeUnderwritingAgent
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Central orchestrator for merchant underwriting process.
    
    Coordinates:
    - Deterministic risk scoring and decision making
    - AI-powered explanation generation via Claude
    - WhatsApp message delivery of results
    - Data persistence and audit trail
    """
    
    @staticmethod
    def process_underwriting(
        merchant: MerchantInput,
        db: Session,
        whatsapp_number: Optional[str] = None,
        mode: Optional[str] = None
    ) -> UnderwritingDecision:
        """
        Process merchant underwriting request with AI-generated explanations and financial offers.
        
        Flow:
        1. Save merchant via MerchantService
        2. Evaluate risk using RiskEngine.evaluate_risk()
        3. Evaluate decision using DecisionEngine.evaluate()
        4. Calculate financial offer based on mode (credit/insurance)
        5. Generate Claude AI explanation (with fallback)
        6. Construct UnderwritingResult with AI-generated explanation and financial offer
        7. Save risk result via RiskScoreService
        8. Send WhatsApp notification (if number provided, non-blocking)
        9. Return decision
        
        Args:
            merchant: MerchantInput containing merchant financial metrics
            db: SQLAlchemy database session
            whatsapp_number: Optional WhatsApp number to send result (format: whatsapp:+91XXXXXXXXXX)
            mode: Optional mode for financial offer ("credit", "insurance", None for both)
            
        Returns:
            UnderwritingResult: Structured underwriting result with AI explanation and financial offer
        """
        # Step 1: Save merchant to database
        MerchantService.create_merchant(db, merchant)
        
        # Step 2: Evaluate risk with hard rules and weighted scoring
        risk_result = RiskEngine.evaluate_risk(merchant)
        
        # Step 3: Evaluate decision based on risk result
        risk_tier, decision, _ = DecisionEngine.evaluate(risk_result)
        
        # Step 4: Calculate financial offer based on mode
        financial_offer = OfferEngine.calculate_financial_offer(
            risk_tier=risk_tier,
            merchant_data=merchant.dict(),
            mode=mode
        )
        
        # Step 5: Generate Claude AI explanation (with automatic fallback)
        ai_explanation = ClaudeUnderwritingAgent.generate_explanation(
            merchant_data=merchant.dict(),
            risk_score=risk_result["score"],
            risk_tier=risk_tier,
            decision=decision
        )
        
        # Step 6: Construct UnderwritingResult with AI explanation and financial offer
        underwriting_decision = UnderwritingDecision(
            merchant_id=merchant.merchant_id,
            risk_score=risk_result["score"],
            risk_tier=risk_tier,
            decision=decision,
            explanation=ai_explanation,
            financial_offer=financial_offer
        )
        
        # Step 7: Save risk result to database
        RiskScoreService.create_risk_record(db, underwriting_decision)
        
        # Step 8: Send WhatsApp notification (non-blocking, doesn't affect API response)
        if whatsapp_number:
            try:
                whatsapp_service = WhatsAppService()
                result = whatsapp_service.send_underwriting_result(
                    to_number=whatsapp_number,
                    merchant_id=merchant.merchant_id,
                    risk_tier=risk_tier,
                    decision=decision,
                    risk_score=risk_result["score"],
                    explanation=ai_explanation
                )
                logger.info(
                    f"WhatsApp notification sent | Merchant: {merchant.merchant_id} | "
                    f"SID: {result.get('sid')} | Status: {result.get('status')}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to send WhatsApp notification for {merchant.merchant_id}: {e}",
                    exc_info=True
                )
                # Do not raise - API response should not be affected by WhatsApp failure
        
        # Step 9: Return decision
        return underwriting_decision
