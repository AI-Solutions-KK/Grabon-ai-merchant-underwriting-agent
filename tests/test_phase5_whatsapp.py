"""
Phase 5 Step 6: Live Testing with Twilio WhatsApp

Tests:
1. API returns JSON normally
2. WhatsApp message sent (or error logged gracefully)
3. System doesn't break if WhatsApp fails
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

# Test merchants
TEST_CASES = {
    "strong_merchant": {
        "merchant_id": "LIVE_TEST_001",
        "monthly_revenue": 50000,
        "credit_score": 780,
        "years_in_business": 5,
        "existing_loans": 1,
        "past_defaults": 0,
        "description": "Strong merchant (should APPROVE)"
    },
    "weak_merchant": {
        "merchant_id": "LIVE_TEST_002",
        "monthly_revenue": 8000,
        "credit_score": 540,
        "years_in_business": 1,
        "existing_loans": 3,
        "past_defaults": 2,
        "description": "Weak merchant (should REJECT)"
    },
}

# Your WhatsApp test number (from .env or Twilio sandbox)
# NOTE: Comment out if you don't have Twilio sandbox configured
WHATSAPP_TEST_NUMBER = "whatsapp:+91XXXXXXXXXX"  # Replace with your test number

def test_api_without_whatsapp():
    """Test 1: API works without WhatsApp"""
    print("\n" + "="*70)
    print("TEST 1: API WITHOUT WHATSAPP")
    print("="*70)
    
    merchant = TEST_CASES["strong_merchant"]
    print(f"\nTesting: {merchant['description']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/underwrite",
            json={k: v for k, v in merchant.items() if k != "description"},
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"[OK] API Response received")
        print(f"     Status Code: {response.status_code}")
        print(f"     Merchant ID: {result['merchant_id']}")
        print(f"     Decision: {result['decision']}")
        print(f"     Risk Tier: {result['risk_tier']}")
        print(f"     Risk Score: {result['risk_score']}")
        print(f"     Explanation: {result['explanation'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        return False

def test_api_with_whatsapp_sandbox():
    """Test 2: API with WhatsApp (sandbox)"""
    print("\n" + "="*70)
    print("TEST 2: API WITH WHATSAPP (SANDBOX)")
    print("="*70)
    
    merchant = TEST_CASES["weak_merchant"]
    print(f"\nTesting: {merchant['description']}")
    print(f"WhatsApp Number: {WHATSAPP_TEST_NUMBER}")
    
    # Only test if number is configured
    if "XXXXXXXXXX" in WHATSAPP_TEST_NUMBER:
        print("\n[SKIP] WhatsApp test number not configured")
        print("       To enable: Replace +91XXXXXXXXXX with your test number")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/underwrite",
            json={k: v for k, v in merchant.items() if k != "description"},
            params={"whatsapp_number": WHATSAPP_TEST_NUMBER},
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"[OK] API Response with WhatsApp parameter")
        print(f"     Status Code: {response.status_code}")
        print(f"     Merchant ID: {result['merchant_id']}")
        print(f"     Decision: {result['decision']}")
        print(f"     Risk Tier: {result['risk_tier']}")
        print(f"     Risk Score: {result['risk_score']}")
        
        print(f"\n[INFO] WhatsApp message should be sent to {WHATSAPP_TEST_NUMBER}")
        print(f"       Check your Twilio console for message status")
        print(f"       Message format:")
        print(f"       ─" * 35)
        print(f"       📊 GrabCredit Underwriting Result")
        print(f"       Merchant ID: {result['merchant_id']}")
        print(f"       Risk Tier: {result['risk_tier']}")
        print(f"       Decision: {result['decision']}")
        print(f"       Risk Score: {result['risk_score']}/100")
        print(f"       ─" * 35)
        
        return True
        
    except Exception as e:
        print(f"[WARN] API with WhatsApp failed: {e}")
        print(f"       This could be:")
        print(f"       1. Twilio credentials invalid")
        print(f"       2. WhatsApp number not in sandbox")
        print(f"       3. Network issue")
        print(f"\n       Checking if API still returns valid response...")
        return False

def test_api_resilience():
    """Test 3: API resilience (WhatsApp failure doesn't break API)"""
    print("\n" + "="*70)
    print("TEST 3: API RESILIENCE (WhatsApp failure shouldn't break API)")
    print("="*70)
    
    merchant = TEST_CASES["strong_merchant"].copy()
    merchant["merchant_id"] = "RESILIENCE_TEST_001"
    
    print(f"\nTesting API returns valid response despite WhatsApp issues")
    
    try:
        # Call with invalid WhatsApp number (should still return valid API response)
        response = requests.post(
            f"{BASE_URL}/underwrite",
            json={k: v for k, v in merchant.items() if k != "description"},
            params={"whatsapp_number": "whatsapp:+9999999999"},  # Invalid number
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Verify we got valid underwriting response
        required_fields = ["merchant_id", "decision", "risk_tier", "risk_score", "explanation"]
        all_present = all(field in result for field in required_fields)
        
        if all_present:
            print(f"[PASS] API returns valid response even with invalid WhatsApp number")
            print(f"       Merchant ID: {result['merchant_id']}")
            print(f"       Decision: {result['decision']}")
            print(f"       Risk Tier: {result['risk_tier']}")
            print(f"       Risk Score: {result['risk_score']}")
            return True
        else:
            print(f"[FAIL] Response missing required fields: {required_fields}")
            print(f"       Got: {list(result.keys())}")
            return False
        
    except Exception as e:
        print(f"[FAIL] API call failed: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("PHASE 5: LIVE TESTING WITH TWILIO WHATSAPP")
    print("="*70)
    
    # Check server is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print("\n[OK] API server is running")
    except:
        print("\n[ERROR] API server not accessible on http://localhost:8000")
        print("Please start: uvicorn app.main:app --reload")
        return
    
    # Run tests
    test1 = test_api_without_whatsapp()
    test2 = test_api_with_whatsapp_sandbox()
    test3 = test_api_resilience()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum([test1, test3]) + (1 if test2 is True else 0)
    total = 3 if test2 is not None else 2
    
    print(f"\nTest 1 (API without WhatsApp): {'PASS' if test1 else 'FAIL'}")
    if test2 is None:
        print(f"Test 2 (API with WhatsApp): SKIP (test number not configured)")
    else:
        print(f"Test 2 (API with WhatsApp): {'PASS' if test2 else 'ISSUE (check credentials)'}")
    print(f"Test 3 (API Resilience): {'PASS' if test3 else 'FAIL'}")
    
    print(f"\n{'='*70}")
    if passed >= 2:
        print(f"[SUCCESS] Phase 5 tests passed ({passed}/{total})")
        print(f"\nNext steps:")
        print(f"1. If Test 2 SKIPped: Configure MERCHANT_TEST_NUMBER with your Twilio sandbox")
        print(f"2. If Test 2 failed: Check Twilio credentials in .env")
        print(f"3. Monitor Twilio console for delivery status")
    else:
        print(f"[FAIL] Some tests failed ({passed}/{total})")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
