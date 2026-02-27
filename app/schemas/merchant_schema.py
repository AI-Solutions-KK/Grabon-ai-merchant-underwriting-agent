from pydantic import BaseModel, Field
from typing import Optional, List


class MerchantInput(BaseModel):
    """
    Pydantic model for merchant underwriting input data.
    
    Captures merchant financial metrics and business history for risk assessment.
    Aligns with Project 07 SOW requirements.
    """
    # Core identification
    merchant_id: str = Field(..., description="Unique identifier for the merchant")
    category: Optional[str] = Field(default=None, description="Merchant category (e.g., Electronics, Fashion, Food)")
    
    # Legacy required fields
    monthly_revenue: float = Field(..., gt=0, description="Monthly revenue in currency units")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (300-850)")
    years_in_business: int = Field(..., ge=0, description="Number of years the business has been operating")
    existing_loans: int = Field(..., ge=0, description="Number of existing loans")
    past_defaults: int = Field(..., ge=0, description="Number of past defaults")
    
    # Legacy optional fields
    gmv: float = Field(default=0.0, ge=0, description="Gross Merchandise Value in currency units")
    refund_rate: float = Field(default=0.0, ge=0, le=1, description="Refund rate as percentage (0-1)")
    chargeback_rate: float = Field(default=0.0, ge=0, le=1, description="Chargeback rate as percentage (0-1)")
    
    # SOW-required behavioral metrics
    monthly_gmv_12m: Optional[List[float]] = Field(
        default=None, 
        description="Array of 12 monthly GMV values (last 12 months)"
    )
    coupon_redemption_rate: float = Field(
        default=0.0, 
        ge=0, 
        le=1, 
        description="Coupon redemption rate (0-1)"
    )
    unique_customer_count: int = Field(
        default=0, 
        ge=0, 
        description="Total unique customers"
    )
    customer_return_rate: float = Field(
        default=0.0, 
        ge=0, 
        le=1, 
        description="% of returning customers (0-1)"
    )
    avg_order_value: float = Field(
        default=0.0, 
        ge=0, 
        description="Average order value in currency"
    )
    seasonality_index: float = Field(
        default=1.0, 
        ge=0.1, 
        description="Peak/trough ratio for seasonality"
    )
    deal_exclusivity_rate: float = Field(
        default=0.0, 
        ge=0, 
        le=1, 
        description="% exclusive deals (0-1)"
    )
    return_and_refund_rate: float = Field(
        default=0.0, 
        ge=0, 
        le=1, 
        description="% returns/refunds (0-1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "MERCH_12345",
                "category": "Electronics",
                "monthly_revenue": 50000.0,
                "credit_score": 750,
                "years_in_business": 5,
                "existing_loans": 2,
                "past_defaults": 0,
                "gmv": 75000.0,
                "refund_rate": 0.05,
                "chargeback_rate": 0.02,
                "monthly_gmv_12m": [65000, 68000, 70000, 72000, 75000, 76000, 78000, 80000, 79000, 77000, 76000, 75000],
                "coupon_redemption_rate": 0.12,
                "unique_customer_count": 4500,
                "customer_return_rate": 0.35,
                "avg_order_value": 18.50,
                "seasonality_index": 1.15,
                "deal_exclusivity_rate": 0.08,
                "return_and_refund_rate": 0.08
            }
        }
