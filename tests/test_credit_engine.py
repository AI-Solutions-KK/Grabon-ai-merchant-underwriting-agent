from app.engines.credit_engine import CreditEngine
from app.schemas.merchant_schema import MerchantInput


class TestCreditEngine:
    def test_deterministic_same_input_same_score(self):
        merchant = MerchantInput(
            merchant_id="CREDIT_DET_1",
            monthly_revenue=80000,
            years_in_business=5,
            existing_loans=1,
            past_defaults=0,
            refund_rate=0.03,
            chargeback_rate=0.01,
            customer_return_rate=0.42,
            deal_exclusivity_rate=0.12,
            seasonality_index=1.3,
            return_and_refund_rate=0.05,
            monthly_gmv_12m=[70000, 72000, 71000, 73000, 74000, 75000, 76000, 77000, 78000, 79000, 80000, 81000],
        )

        s1 = CreditEngine.calculate_credit_score(merchant)
        s2 = CreditEngine.calculate_credit_score(merchant)

        assert s1 == s2
        assert 300 <= s1 <= 850

    def test_poor_profile_lower_than_strong_profile(self):
        strong = MerchantInput(
            merchant_id="CREDIT_STRONG",
            monthly_revenue=150000,
            years_in_business=8,
            existing_loans=0,
            past_defaults=0,
            refund_rate=0.01,
            chargeback_rate=0.002,
            customer_return_rate=0.60,
            deal_exclusivity_rate=0.30,
            seasonality_index=1.1,
            return_and_refund_rate=0.02,
        )
        weak = MerchantInput(
            merchant_id="CREDIT_WEAK",
            monthly_revenue=15000,
            years_in_business=1,
            existing_loans=4,
            past_defaults=2,
            refund_rate=0.25,
            chargeback_rate=0.08,
            customer_return_rate=0.10,
            deal_exclusivity_rate=0.01,
            seasonality_index=2.4,
            return_and_refund_rate=0.18,
        )

        strong_score = CreditEngine.calculate_credit_score(strong)
        weak_score = CreditEngine.calculate_credit_score(weak)

        assert strong_score > weak_score
