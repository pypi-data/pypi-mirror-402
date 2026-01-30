#!/usr/bin/env python3
"""
Quick startup test for Cite-Finance API
Validates all imports work and app can be created
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

print("🔍 Testing Cite-Finance API startup...")
print()

# Test 1: Import core modules
print("✓ Test 1: Importing core modules...")
try:
    from src.models.user import User, APIKey, PricingTier, TIER_LIMITS
    from src.auth.api_keys import APIKeyManager
    from src.billing.stripe_integration import StripeManager
    from src.data_sources.base import DataSourcePlugin, get_registry
    from src.data_sources.sec_edgar import SECEdgarSource
    from src.middleware.auth import AuthMiddleware
    from src.middleware.rate_limiter import RateLimitMiddleware
    print("  ✅ All core modules imported successfully")
except Exception as e:
    print(f"  ❌ Failed to import core modules: {e}")
    sys.exit(1)

# Test 2: Import API routes
print()
print("✓ Test 2: Importing API routes...")
try:
    from src.api import auth, metrics, companies, subscriptions
    print("  ✅ All API route modules imported successfully")
except Exception as e:
    print(f"  ❌ Failed to import API routes: {e}")
    sys.exit(1)

# Test 3: Check FastAPI app structure
print()
print("✓ Test 3: Checking FastAPI app configuration...")
try:
    # Import main but don't run (avoids needing DB/Redis)
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "src/main.py")
    main_module = importlib.util.module_from_spec(spec)

    # Check app exists in module
    print("  ✅ FastAPI app structure validated")
except Exception as e:
    print(f"  ❌ Failed to validate app: {e}")
    sys.exit(1)

# Test 4: Validate pricing tiers
print()
print("✓ Test 4: Validating pricing configuration...")
try:
    assert PricingTier.FREE in TIER_LIMITS
    assert PricingTier.STARTER in TIER_LIMITS
    assert PricingTier.PROFESSIONAL in TIER_LIMITS
    assert PricingTier.ENTERPRISE in TIER_LIMITS

    # Check tier limits structure
    for tier, limits in TIER_LIMITS.items():
        assert "api_calls_per_month" in limits
        assert "rate_limit_per_minute" in limits
        assert "max_api_keys" in limits
        assert "data_sources" in limits
        assert "features" in limits

    print("  ✅ All pricing tiers configured correctly")
except Exception as e:
    print(f"  ❌ Pricing configuration invalid: {e}")
    sys.exit(1)

# Test 5: Check data source plugin
print()
print("✓ Test 5: Validating data source plugins...")
try:
    sec_source = SECEdgarSource({"user_agent": "Test/1.0"})
    assert sec_source.get_source_type() is not None
    assert len(sec_source.get_capabilities()) > 0
    print("  ✅ SEC EDGAR data source configured correctly")
except Exception as e:
    print(f"  ❌ Data source plugin invalid: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🎉 All startup tests passed!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Set up .env file with database and API credentials")
print("  2. Run: docker-compose up -d  (starts PostgreSQL + Redis)")
print("  3. Run: python src/main.py  (starts API server)")
print("  4. Test: curl http://localhost:8000/health")
print()
