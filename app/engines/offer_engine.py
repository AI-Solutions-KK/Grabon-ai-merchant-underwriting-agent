"""
Financial Offer Engine for deterministic offer calculation.

Generates credit and insurance offers based on:
- Risk tier (Tier 1/2/3)
- Merchant financial metrics (GMV, monthly_revenue, credit_score)
- Mode (credit/insurance)
"""

import logging
from typing import Optional
from app.schemas.decision_schema import CreditOffer, InsuranceOffer, FinancialOffer

logger = logging.getLogger(__name__)


class OfferEngine:
    """
    Deterministic financial offer calculator for merchants.
    
    Tier-based offer generation with consistent, auditable logic.
    """
    
    # Tier 1: Excellent credit profile
    TIER1_CREDIT_LIMIT_MULTIPLIER = 1.0  # GMV / 3 = 1.0 * GMV * (1/3)
    TIER1_CREDIT_INTEREST_RATE = 10.0  # 10% APR
    
    # Tier 2: Good credit profile  
    TIER2_CREDIT_LIMIT_MULTIPLIER = 0.5  # GMV / 6 = 0.5 * GMV * (1/6)
    TIER2_CREDIT_INTEREST_RATE = 15.0  # 15% APR
    
    # Insurance: Premium as % of GMV
    TIER1_INSURANCE_PREMIUM_RATE = 0.012  # 1.2% of annual GMV
    TIER2_INSURANCE_PREMIUM_RATE = 0.020  # 2.0% of annual GMV
    
    @staticmethod
    def calculate_credit_offer(
        risk_tier: str,
        merchant_data: dict
    ) -> Optional[CreditOffer]:
        """
        Calculate deterministic credit offer based on tier and merchant financials.
        
        Returns None if merchant is Tier 3 (rejected).
        
        Args:
            risk_tier: "Tier 1", "Tier 2", or "Tier 3"
            merchant_data: Merchant financial metrics dict
            
        Returns:
            CreditOffer or None
        """
        if risk_tier == "Tier 3":
            return None
        
        # Get merchant GMV (monthly_revenue if gmv not provided)
        gmv_monthly = merchant_data.get("gmv") or merchant_data.get("monthly_revenue", 50000)
        gmv_annual = gmv_monthly * 12
        
        if risk_tier == "Tier 1":
            # Tier 1: Higher limits, lower rates
            credit_limit_amount = (gmv_annual / 3) / 100000  # Convert to lakhs
            interest_rate = OfferEngine.TIER1_CREDIT_INTEREST_RATE
        elif risk_tier == "Tier 2":
            # Tier 2: Moderate limits, higher rates
            credit_limit_amount = (gmv_annual / 6) / 100000  # Convert to lakhs
            interest_rate = OfferEngine.TIER2_CREDIT_INTEREST_RATE
        else:
            return None
        
        # Ensure minimum credit limit of 0.5 lakhs
        credit_limit_amount = max(0.5, min(credit_limit_amount, 50.0))  # Cap at 50 lakhs
        
        tenure_options = [6, 12, 24, 36] if risk_tier == "Tier 1" else [6, 12, 24]
        
        return CreditOffer(
            credit_limit_lakhs=round(credit_limit_amount, 2),
            interest_rate_percent=interest_rate,
            tenure_options_months=tenure_options
        )
    
    @staticmethod
    def calculate_insurance_offer(
        risk_tier: str,
        merchant_data: dict
    ) -> Optional[InsuranceOffer]:
        """
        Calculate deterministic insurance offer based on tier and GMV.
        
        Returns None if merchant is Tier 3 (rejected).
        
        Args:
            risk_tier: "Tier 1", "Tier 2", or "Tier 3"
            merchant_data: Merchant financial metrics dict
            
        Returns:
            InsuranceOffer or None
        """
        if risk_tier == "Tier 3":
            return None
        
        # Get merchant GMV
        gmv_monthly = merchant_data.get("gmv") or merchant_data.get("monthly_revenue", 50000)
        gmv_annual = gmv_monthly * 12
        
        if risk_tier == "Tier 1":
            # Tier 1: Higher coverage, lower premium rate
            coverage_amount = (gmv_annual / 2) / 100000  # Convert to lakhs
            premium_rate = OfferEngine.TIER1_INSURANCE_PREMIUM_RATE
            policy_type = "Premium"
        elif risk_tier == "Tier 2":
            # Tier 2: Moderate coverage, higher premium rate
            coverage_amount = (gmv_annual / 4) / 100000  # Convert to lakhs
            premium_rate = OfferEngine.TIER2_INSURANCE_PREMIUM_RATE
            policy_type = "Standard"
        else:
            return None
        
        # Calculate annual premium
        premium_amount = gmv_annual * premium_rate
        
        # Ensure realistic bounds
        coverage_amount = max(2.0, min(coverage_amount, 100.0))  # 2-100 lakhs
        premium_amount = max(1000, min(premium_amount, 500000))  # 1k-500k currency
        
        return InsuranceOffer(
            coverage_amount_lakhs=round(coverage_amount, 2),
            premium_amount=round(premium_amount, 2),
            policy_type=policy_type
        )
    
    @staticmethod
    def calculate_financial_offer(
        risk_tier: str,
        merchant_data: dict,
        mode: Optional[str] = None
    ) -> Optional[FinancialOffer]:
        """
        Calculate financial offer based on mode.
        
        Mode determines what offer structure is returned:
        - "credit": Credit offer in credit field, insurance field None
        - "insurance": Insurance offer in insurance field, credit field None
        - None or "both": Both offers calculated and returned
        
        Args:
            risk_tier: Risk tier ("Tier 1", "Tier 2", "Tier 3")
            merchant_data: Merchant financial metrics
            mode: "credit", "insurance", or None for both
            
        Returns:
            FinancialOffer with appropriate fields populated
        """
        if risk_tier == "Tier 3":
            return None
        
        credit_offer = None
        insurance_offer = None
        
        if mode is None or mode == "both" or mode == "credit":
            credit_offer = OfferEngine.calculate_credit_offer(risk_tier, merchant_data)
        
        if mode is None or mode == "both" or mode == "insurance":
            insurance_offer = OfferEngine.calculate_insurance_offer(risk_tier, merchant_data)
        
        if credit_offer is None and insurance_offer is None:
            return None
        
        return FinancialOffer(
            credit=credit_offer,
            insurance=insurance_offer
        )
