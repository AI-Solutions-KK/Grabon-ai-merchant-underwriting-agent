from app.schemas.merchant_schema import MerchantInput


class CreditEngine:
    """
        Deterministic profile-based credit score engine.

        Produces a bureau-like credit score in range 300-850 using only merchant
        profile/behavioral metrics (no randomness, no external API).

        Methodology:
        - Uses a bank-style weighted framework inspired by published FICO factor
            categories (payment history, amounts owed, length/history, mix, new credit).
        - Since this is merchant underwriting (not consumer bureau pull), each factor
            is mapped to deterministic merchant-side proxy metrics.
    """

    MIN_SCORE = 300
    MAX_SCORE = 850

    # Bank-style category weights (FICO-like structure)
    WEIGHT_PAYMENT_HISTORY = 0.35
    WEIGHT_AMOUNTS_OWED = 0.30
    WEIGHT_LENGTH_HISTORY = 0.15
    WEIGHT_CREDIT_MIX = 0.10
    WEIGHT_NEW_CREDIT = 0.10

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _payment_history_score(merchant: MerchantInput) -> float:
        """
        Proxy for repayment quality (0-100).

        Strong penalties for defaults and high dispute/refund behaviour.
        """
        score = 100.0

        defaults = float(merchant.past_defaults or 0)
        score -= defaults * 35.0

        rr = float(merchant.refund_rate or 0.0)
        cb = float(merchant.chargeback_rate or 0.0)
        rfr = float(merchant.return_and_refund_rate or 0.0)

        # Tiered behaviour penalties
        if rr > 0.30:
            score -= 20.0
        elif rr > 0.15:
            score -= 10.0

        if cb > 0.10:
            score -= 25.0
        elif cb > 0.05:
            score -= 12.0

        if rfr > 0.20:
            score -= 15.0
        elif rfr > 0.10:
            score -= 8.0

        return CreditEngine._clamp(score, 0.0, 100.0)

    @staticmethod
    def _amounts_owed_score(merchant: MerchantInput) -> float:
        """
        Proxy for debt burden / over-extension (0-100).

        Uses active-loan pressure and dispute-related cashflow stress.
        """
        loans = float(merchant.existing_loans or 0)
        rr = float(merchant.refund_rate or 0.0)
        cb = float(merchant.chargeback_rate or 0.0)
        rfr = float(merchant.return_and_refund_rate or 0.0)

        # 0 loans => best; 5+ loans => max pressure contribution
        loan_pressure = CreditEngine._clamp(loans / 5.0, 0.0, 1.0)

        # Proxy for utilization-like stress from money going out/disputed
        dispute_stress = CreditEngine._clamp((rr + cb + rfr) / 0.50, 0.0, 1.0)

        # Weighted within the factor
        score = 100.0 - ((loan_pressure * 70.0) + (dispute_stress * 30.0))
        return CreditEngine._clamp(score, 0.0, 100.0)

    @staticmethod
    def _length_history_score(merchant: MerchantInput) -> float:
        """Proxy for credit history length (0-100) from years in business."""
        years = float(merchant.years_in_business or 0)
        # 10+ years treated as full maturity
        return CreditEngine._clamp((years / 10.0) * 100.0, 0.0, 100.0)

    @staticmethod
    def _credit_mix_score(merchant: MerchantInput) -> float:
        """
        Proxy for profile quality mix (0-100).

        Uses repeat-customer quality, exclusivity moat, and seasonality stability.
        """
        crr = float(merchant.customer_return_rate or 0.0)
        excl = float(merchant.deal_exclusivity_rate or 0.0)
        si = float(merchant.seasonality_index or 1.0)

        loyalty_component = CreditEngine._clamp(crr, 0.0, 1.0) * 45.0
        moat_component = CreditEngine._clamp(excl, 0.0, 1.0) * 25.0

        # seasonality 1.0 is stable (good), >3.0 very volatile (bad)
        stability_ratio = 1.0 - CreditEngine._clamp((si - 1.0) / 2.0, 0.0, 1.0)
        stability_component = stability_ratio * 30.0

        return CreditEngine._clamp(
            loyalty_component + moat_component + stability_component,
            0.0,
            100.0,
        )

    @staticmethod
    def _new_credit_score(merchant: MerchantInput) -> float:
        """
        Proxy for recent-credit risk (0-100).

        Uses active borrowing load and short-term GMV trend direction.
        """
        loans = float(merchant.existing_loans or 0)
        loan_penalty = CreditEngine._clamp(loans / 6.0, 0.0, 1.0) * 60.0

        gmv_penalty = 0.0
        gmv_list = merchant.monthly_gmv_12m or []
        if len(gmv_list) >= 12:
            h1_avg = sum(gmv_list[:6]) / 6
            h2_avg = sum(gmv_list[6:]) / 6
            if h1_avg > 0:
                yoy_pct = ((h2_avg - h1_avg) / h1_avg) * 100.0
                # Penalize deterioration only (positive trend not penalized)
                if yoy_pct < 0:
                    gmv_penalty = CreditEngine._clamp(abs(yoy_pct) / 40.0, 0.0, 1.0) * 40.0

        return CreditEngine._clamp(100.0 - loan_penalty - gmv_penalty, 0.0, 100.0)

    @staticmethod
    def calculate_credit_score(merchant: MerchantInput) -> int:
        """
        Calculate deterministic credit score from merchant profile.

        Notes:
        - Input `merchant.credit_score` is ignored by design.
        - The same merchant profile always yields the same score.
        """
        # Category scores (0-100)
        payment_history = CreditEngine._payment_history_score(merchant)
        amounts_owed = CreditEngine._amounts_owed_score(merchant)
        length_history = CreditEngine._length_history_score(merchant)
        credit_mix = CreditEngine._credit_mix_score(merchant)
        new_credit = CreditEngine._new_credit_score(merchant)

        # Weighted index in [0,100]
        weighted_index = (
            payment_history * CreditEngine.WEIGHT_PAYMENT_HISTORY
            + amounts_owed * CreditEngine.WEIGHT_AMOUNTS_OWED
            + length_history * CreditEngine.WEIGHT_LENGTH_HISTORY
            + credit_mix * CreditEngine.WEIGHT_CREDIT_MIX
            + new_credit * CreditEngine.WEIGHT_NEW_CREDIT
        )

        # Map [0,100] → [300,850]
        final_score = int(round(CreditEngine.MIN_SCORE + (weighted_index * 5.5)))
        return int(CreditEngine._clamp(final_score, CreditEngine.MIN_SCORE, CreditEngine.MAX_SCORE))
