# 📊 Interview Response: Merchant Scoring Logic (Updated)

> Updated for the latest implementation: **merchant profile → computed credit score → computed risk score (0–100) → tier decision**.

## 🎯 Executive Clarification

The underwriting pipeline is now fully deterministic and reproducible end-to-end:

1. Merchant profile is submitted/synced
2. System **computes credit score automatically** from profile data (no randomness)
3. Risk engine computes 0–100 risk score using weighted rules
4. Decision engine maps score to tier and decision
5. Offer engine generates credit/insurance offers for approved tiers

This means users/ops can add merchant data without manually deciding a final credit score.

---

## ✅ What changed in implementation

### 1) New deterministic profile-based credit engine
**File:** `app/engines/credit_engine.py` (new file)

```python
class CreditEngine:
    MIN_SCORE = 300
    MAX_SCORE = 850

    # Bank-style category weights (FICO-like)
    WEIGHT_PAYMENT_HISTORY = 0.35
    WEIGHT_AMOUNTS_OWED = 0.30
    WEIGHT_LENGTH_HISTORY = 0.15
    WEIGHT_CREDIT_MIX = 0.10
    WEIGHT_NEW_CREDIT = 0.10

    @staticmethod
    def calculate_credit_score(merchant: MerchantInput) -> int:
        # Factor scores in [0,100]
        payment_history = _payment_history_score(merchant)  # defaults, chargebacks, refunds
        amounts_owed = _amounts_owed_score(merchant)        # loan pressure + dispute stress
        length_history = _length_history_score(merchant)    # years in business proxy
        credit_mix = _credit_mix_score(merchant)            # loyalty/exclusivity/stability proxy
        new_credit = _new_credit_score(merchant)            # active borrowing + negative trend proxy

        # Weighted index in [0,100]
        weighted_index = (
            payment_history * WEIGHT_PAYMENT_HISTORY
            + amounts_owed * WEIGHT_AMOUNTS_OWED
            + length_history * WEIGHT_LENGTH_HISTORY
            + credit_mix * WEIGHT_CREDIT_MIX
            + new_credit * WEIGHT_NEW_CREDIT
        )

        # Map to bureau range [300,850]
        return clamp(300 + (weighted_index * 5.5), 300, 850)
```

This is deterministic and auditable: no random calls, no external APIs. Same profile gives the same score every time.

---

### 2) Orchestration now enforces computed credit
**File:** `app/orchestrator/orchestrator.py`

**Before (old pattern — caller supplied credit_score):**
```python
def process_underwriting(merchant: MerchantInput, db, ...):
    MerchantService.create_merchant(db, merchant)          # used whatever was in request
    risk_result = RiskEngine.evaluate_risk(merchant)       # scored against caller's number
```

**After (Step 0 injection):**
```python
def process_underwriting(merchant: MerchantInput, db, ...):
    # Step 0: recompute from profile — overwrite any submitted value
    computed_credit_score = CreditEngine.calculate_credit_score(merchant)
    merchant = merchant.model_copy(update={"credit_score": computed_credit_score})
    #          ↑ Pydantic v2: creates a new immutable object with patched field

    MerchantService.create_merchant(db, merchant)     # persists computed credit
    risk_result = RiskEngine.evaluate_risk(merchant)  # uses computed credit (40% weight)
```

The injected credit score flows untouched through all downstream stages.

---

### 3) Merchant persistence now updates profile + computed credit
**File:** `app/services/merchant_service.py`

**Before:** if merchant already existed, the function returned early with no changes.

**After (upsert pattern):**
```python
def create_merchant(db, merchant_input):
    # Credit is already computed by orchestrator;
    # fallback for direct service calls (monitor, engine_service)
    derived_credit_score = (
        merchant_input.credit_score
        if merchant_input.credit_score is not None
        else CreditEngine.calculate_credit_score(merchant_input)
    )

    existing = db.query(Merchant).filter(
        Merchant.merchant_id == merchant_input.merchant_id
    ).first()

    if existing:
        existing.monthly_revenue = merchant_input.monthly_revenue
        existing.credit_score    = derived_credit_score   # ← always overwrites
        existing.years_in_business = merchant_input.years_in_business
        # ... all other profile fields updated ...
        db.commit()
        return existing

    db.add(Merchant(..., credit_score=derived_credit_score))
    db.commit()
```

---

### 4) Change detection uses profile fields (not stored credit)
**File:** `app/services/monitor_service.py`

**Before:** fingerprint included `credit_score` column value — a derived value triggering itself.

**After:** fingerprint uses only the raw input profile fields:
```python
def _merchant_fingerprint(merchant) -> str:
    payload = {
        "monthly_revenue":      merchant.monthly_revenue,
        "years_in_business":    merchant.years_in_business,
        "existing_loans":       merchant.existing_loans or 0,
        "past_defaults":        merchant.past_defaults or 0,
        "gmv":                  round(merchant.gmv or 0.0, 2),
        "monthly_gmv_12m":      [round(v, 2) for v in (merchant.monthly_gmv_12m or [])],
        "refund_rate":          round(merchant.refund_rate or 0.0, 4),
        "chargeback_rate":      round(merchant.chargeback_rate or 0.0, 4),
        "customer_return_rate": round(merchant.customer_return_rate or 0.0, 4),
        # credit_score intentionally excluded — it's a computed output, not a trigger
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
```

If `current_fp != last_fp` OR no prior risk record → orchestrator re-runs with `credit_score=None`.

---

### 5) Batch/monitor processing rebuilds input from profile
**Files:** `app/services/engine_service.py`, `app/services/monitor_service.py`

**Before:** both reconstructed `MerchantInput` from DB and passed `credit_score=merchant.credit_score` (trusting stale DB value).

**After:**
```python
# engine_service.py and monitor_service.py — reconstruction snippet
merchant_input = MerchantInput(
    merchant_id=merchant.merchant_id,
    monthly_revenue=merchant.monthly_revenue,
    credit_score=None,              # ← orchestrator will compute fresh
    years_in_business=merchant.years_in_business,
    monthly_gmv_12m=merchant.monthly_gmv_12m or [],
    # ... remaining fields ...
)
orchestrator.process_underwriting(merchant_input, db)
# orchestrator Step 0 computes credit from profile before doing anything
```

---

### 6) Seed/init flows aligned to deterministic credit
**File:** `app/db/init_db.py`

**Before:**
```python
merchant = Merchant(
    merchant_id="M001",
    credit_score=data["credit_score"],  # ← hardcoded number in seed dict
    ...
)
```

**After:**
```python
from app.engines.credit_engine import CreditEngine
from app.schemas.merchant_schema import MerchantInput

# Build input object from profile fields only
m_input = MerchantInput(merchant_id=row["id"], monthly_revenue=row["revenue"], ...)

# Compute credit deterministically
computed_credit = CreditEngine.calculate_credit_score(m_input)

merchant = Merchant(
    merchant_id=row["id"],
    credit_score=computed_credit,   # ← always profile-derived
    ...
)
```

**File:** `app/scripts/seed_merchants.py`

**Before (tuple layout included a credit score column):**
```python
("M001", "TechGadgets",  85000, 5, 2, 0, 70000, 750, 0.03, 0.01),
#                                              ^^^^ manual credit score
```

**After:**
```python
("M001", "TechGadgets",  85000, 5, 2, 0, 70000, 0.03, 0.01),
#       no credit_score column — MerchantInput(...) omits it entirely
# orchestrator computes it at Step 0
```

---

---

## 🔑 Schema change that makes it optional

**File:** `app/schemas/merchant_schema.py`

**Before:**
```python
credit_score: int = Field(..., ge=300, le=850)   # required — caller must supply
```

**After:**
```python
credit_score: Optional[int] = Field(
    default=None, ge=300, le=850,
    description="Optional legacy field. System always computes and uses profile-derived score."
)
```

Existing clients that still send `credit_score` in the JSON body continue to work without error.
The value is accepted, then silently replaced by the orchestrator's Step 0 computation.

---

## 🔢 Scoring logic summary

### A) Credit score (300–850)
Computed from profile signals:
- Positive: higher revenue, more years in business, stronger repeat customers, exclusivity, positive GMV trend
- Negative: existing loans, defaults, high refund/chargeback/return rates, high seasonality

Then clamped to:
$$
\text{credit\_score} \in [300, 850]
$$

### B) Risk score (0–100)
Computed via deterministic weighted rules in `risk_engine.py`, including hard-reject checks:
- Credit score < 550 → auto reject
- Past defaults ≥ 3 → auto reject

Otherwise weighted positives/penalties produce score:
$$
\text{risk\_score} \in [0, 100]
$$

### C) Tier mapping
- Score ≥ 75 → Tier 1 (APPROVED)
- 50 ≤ Score < 75 → Tier 2 (APPROVED_WITH_CONDITIONS)
- Score < 50 → Tier 3 (REJECTED)

---

## 🧪 Reproducibility guarantee

- Same merchant profile → same computed credit score
- Same computed credit score + same profile metrics → same risk score
- No random generators used in scoring path
- Deterministic, auditable, testable

---

## 🗄️ DB/seed/direct-SQL behavior

### If merchant is inserted or updated via Python seed
- Profile is processed
- Credit is computed deterministically
- Risk + tier follow the standard pipeline

### If merchant profile is inserted/updated directly in DB (SQL)
- Monitor fingerprint detects profile changes (or missing prior risk record)
- Merchant is reprocessed automatically in engine/monitor cycle
- Credit is recomputed and used for risk/tier

---

## 🧭 Current expected flow (final)

```text
Merchant profile data
      ↓
CreditEngine.calculate_credit_score()   [300–850, deterministic]
      ↓
RiskEngine.evaluate_risk()              [0–100, deterministic]
      ↓
DecisionEngine.evaluate()               [Tier 1/2/3 + decision]
      ↓
OfferEngine.calculate_financial_offer()
      ↓
Persist + optional WhatsApp delivery
```

---

## ✅ Verification notes

- Added tests for deterministic credit calculation and orchestration integration:
  - `tests/test_credit_engine.py`
  - `tests/test_orchestrator_credit_auto.py`
- Existing core risk/decision tests continue to pass.

---

*Updated on: March 21, 2026*  
*Project: GrabOn AI Merchant Underwriting System*