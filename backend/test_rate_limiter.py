"""
Test suite for Token Bucket Rate Limiter

Run with: python test_rate_limiter.py
"""

import asyncio
import time
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.redis_service import redis_service
from app.utils.rate_limiter import (
    TokenBucketRateLimiter,
    RateLimitWindow,
    RATE_LIMIT_PRESETS,
    TIER_MULTIPLIERS
)


async def test_token_bucket_basic():
    """Test basic token bucket functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: Token Bucket - Basic Functionality")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up any previous test data
    await rate_limiter.reset_limit("test_user_1", "test:basic")

    # First request should be allowed
    result = await rate_limiter.check_limit(
        identifier="test_user_1",
        resource="test:basic",
        max_tokens=5,
        refill_rate=1.0,
        bucket_size=5
    )

    print(f"Request 1: allowed={result.allowed}, remaining={result.remaining}")
    assert result.allowed, "First request should be allowed"
    assert result.remaining == 4, "Should have 4 tokens remaining"

    # Make 4 more requests to exhaust bucket
    for i in range(4):
        result = await rate_limiter.check_limit(
            identifier="test_user_1",
            resource="test:basic",
            max_tokens=5,
            refill_rate=1.0,
            bucket_size=5
        )
        print(f"Request {i+2}: allowed={result.allowed}, remaining={result.remaining}")

    # 6th request should be denied
    result = await rate_limiter.check_limit(
        identifier="test_user_1",
        resource="test:basic",
        max_tokens=5,
        refill_rate=1.0,
        bucket_size=5
    )

    print(f"Request 6: allowed={result.allowed}, retry_after={result.retry_after}s")
    assert not result.allowed, "6th request should be denied"
    assert result.retry_after > 0, "Should have positive retry_after"

    print("✅ TEST 1 PASSED: Token bucket basic functionality works")


async def test_token_bucket_refill():
    """Test token refill over time"""
    print("\n" + "=" * 60)
    print("TEST 2: Token Bucket - Refill Over Time")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up
    await rate_limiter.reset_limit("test_user_2", "test:refill")

    # Exhaust all tokens (bucket size 3, refill rate 1/sec)
    for i in range(3):
        result = await rate_limiter.check_limit(
            identifier="test_user_2",
            resource="test:refill",
            max_tokens=3,
            refill_rate=1.0,  # 1 token per second
            bucket_size=3
        )
        print(f"Request {i+1}: allowed={result.allowed}")

    # Should be denied now
    result = await rate_limiter.check_limit(
        identifier="test_user_2",
        resource="test:refill",
        max_tokens=3,
        refill_rate=1.0,
        bucket_size=3
    )
    print(f"Request after exhaustion: allowed={result.allowed}")
    assert not result.allowed, "Should be denied after exhausting tokens"

    # Wait for token to refill
    print("Waiting 1.5 seconds for token refill...")
    await asyncio.sleep(1.5)

    # Should be allowed now
    result = await rate_limiter.check_limit(
        identifier="test_user_2",
        resource="test:refill",
        max_tokens=3,
        refill_rate=1.0,
        bucket_size=3
    )
    print(f"Request after refill: allowed={result.allowed}")
    assert result.allowed, "Should be allowed after refill"

    print("✅ TEST 2 PASSED: Token refill works correctly")


async def test_tier_multipliers():
    """Test tier-based rate limit multipliers"""
    print("\n" + "=" * 60)
    print("TEST 3: Tier Multipliers")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Test with different tiers
    tiers = ["free", "pro", "enterprise"]

    for tier in tiers:
        # Clean up
        await rate_limiter.reset_limit(f"test_user_tier_{tier}", "test:tier")

        # Check limit
        result = await rate_limiter.check_limit(
            identifier=f"test_user_tier_{tier}",
            resource="test:tier",
            max_tokens=10,
            refill_rate=1.0,
            bucket_size=10,
            tier=tier
        )

        expected_max = int(10 * TIER_MULTIPLIERS[tier])
        print(f"Tier '{tier}': max_tokens={result.max_tokens} (expected: {expected_max})")
        assert result.max_tokens == expected_max, f"Tier {tier} should have {expected_max} max tokens"

    print("✅ TEST 3 PASSED: Tier multipliers work correctly")


async def test_sliding_window():
    """Test sliding window rate limiting"""
    print("\n" + "=" * 60)
    print("TEST 4: Sliding Window Rate Limiting")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up
    await rate_limiter.reset_limit("test_user_3", "test:window")

    # Make 3 requests (limit is 3)
    for i in range(3):
        result = await rate_limiter.check_sliding_window(
            identifier="test_user_3",
            resource="test:window",
            limit=3,
            window=RateLimitWindow.MINUTE
        )
        print(f"Request {i+1}: allowed={result.allowed}, remaining={result.remaining}")
        assert result.allowed, f"Request {i+1} should be allowed"

    # 4th request should be denied
    result = await rate_limiter.check_sliding_window(
        identifier="test_user_3",
        resource="test:window",
        limit=3,
        window=RateLimitWindow.MINUTE
    )
    print(f"Request 4: allowed={result.allowed}, retry_after={result.retry_after}s")
    assert not result.allowed, "4th request should be denied"

    print("✅ TEST 4 PASSED: Sliding window works correctly")


async def test_concurrent_limit():
    """Test concurrent connection limiting"""
    print("\n" + "=" * 60)
    print("TEST 5: Concurrent Connection Limiting")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up
    await rate_limiter.reset_limit("test_user_4", "test:concurrent")

    # Check initial limit (max 3 concurrent)
    result = await rate_limiter.check_concurrent_limit(
        identifier="test_user_4",
        resource="test:concurrent",
        max_concurrent=3
    )
    print(f"Initial check: allowed={result.allowed}, remaining={result.remaining}")
    assert result.allowed, "Should be allowed initially"
    assert result.remaining == 3, "Should have 3 remaining"

    # Add 3 connections
    for i in range(3):
        await rate_limiter.add_concurrent_connection(
            identifier="test_user_4",
            resource="test:concurrent",
            connection_id=f"conn_{i}"
        )
        print(f"Added connection conn_{i}")

    # Check limit again
    result = await rate_limiter.check_concurrent_limit(
        identifier="test_user_4",
        resource="test:concurrent",
        max_concurrent=3
    )
    print(f"After 3 connections: allowed={result.allowed}")
    assert not result.allowed, "Should be denied at max concurrent"

    # Remove one connection
    await rate_limiter.remove_concurrent_connection(
        identifier="test_user_4",
        resource="test:concurrent",
        connection_id="conn_0"
    )
    print("Removed connection conn_0")

    # Check again
    result = await rate_limiter.check_concurrent_limit(
        identifier="test_user_4",
        resource="test:concurrent",
        max_concurrent=3
    )
    print(f"After removal: allowed={result.allowed}")
    assert result.allowed, "Should be allowed after removal"

    print("✅ TEST 5 PASSED: Concurrent limiting works correctly")


async def test_presets():
    """Test rate limit presets"""
    print("\n" + "=" * 60)
    print("TEST 6: Rate Limit Presets")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up
    await rate_limiter.reset_limit("test_user_5", "agent:create")

    # Test agent:create preset
    result = await rate_limiter.check_limit(
        identifier="test_user_5",
        resource="agent:create"  # Uses preset
    )

    preset = RATE_LIMIT_PRESETS["agent:create"]
    print(f"Using preset 'agent:create': bucket_size={preset['bucket_size']}")
    print(f"Result: allowed={result.allowed}, max_tokens={result.max_tokens}")
    assert result.max_tokens == preset["bucket_size"], "Should use preset bucket size"

    print("✅ TEST 6 PASSED: Presets work correctly")


async def test_reset_limit():
    """Test rate limit reset functionality"""
    print("\n" + "=" * 60)
    print("TEST 7: Rate Limit Reset")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Exhaust tokens
    for i in range(5):
        await rate_limiter.check_limit(
            identifier="test_user_6",
            resource="test:reset",
            max_tokens=5,
            refill_rate=0.1,  # Very slow refill
            bucket_size=5
        )

    # Should be denied
    result = await rate_limiter.check_limit(
        identifier="test_user_6",
        resource="test:reset",
        max_tokens=5,
        refill_rate=0.1,
        bucket_size=5
    )
    print(f"Before reset: allowed={result.allowed}")
    assert not result.allowed, "Should be denied before reset"

    # Reset limit
    await rate_limiter.reset_limit("test_user_6", "test:reset")
    print("Rate limit reset")

    # Should be allowed now
    result = await rate_limiter.check_limit(
        identifier="test_user_6",
        resource="test:reset",
        max_tokens=5,
        refill_rate=0.1,
        bucket_size=5
    )
    print(f"After reset: allowed={result.allowed}")
    assert result.allowed, "Should be allowed after reset"

    print("✅ TEST 7 PASSED: Reset works correctly")


async def test_rate_limit_headers():
    """Test rate limit response headers"""
    print("\n" + "=" * 60)
    print("TEST 8: Rate Limit Headers")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up
    await rate_limiter.reset_limit("test_user_7", "test:headers")

    result = await rate_limiter.check_limit(
        identifier="test_user_7",
        resource="test:headers",
        max_tokens=10,
        refill_rate=1.0,
        bucket_size=10
    )

    headers = result.to_headers()
    print(f"Headers: {headers}")

    assert "X-RateLimit-Limit" in headers, "Should have X-RateLimit-Limit header"
    assert "X-RateLimit-Remaining" in headers, "Should have X-RateLimit-Remaining header"
    assert "X-RateLimit-Reset" in headers, "Should have X-RateLimit-Reset header"
    assert "X-RateLimit-Resource" in headers, "Should have X-RateLimit-Resource header"
    assert headers["X-RateLimit-Limit"] == "10", "Limit should be 10"
    assert headers["X-RateLimit-Resource"] == "test:headers", "Resource should match"

    print("✅ TEST 8 PASSED: Headers are generated correctly")


async def test_fail_open():
    """Test that rate limiter fails open (allows) on Redis errors"""
    print("\n" + "=" * 60)
    print("TEST 9: Fail Open Behavior")
    print("=" * 60)

    # Create rate limiter with a mock Redis service that will fail
    class FailingRedisService:
        class FailingClient:
            async def hgetall(self, key):
                raise Exception("Redis connection failed")
            async def hset(self, key, mapping):
                raise Exception("Redis connection failed")
            async def expire(self, key, seconds):
                raise Exception("Redis connection failed")

        redis_client = FailingClient()

    failing_service = FailingRedisService()
    rate_limiter = TokenBucketRateLimiter(failing_service)

    # Should allow request despite Redis failure
    result = await rate_limiter.check_limit(
        identifier="test_user_8",
        resource="test:failopen",
        max_tokens=5,
        refill_rate=1.0,
        bucket_size=5
    )

    print(f"Result with failing Redis: allowed={result.allowed}")
    assert result.allowed, "Should fail open (allow) when Redis fails"

    print("✅ TEST 9 PASSED: Fails open correctly on Redis errors")


async def test_get_limit_status():
    """Test getting current rate limit status"""
    print("\n" + "=" * 60)
    print("TEST 10: Get Limit Status")
    print("=" * 60)

    rate_limiter = TokenBucketRateLimiter(redis_service)

    # Clean up and make some requests
    await rate_limiter.reset_limit("test_user_9", "test:status")

    # Make 3 requests
    for i in range(3):
        await rate_limiter.check_limit(
            identifier="test_user_9",
            resource="test:status",
            max_tokens=10,
            refill_rate=1.0,
            bucket_size=10
        )

    # Get status
    status = await rate_limiter.get_limit_status(
        identifier="test_user_9",
        resource="test:status"
    )

    print(f"Status: {status}")
    assert status["status"] == "active", "Should be active"
    assert status["tokens"] < 10, "Tokens should be less than max after usage"
    assert status["resource"] == "test:status", "Resource should match"

    print("✅ TEST 10 PASSED: Get status works correctly")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TOKEN BUCKET RATE LIMITER - TEST SUITE")
    print("=" * 60)

    # Connect to Redis
    connected = await redis_service.connect()
    if not connected:
        print("❌ Failed to connect to Redis. Skipping tests.")
        return False

    print("✅ Connected to Redis")

    tests = [
        test_token_bucket_basic,
        test_token_bucket_refill,
        test_tier_multipliers,
        test_sliding_window,
        test_concurrent_limit,
        test_presets,
        test_reset_limit,
        test_rate_limit_headers,
        test_fail_open,
        test_get_limit_status,
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
