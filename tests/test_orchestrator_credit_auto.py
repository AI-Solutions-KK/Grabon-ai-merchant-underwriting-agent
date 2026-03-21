from app.orchestrator.orchestrator import Orchestrator
from app.schemas.merchant_schema import MerchantInput


class _DummyDB:
    pass


def test_orchestrator_uses_computed_credit_score(monkeypatch):
    captured = {"credit_seen": None}

    def _fake_calc(_merchant):
        return 777

    def _fake_create_merchant(_db, _merchant):
        return None

    def _fake_risk_eval(merchant):
        captured["credit_seen"] = merchant.credit_score
        return {
            "auto_reject": False,
            "reason": None,
            "score": 80,
            "score_breakdown": {},
            "category_benchmark": {},
            "gmv_yoy_pct": None,
        }

    def _fake_decision_eval(_risk_result):
        return ("Tier 1", "APPROVED", "ok")

    def _fake_offer(*_args, **_kwargs):
        return None

    def _fake_expl(*_args, **_kwargs):
        return "deterministic explanation"

    def _fake_create_risk(_db, _decision):
        return None

    monkeypatch.setattr("app.orchestrator.orchestrator.CreditEngine.calculate_credit_score", _fake_calc)
    monkeypatch.setattr("app.orchestrator.orchestrator.MerchantService.create_merchant", _fake_create_merchant)
    monkeypatch.setattr("app.orchestrator.orchestrator.RiskEngine.evaluate_risk", _fake_risk_eval)
    monkeypatch.setattr("app.orchestrator.orchestrator.DecisionEngine.evaluate", _fake_decision_eval)
    monkeypatch.setattr("app.orchestrator.orchestrator.OfferEngine.calculate_financial_offer", _fake_offer)
    monkeypatch.setattr("app.orchestrator.orchestrator.ClaudeUnderwritingAgent.generate_explanation", _fake_expl)
    monkeypatch.setattr("app.orchestrator.orchestrator.RiskScoreService.create_risk_record", _fake_create_risk)
    monkeypatch.setattr("app.orchestrator.orchestrator.get_config", lambda *_args, **_kwargs: "OFF")

    merchant = MerchantInput(
        merchant_id="ORCH_AUTO_CREDIT_1",
        monthly_revenue=90000,
        credit_score=350,  # must be ignored/overridden
        years_in_business=6,
        existing_loans=0,
        past_defaults=0,
    )

    result = Orchestrator.process_underwriting(merchant=merchant, db=_DummyDB(), whatsapp_number=None, mode=None)

    assert captured["credit_seen"] == 777
    assert result.risk_score == 80
    assert result.risk_tier == "Tier 1"
