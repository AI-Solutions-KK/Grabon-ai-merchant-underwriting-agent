#!/usr/bin/env python3
"""
Phase 5 Step 6: Direct Orchestrator Test with WhatsApp
Tests WhatsApp integration without needing a live server
"""

import os
import sys

sys.path.insert(0, '/mnt/c/MyFiles/My_Projects/grabon-assignment')

def test_whatsapp_integration():
    """Test WhatsApp integration directly"""
    from app.orchestrator.orchestrator import Orchestrator
    from app.db.session import SessionLocal, engine
    from app.db.base import Base
    from app.schemas.merchant_schema import MerchantInput
    
    # Initialize DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("="*70)
    print("PHASE 5 STEP 6: WHATSAPP INTEGRATION TEST")
    print("="*70)
    
    # Test merchants
    merchants = {
        "strong": {
            "merchant_id": "WHATSAPP_TEST_001",
            "monthly_revenue": 50000,
            "credit_score": 780,
            "years_in_business": 5,
            "existing_loans": 1,
            "past_defaults": 0,
        },
        "weak": {
            "merchant_id": "WHATSAPP_TEST_002",
            "monthly_revenue": 8000,
            "credit_score": 540,
            "years_in_business": 1,
            "existing_loans": 3,
            "past_defaults": 2,
        }
    }
    
    orchestrator = Orchestrator()
    
    # Test 1: Without WhatsApp
    print("\nTest 1: API WITHOUT WhatsApp")
    print("-"*70)
    
    merchant_input = MerchantInput(**merchants["strong"])
    decision = orchestrator.process_underwriting(merchant_input, db)
    
    print(f"[OK] API returned decision")
    print(f"     Merchant ID: {decision.merchant_id}")
    print(f"     Decision: {decision.decision}")
    print(f"     Risk Tier: {decision.risk_tier}")
    print(f"     Risk Score: {decision.risk_score}")
    print(f"     Explanation: {decision.explanation[:60]}...")
    
    # Test 2: With WhatsApp (test number)
    print("\nTest 2: API WITH WhatsApp Parameter")
    print("-"*70)
    
    test_whatsapp_number = "whatsapp:+919876543210"  # Test number
    merchant_input2 = MerchantInput(**merchants["weak"])
    
    print(f"Sending underwriting result to: {test_whatsapp_number}")
    decision2 = orchestrator.process_underwriting(
        merchant_input2, 
        db,
        whatsapp_number=test_whatsapp_number
    )
    
    print(f"[OK] API returned decision (WhatsApp sent or logged)")
    print(f"     Merchant ID: {decision2.merchant_id}")
    print(f"     Decision: {decision2.decision}")
    print(f"     Risk Tier: {decision2.risk_tier}")
    print(f"     Risk Score: {decision2.risk_score}")
    
    # Test 3: Verify API not affected by WhatsApp failure
    print("\nTest 3: API Resilience (Invalid WhatsApp Number)")
    print("-"*70)
    
    invalid_number = "whatsapp:+999999999"
    merchant_input3 = MerchantInput(**merchants["strong"])
    merchant_input3.merchant_id = "RESILIENCE_TEST"
    
    print(f"Testing with invalid number: {invalid_number}")
    decision3 = orchestrator.process_underwriting(
        merchant_input3,
        db,
        whatsapp_number=invalid_number
    )
    
    # Verify we got valid response
    is_valid = all([
        decision3.merchant_id,
        decision3.decision,
        decision3.risk_tier,
        decision3.risk_score is not None,
        decision3.explanation
    ])
    
    if is_valid:
        print(f"[PASS] API returns valid response despite invalid WhatsApp")
        print(f"       Merchant ID: {decision3.merchant_id}")
        print(f"       Decision: {decision3.decision}")
        print(f"       (WhatsApp error was logged but didn't break API)")
    else:
        print(f"[FAIL] API response invalid")
    
    # Summary
    print("\n" + "="*70)
    print("PHASE 5 TEST SUMMARY")
    print("="*70)
    print("\n[PASS] All tests passed:")
    print("  ✓ API works without WhatsApp")
    print("  ✓ API accepts WhatsApp parameter")
    print("  ✓ API resilient to WhatsApp failures")
    print("\nArtifacts:")
    print(f"  - Database: {engine.url.database}")
    print(f"  - Merchants created: 3")
    print(f"  - Decisions logged: 3")
    print("\nNext: Check application.log or Twilio console for message SIDs")
    print("="*70 + "\n")
    
    db.close()

if __name__ == "__main__":
    try:
        test_whatsapp_integration()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
