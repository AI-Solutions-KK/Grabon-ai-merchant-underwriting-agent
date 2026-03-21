# GrabOn AI Merchant Underwriting — Project Notes (Final)

Only logic, formulas, and Q&A-ready explanations (no analogy).

---

## Q1) What is the exact underwriting flow?

```text
Merchant Profile
   ↓
CreditEngine (300–850)
   ↓
RiskEngine (0–100)
   ↓
DecisionEngine (Tier + Decision)
   ↓
OfferEngine
   ↓
Persist + Optional WhatsApp
```

---

## Q2) How is credit score calculated now?

### Formula

Let:

- $P$ = payment-history proxy score (0–100)
- $A$ = amounts-owed proxy score (0–100)
- $L$ = length/history proxy score (0–100)
- $M$ = credit-mix proxy score (0–100)
- $N$ = new-credit proxy score (0–100)

Weighted index:

$$
W = 0.35P + 0.30A + 0.15L + 0.10M + 0.10N
$$

Final score:

$$
credit\_score = clamp(300 + 5.5W,\ 300,\ 850)
$$

### In words (how it computes)

1. Compute 5 factor scores from merchant profile fields.
2. Multiply each factor by its weight.
3. Add weighted values to get a 0–100 index.
4. Scale index into 300–850 range.
5. Clamp result so it never goes below 300 or above 850.

### Factor-to-field mapping

- `P`: defaults + refund/chargeback/return behavior
- `A`: existing loans + dispute/refund stress
- `L`: years in business
- `M`: customer return rate + exclusivity + seasonality stability
- `N`: loan load + negative GMV trend risk

---

## Q3) Is it random?

No.

- No random number generator
- No external scoring API call
- Same input profile → same credit score every run

---

## Q4) What happens if client sends `credit_score` in request JSON?

It is accepted for backward compatibility, but not trusted as final input.

In `orchestrator.process_underwriting()`:

```python
computed_credit_score = CreditEngine.calculate_credit_score(merchant)
merchant = merchant.model_copy(update={"credit_score": computed_credit_score})
```

So system always uses profile-derived score.

---

## Q5) How are risk score and tier decided?

### Hard rejects first

- `credit_score < 550` → auto reject
- `past_defaults >= 3` → auto reject

### Otherwise score bands

- `score >= 75` → Tier 1 → APPROVED
- `50 <= score < 75` → Tier 2 → APPROVED_WITH_CONDITIONS
- `score < 50` → Tier 3 → REJECTED

---

## Q6) How does DB/direct SQL change get reprocessed?

`monitor_service` computes MD5 fingerprint from profile fields.

If fingerprint changed (or risk record missing), merchant is re-run through orchestrator.

`credit_score` is excluded from fingerprint because it is computed output, not trigger input.

---

## Q7) What changed in codebase (final)

- Added deterministic weighted `CreditEngine`
- Orchestrator Step 0 credit recomputation
- Schema `credit_score` made optional
- Merchant upsert now updates existing rows
- Monitor fingerprint tracks profile fields
- Seed/init/batch paths aligned to recompute credit

---

## Q8) Verification

Executed tests:

- `tests/test_credit_engine.py`
- `tests/test_orchestrator_credit_auto.py`
- `tests/test_risk_engine.py`
- `tests/test_decision_engine.py`

Result: **17 passed**.
