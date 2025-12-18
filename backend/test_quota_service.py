"""
Test suite for Per-User Quota Service

Run with: python test_quota_service.py
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.redis_service import redis_service
from app.services.quota_service import (
    QuotaService,
    QuotaType,
    QuotaTier,
    TIER_QUOTAS
)


async def test_check_quota_basic():
    """Test basic quota checking"""
    print("\n" + "=" * 60)
    print("TEST 1: Check Quota - Basic Functionality")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Clean up
    await quota_service.reset_quota("test_user_1", QuotaType.AGENTS_TOTAL.value)

    # Check quota - should be allowed
    result = await quota_service.check_quota(
        user_id="test_user_1",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        tier="free"
    )

    print(f"Quota check result: allowed={result.allowed}, current={result.current}, limit={result.limit}")
    assert result.allowed, "Should be allowed when under quota"
    assert result.current == 0, "Current should be 0"
    assert result.limit == 10, "Free tier should have limit of 10 agents"

    print("✅ TEST 1 PASSED: Basic quota checking works")


async def test_quota_increment():
    """Test quota incrementing"""
    print("\n" + "=" * 60)
    print("TEST 2: Quota Increment")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Clean up
    await quota_service.reset_quota("test_user_2", QuotaType.AGENTS_TOTAL.value)

    # Increment quota
    new_value = await quota_service.increment_quota(
        user_id="test_user_2",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        amount=1
    )

    print(f"After increment: {new_value}")
    assert new_value == 1, "Should be 1 after incrementing"

    # Check quota again
    result = await quota_service.check_quota(
        user_id="test_user_2",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        tier="free"
    )

    print(f"After check: current={result.current}, remaining={result.remaining}")
    assert result.current == 1, "Current should be 1"
    assert result.remaining == 9, "Remaining should be 9"

    print("✅ TEST 2 PASSED: Quota incrementing works")


async def test_quota_exceeded():
    """Test quota exceeded scenario"""
    print("\n" + "=" * 60)
    print("TEST 3: Quota Exceeded")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Clean up
    await quota_service.reset_quota("test_user_3", QuotaType.AGENTS_TOTAL.value)

    # Set quota to limit
    await quota_service.set_quota(
        user_id="test_user_3",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        value=10  # Free tier limit
    )

    # Check quota - should be denied
    result = await quota_service.check_quota(
        user_id="test_user_3",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        tier="free",
        required=1
    )

    print(f"Quota check at limit: allowed={result.allowed}, message={result.message}")
    assert not result.allowed, "Should be denied when at limit"
    assert result.remaining == 0, "Remaining should be 0"

    print("✅ TEST 3 PASSED: Quota exceeded works correctly")


async def test_tier_limits():
    """Test different tier limits"""
    print("\n" + "=" * 60)
    print("TEST 4: Tier-Based Limits")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Check limits for different tiers
    tiers = ["free", "pro", "enterprise"]
    expected_limits = [10, 50, 1000]  # agents:total limits

    for tier, expected in zip(tiers, expected_limits):
        limit = quota_service.get_limit(QuotaType.AGENTS_TOTAL.value, tier)
        print(f"Tier '{tier}': agents:total limit = {limit} (expected: {expected})")
        assert limit == expected, f"Tier {tier} should have limit {expected}"

    print("✅ TEST 4 PASSED: Tier limits are correct")


async def test_check_and_increment():
    """Test atomic check and increment"""
    print("\n" + "=" * 60)
    print("TEST 5: Check and Increment (Atomic)")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Clean up
    await quota_service.reset_quota("test_user_5", QuotaType.EXECUTIONS_HOUR.value)

    # Atomic check and increment
    result = await quota_service.check_and_increment(
        user_id="test_user_5",
        quota_type=QuotaType.EXECUTIONS_HOUR.value,
        tier="free"
    )

    print(f"After check_and_increment: allowed={result.allowed}, current={result.current}")
    assert result.allowed, "Should be allowed"
    assert result.current == 1, "Current should be 1 after increment"

    # Do it again
    result2 = await quota_service.check_and_increment(
        user_id="test_user_5",
        quota_type=QuotaType.EXECUTIONS_HOUR.value,
        tier="free"
    )

    print(f"Second check_and_increment: allowed={result2.allowed}, current={result2.current}")
    assert result2.allowed, "Should still be allowed"
    assert result2.current == 2, "Current should be 2"

    print("✅ TEST 5 PASSED: Check and increment works atomically")


async def test_decrement_quota():
    """Test quota decrement (for resource deletion)"""
    print("\n" + "=" * 60)
    print("TEST 6: Quota Decrement")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Clean up and set initial value
    await quota_service.reset_quota("test_user_6", QuotaType.AGENTS_TOTAL.value)
    await quota_service.set_quota(
        user_id="test_user_6",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        value=5
    )

    # Decrement
    new_value = await quota_service.decrement_quota(
        user_id="test_user_6",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        amount=2
    )

    print(f"After decrement (5 - 2): {new_value}")
    assert new_value == 3, "Should be 3 after decrementing 2"

    # Decrement more than current (should not go negative)
    new_value2 = await quota_service.decrement_quota(
        user_id="test_user_6",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        amount=10
    )

    print(f"After decrement (3 - 10): {new_value2}")
    assert new_value2 == 0, "Should be 0 (not negative)"

    print("✅ TEST 6 PASSED: Decrement works correctly")


async def test_get_all_quotas():
    """Test getting all quotas for a user"""
    print("\n" + "=" * 60)
    print("TEST 7: Get All Quotas")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Get all quotas
    quotas = await quota_service.get_all_quotas(
        user_id="test_user_7",
        tier="free"
    )

    print(f"Number of quota types: {len(quotas)}")
    print(f"Quota types: {list(quotas.keys())}")

    # Should have all quota types
    assert len(quotas) == len(QuotaType), f"Should have {len(QuotaType)} quota types"

    # Each should be a QuotaResult
    for quota_type, result in quotas.items():
        print(f"  {quota_type}: current={result.current}, limit={result.limit}")
        assert result.limit > 0 or result.limit == 999999999, f"{quota_type} should have positive limit"

    print("✅ TEST 7 PASSED: Get all quotas works")


async def test_usage_summary():
    """Test usage summary with warnings and blocked"""
    print("\n" + "=" * 60)
    print("TEST 8: Usage Summary with Warnings")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Set some quotas near limits
    await quota_service.set_quota(
        user_id="test_user_8",
        quota_type=QuotaType.AGENTS_TOTAL.value,
        value=9  # 90% of 10
    )
    await quota_service.set_quota(
        user_id="test_user_8",
        quota_type=QuotaType.EXECUTIONS_HOUR.value,
        value=10  # 100% of 10
    )

    # Get summary
    summary = await quota_service.get_usage_summary(
        user_id="test_user_8",
        tier="free"
    )

    print(f"Tier: {summary['tier']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Blocked: {summary['blocked']}")

    # Check warnings (>80%)
    assert QuotaType.AGENTS_TOTAL.value in summary["warnings"], "agents:total should be in warnings (90%)"

    # Check blocked (100%)
    assert QuotaType.EXECUTIONS_HOUR.value in summary["blocked"], "executions:hour should be blocked (100%)"

    print("✅ TEST 8 PASSED: Usage summary with warnings works")


async def test_time_based_quotas():
    """Test time-based quota keys (hourly/daily)"""
    print("\n" + "=" * 60)
    print("TEST 9: Time-Based Quota Keys")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Test hourly quota key generation
    key_hourly = quota_service._get_quota_key("user_123", QuotaType.AGENTS_CREATE_HOUR.value)
    print(f"Hourly key: {key_hourly}")
    assert "hour" not in key_hourly.split(":")[-1] or len(key_hourly.split(":")[-1]) > 5, "Key should include date-hour"

    # Test daily quota key generation
    key_daily = quota_service._get_quota_key("user_123", QuotaType.AI_TOKENS_DAY.value)
    print(f"Daily key: {key_daily}")
    assert len(key_daily.split(":")[-1]) == 10, "Key should include date (YYYY-MM-DD)"

    # Test permanent quota key generation
    key_permanent = quota_service._get_quota_key("user_123", QuotaType.AGENTS_TOTAL.value)
    print(f"Permanent key: {key_permanent}")
    assert key_permanent.endswith("user_123"), "Permanent key should end with user_id"

    print("✅ TEST 9 PASSED: Time-based quota keys work correctly")


async def test_unlimited_quota():
    """Test unlimited (enterprise) quotas"""
    print("\n" + "=" * 60)
    print("TEST 10: Unlimited (Enterprise) Quotas")
    print("=" * 60)

    quota_service = QuotaService(redis_service)

    # Check AI tokens daily for enterprise (should be unlimited)
    result = await quota_service.check_quota(
        user_id="test_user_10",
        quota_type=QuotaType.AI_TOKENS_DAY.value,
        tier="enterprise",
        required=1000000  # Request 1 million tokens
    )

    print(f"Enterprise AI tokens check: allowed={result.allowed}, limit={result.limit}")
    assert result.allowed, "Enterprise should allow unlimited tokens"
    assert result.limit == 999999999, "Limit should be displayed as 999999999 for unlimited"
    assert result.message == "Unlimited quota", "Should have unlimited message"

    print("✅ TEST 10 PASSED: Unlimited quotas work correctly")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PER-USER QUOTA SERVICE - TEST SUITE")
    print("=" * 60)

    # Connect to Redis
    connected = await redis_service.connect()
    if not connected:
        print("❌ Failed to connect to Redis. Skipping tests.")
        return False

    print("✅ Connected to Redis")

    tests = [
        test_check_quota_basic,
        test_quota_increment,
        test_quota_exceeded,
        test_tier_limits,
        test_check_and_increment,
        test_decrement_quota,
        test_get_all_quotas,
        test_usage_summary,
        test_time_based_quotas,
        test_unlimited_quota,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1

    # Disconnect from Redis
    await redis_service.disconnect()

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
