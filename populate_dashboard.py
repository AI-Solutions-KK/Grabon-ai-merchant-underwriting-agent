#!/usr/bin/env python3
"""
Phase 6 Dashboard Test: Populate with test merchants
"""

import sys
sys.path.insert(0, '/mnt/c/MyFiles/My_Projects/grabon-assignment')

def populate_test_data():
    """Create test merchants and underwriting results"""
    from app.orchestrator.orchestrator import Orchestrator
    from app.db.session import SessionLocal, engine
    from app.db.base import Base
    from app.schemas.merchant_schema import MerchantInput
    
    # Initialize DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    orchestrator = Orchestrator()
    
    # Test merchants
    test_merchants = [
        {
            "merchant_id": "DASHBOARD_001",
            "monthly_revenue": 50000,
            "credit_score": 780,
            "years_in_business": 5,
            "existing_loans": 1,
            "past_defaults": 0,
            "name": "Premium Tech Solutions"
        },
        {
            "merchant_id": "DASHBOARD_002",
            "monthly_revenue": 25000,
            "credit_score": 680,
            "years_in_business": 3,
            "existing_loans": 2,
            "past_defaults": 0,
            "name": "Growth Retail Co"
        },
        {
            "merchant_id": "DASHBOARD_003",
            "monthly_revenue": 12000,
            "credit_score": 620,
            "years_in_business": 1,
            "existing_loans": 3,
            "past_defaults": 1,
            "name": "Startup Services"
        },
        {
            "merchant_id": "DASHBOARD_004",
            "monthly_revenue": 8000,
            "credit_score": 540,
            "years_in_business": 1,
            "existing_loans": 2,
            "past_defaults": 2,
            "name": "High Risk Ventures"
        },
    ]
    
    print("="*70)
    print("POPULATING DASHBOARD WITH TEST DATA")
    print("="*70)
    
    for merchant_data in test_merchants:
        # Remove name field as it's not in schema
        merchant_input_data = {k: v for k, v in merchant_data.items() if k != "name"}
        merchant_input = MerchantInput(**merchant_input_data)
        
        decision = orchestrator.process_underwriting(merchant_input, db)
        
        print(f"\n[OK] {merchant_data['name']}")
        print(f"     ID: {decision.merchant_id}")
        print(f"     Decision: {decision.decision}")
        print(f"     Tier: {decision.risk_tier}")
        print(f"     Score: {decision.risk_score}")
    
    print("\n" + "="*70)
    print(f"DASHBOARD READY: {len(test_merchants)} merchants loaded")
    print("="*70)
    print("\nAccess the dashboard at:")
    print("  http://localhost:8000/dashboard/")
    print("\nMerchants available:")
    for m in test_merchants:
        print(f"  - {m['merchant_id']}: {m['name']}")
    print("="*70 + "\n")
    
    db.close()

if __name__ == "__main__":
    try:
        populate_test_data()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
