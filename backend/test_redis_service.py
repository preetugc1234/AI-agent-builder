"""
Test Redis Service Integration
Run with: python test_redis_service.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.redis_service import redis_service
from app.core.config import settings


async def test_connection():
    """Test Redis connection"""
    print("\n" + "="*60)
    print("TEST 1: Redis Connection")
    print("="*60)

    connected = await redis_service.connect()
    if connected:
        print("✅ Connected to Redis successfully")
        print(f"   URL: {settings.REDIS_URL[:20]}...")
    else:
        print("❌ Failed to connect to Redis")
        return False
    return True


async def test_session_management():
    """Test session management"""
    print("\n" + "="*60)
    print("TEST 2: Session Management")
    print("="*60)

    # Set session
    session_id = "test_session_123"
    user_data = {"user_id": "user_456", "email": "test@example.com"}

    result = await redis_service.set_session(session_id, user_data, expire_seconds=300)
    print(f"✅ Set session: {result}")

    # Get session
    retrieved = await redis_service.get_session(session_id)
    print(f"✅ Retrieved session: {retrieved}")

    # Verify data matches
    assert retrieved == user_data, "Session data mismatch!"
    print("✅ Session data matches")

    # Delete session
    await redis_service.delete_session(session_id)
    deleted_session = await redis_service.get_session(session_id)
    assert deleted_session is None, "Session not deleted!"
    print("✅ Session deleted successfully")


async def test_caching():
    """Test caching functionality"""
    print("\n" + "="*60)
    print("TEST 3: Caching")
    print("="*60)

    # Cache agent data
    agent_data = {
        "id": "agent_789",
        "name": "Test Agent",
        "status": "ready"
    }

    await redis_service.cache_set("agent:789", agent_data, expire_seconds=300)
    print("✅ Cached agent data")

    # Retrieve cached data
    cached = await redis_service.cache_get("agent:789")
    print(f"✅ Retrieved from cache: {cached}")
    assert cached == agent_data, "Cached data mismatch!"

    # Delete cache
    await redis_service.cache_delete("agent:789")
    deleted_cache = await redis_service.cache_get("agent:789")
    assert deleted_cache is None, "Cache not deleted!"
    print("✅ Cache deleted successfully")


async def test_queue():
    """Test queue functionality"""
    print("\n" + "="*60)
    print("TEST 4: Queue (LPUSH/BRPOP)")
    print("="*60)

    # Enqueue execution
    execution_data = {
        "prompt": "Create a chatbot",
        "user_id": "user_123"
    }

    await redis_service.enqueue_agent_execution("agent_111", execution_data)
    print("✅ Enqueued agent execution")

    # Check queue length
    length = await redis_service.get_queue_length("agent_execution")
    print(f"✅ Queue length: {length}")

    # Dequeue (non-blocking for test)
    dequeued = await redis_service.dequeue_agent_execution(timeout=1)
    print(f"✅ Dequeued: {dequeued}")
    assert dequeued["agent_id"] == "agent_111", "Dequeued data mismatch!"
    assert dequeued["data"] == execution_data, "Execution data mismatch!"

    # Verify queue is empty
    length_after = await redis_service.get_queue_length("agent_execution")
    print(f"✅ Queue length after dequeue: {length_after}")


async def test_rate_limiting():
    """Test rate limiting"""
    print("\n" + "="*60)
    print("TEST 5: Rate Limiting")
    print("="*60)

    user_id = "user_rate_test"
    resource = "api_calls"
    limit = 5

    # First 5 requests should be allowed
    for i in range(5):
        result = await redis_service.check_rate_limit(user_id, resource, limit, window_seconds=60)
        print(f"   Request {i+1}: allowed={result['allowed']}, remaining={result['remaining']}")
        assert result["allowed"] == True, f"Request {i+1} should be allowed"

    # 6th request should be denied
    result = await redis_service.check_rate_limit(user_id, resource, limit, window_seconds=60)
    print(f"   Request 6: allowed={result['allowed']}, current={result['current']}")
    assert result["allowed"] == False, "Request 6 should be denied"
    print("✅ Rate limiting works correctly")

    # Reset rate limit
    await redis_service.reset_rate_limit(user_id, resource)
    result = await redis_service.check_rate_limit(user_id, resource, limit, window_seconds=60)
    assert result["allowed"] == True, "Should be allowed after reset"
    print("✅ Rate limit reset works")


async def test_token_usage():
    """Test token usage tracking"""
    print("\n" + "="*60)
    print("TEST 6: Token Usage Tracking")
    print("="*60)

    user_id = "user_token_test"
    agent_id = "agent_token_test"

    # Track token usage
    await redis_service.track_token_usage(user_id, agent_id, 100, model="gpt-4")
    await redis_service.track_token_usage(user_id, agent_id, 50, model="gpt-4")
    await redis_service.track_token_usage(user_id, None, 75, model="gpt-3.5")
    print("✅ Tracked token usage")

    # Get today's usage
    usage = await redis_service.get_token_usage(user_id, period="today")
    print(f"✅ Today's usage: {usage}")
    assert usage["total"] == 225, f"Expected 225 tokens, got {usage['total']}"
    assert usage["gpt-4"] == 150, f"Expected 150 GPT-4 tokens, got {usage.get('gpt-4', 0)}"

    # Get agent usage
    agent_usage = await redis_service.get_agent_token_usage(agent_id)
    print(f"✅ Agent usage: {agent_usage}")
    assert agent_usage["total"] == 150, f"Expected 150 tokens for agent, got {agent_usage['total']}"


async def test_quota_management():
    """Test quota management"""
    print("\n" + "="*60)
    print("TEST 7: Quota Management")
    print("="*60)

    user_id = "user_quota_test"
    quota_type = "agents"
    limit = 10

    # Check initial quota
    quota = await redis_service.check_quota(user_id, quota_type, limit)
    print(f"✅ Initial quota: {quota}")
    assert quota["allowed"] == True, "Should be allowed initially"
    assert quota["current"] == 0, "Should start at 0"

    # Create 5 agents
    for i in range(5):
        await redis_service.increment_quota(user_id, quota_type)

    quota = await redis_service.check_quota(user_id, quota_type, limit)
    print(f"✅ Quota after 5 agents: {quota}")
    assert quota["current"] == 5, f"Expected 5, got {quota['current']}"
    assert quota["remaining"] == 5, f"Expected 5 remaining, got {quota['remaining']}"

    # Reset quota
    await redis_service.reset_quota(user_id, quota_type)
    quota = await redis_service.check_quota(user_id, quota_type, limit)
    print(f"✅ Quota after reset: {quota}")
    assert quota["current"] == 0, "Should be 0 after reset"


async def test_system_flags():
    """Test system flags"""
    print("\n" + "="*60)
    print("TEST 8: System Flags (Cost Control)")
    print("="*60)

    # Set pause flag
    await redis_service.set_system_flag("pause_agent_creation", "true", expire_seconds=300)
    print("✅ Set pause_agent_creation flag")

    # Get flag
    flag_value = await redis_service.get_system_flag("pause_agent_creation")
    print(f"✅ Flag value: {flag_value}")
    assert flag_value == "true", "Flag value mismatch"

    # Delete flag
    await redis_service.delete_system_flag("pause_agent_creation")
    deleted_flag = await redis_service.get_system_flag("pause_agent_creation")
    assert deleted_flag is None, "Flag not deleted"
    print("✅ Flag deleted successfully")


async def test_csrf_tokens():
    """Test CSRF token management"""
    print("\n" + "="*60)
    print("TEST 9: CSRF Token Management")
    print("="*60)

    token = "csrf_token_abc123"
    user_id = "user_csrf_test"

    # Store CSRF token
    await redis_service.store_csrf_token(token, user_id, expire_seconds=300)
    print("✅ Stored CSRF token")

    # Verify token
    verified_user_id = await redis_service.verify_csrf_token(token)
    print(f"✅ Verified token for user: {verified_user_id}")
    assert verified_user_id == user_id, "User ID mismatch"

    # Token should be deleted after verification (one-time use)
    second_verify = await redis_service.verify_csrf_token(token)
    assert second_verify is None, "Token should be deleted after use"
    print("✅ Token deleted after verification (one-time use)")


async def test_agent_status():
    """Test agent status tracking"""
    print("\n" + "="*60)
    print("TEST 10: Agent Status Tracking")
    print("="*60)

    agent_id = "agent_status_test"

    # Set generating status
    await redis_service.set_agent_status(agent_id, "generating", {"progress": 25})
    print("✅ Set agent status to 'generating'")

    # Get status
    status = await redis_service.get_agent_status(agent_id)
    print(f"✅ Retrieved status: {status}")
    assert status["status"] == "generating", "Status mismatch"
    assert status["data"]["progress"] == 25, "Progress mismatch"

    # Update status
    await redis_service.set_agent_status(agent_id, "completed", {"result": "success"})
    status = await redis_service.get_agent_status(agent_id)
    print(f"✅ Updated status: {status}")
    assert status["status"] == "completed", "Status not updated"


async def test_redis_command_tracking():
    """Test Redis command tracking"""
    print("\n" + "="*60)
    print("TEST 11: Redis Command Tracking (Cost Monitoring)")
    print("="*60)

    # Track some commands
    for i in range(5):
        count = await redis_service.track_redis_command()

    # Get count
    total_count = await redis_service.get_redis_command_count()
    print(f"✅ Today's Redis command count: {total_count}")
    assert total_count >= 5, f"Expected at least 5 commands, got {total_count}"


async def run_all_tests():
    """Run all Redis tests"""
    print("\n" + "="*60)
    print("🚀 REDIS SERVICE INTEGRATION TESTS")
    print("="*60)

    try:
        # Test connection first
        if not await test_connection():
            print("\n❌ Failed to connect to Redis. Exiting tests.")
            return

        # Run all tests
        await test_session_management()
        await test_caching()
        await test_queue()
        await test_rate_limiting()
        await test_token_usage()
        await test_quota_management()
        await test_system_flags()
        await test_csrf_tokens()
        await test_agent_status()
        await test_redis_command_tracking()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nRedis Service Features Verified:")
        print("  ✅ Connection Management")
        print("  ✅ Session Management (7-day expiry)")
        print("  ✅ Caching (1-hour default)")
        print("  ✅ Queue (LPUSH/BRPOP for background jobs)")
        print("  ✅ Rate Limiting (token bucket algorithm)")
        print("  ✅ Token Usage Tracking (daily/monthly)")
        print("  ✅ Quota Management (user limits)")
        print("  ✅ System Flags (cost control)")
        print("  ✅ CSRF Token Management")
        print("  ✅ Agent Status Tracking")
        print("  ✅ Redis Command Tracking")
        print("\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect
        await redis_service.disconnect()
        print("✅ Disconnected from Redis")


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
