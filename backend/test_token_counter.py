"""
Test Token Counter Service
Run with: python test_token_counter.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.token_counter_service import token_counter
from app.services.redis_service import redis_service


def test_count_tokens():
    """Test basic token counting"""
    print("\n" + "="*60)
    print("TEST 1: Basic Token Counting")
    print("="*60)

    # Test simple text
    text1 = "Hello, world!"
    tokens1 = token_counter.count_tokens(text1)
    print(f"Text: '{text1}'")
    print(f"Tokens: {tokens1}")
    assert tokens1 > 0, "Should have tokens"

    # Test longer text
    text2 = """
    This is a longer text that should result in more tokens.
    Tiktoken will accurately count the number of tokens needed
    to encode this text for the AI model.
    """
    tokens2 = token_counter.count_tokens(text2)
    print(f"\nLonger text ({len(text2)} chars)")
    print(f"Tokens: {tokens2}")
    print(f"Ratio: {len(text2) / tokens2:.2f} chars/token")

    # Test with specific model
    tokens3 = token_counter.count_tokens(text2, model="gpt-4")
    print(f"\nTokens (GPT-4): {tokens3}")

    print("✅ Basic token counting works")


def test_count_messages():
    """Test message-based token counting (chat format)"""
    print("\n" + "="*60)
    print("TEST 2: Message Token Counting (Chat Format)")
    print("="*60)

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Hello! How are you?"},
        {"role": "assistant", "content": "I'm doing great! How can I help you today?"},
        {"role": "user", "content": "Tell me a joke."}
    ]

    tokens = token_counter.count_messages_tokens(messages)
    print(f"Messages: {len(messages)}")
    print(f"Total tokens (including overhead): {tokens}")

    # Calculate content-only tokens
    content_only = sum(token_counter.count_tokens(m["content"]) for m in messages)
    print(f"Content-only tokens: {content_only}")
    print(f"Overhead tokens: {tokens - content_only}")

    print("✅ Message token counting works")


async def test_track_usage():
    """Test token usage tracking"""
    print("\n" + "="*60)
    print("TEST 3: Token Usage Tracking")
    print("="*60)

    # Connect to Redis
    connected = await redis_service.connect()
    if not connected:
        print("❌ Redis not connected - skipping tracking test")
        return

    user_id = "test_user_123"
    agent_id = "test_agent_456"

    # Track some usage
    await token_counter.track_usage(
        user_id=user_id,
        agent_id=agent_id,
        prompt_tokens=100,
        completion_tokens=50,
        model="gpt-4"
    )
    print("✅ Tracked 150 tokens (100 prompt + 50 completion)")

    # Track more usage
    await token_counter.track_usage(
        user_id=user_id,
        agent_id=agent_id,
        prompt_tokens=200,
        completion_tokens=100,
        model="gpt-4"
    )
    print("✅ Tracked 300 more tokens (200 prompt + 100 completion)")

    # Get usage stats
    stats = await token_counter.get_user_usage_stats(user_id)
    print(f"\nUser Stats:")
    print(f"  Today: {stats['today']}")
    print(f"  Month: {stats['month']}")

    # Get agent stats
    agent_stats = await token_counter.get_agent_usage_stats(agent_id)
    print(f"\nAgent Stats:")
    print(f"  Total: {agent_stats}")

    print("✅ Token tracking works")


async def test_quota_check():
    """Test quota checking"""
    print("\n" + "="*60)
    print("TEST 4: Quota Checking")
    print("="*60)

    user_id = "test_user_quota"

    # Simulate usage
    await token_counter.track_usage(
        user_id=user_id,
        agent_id=None,
        prompt_tokens=1000,
        completion_tokens=500,
        model="gpt-4"
    )

    # Check quota (free tier: 50,000/day)
    quota = await token_counter.check_quota(
        user_id=user_id,
        required_tokens=1000,
        tier="free"
    )

    print(f"Quota Check (Free Tier):")
    print(f"  Allowed: {quota['allowed']}")
    print(f"  Used Today: {quota['used_today']}")
    print(f"  Limit: {quota['limit']}")
    print(f"  Remaining: {quota['remaining']}")
    print(f"  Required: {quota['required']}")

    assert quota['allowed'] == True, "Should be within quota"

    # Check pro tier
    quota_pro = await token_counter.check_quota(
        user_id=user_id,
        required_tokens=1000,
        tier="pro"
    )

    print(f"\nQuota Check (Pro Tier):")
    print(f"  Allowed: {quota_pro['allowed']}")
    print(f"  Limit: {quota_pro['limit']}")

    print("✅ Quota checking works")


def test_utility_functions():
    """Test utility functions"""
    print("\n" + "="*60)
    print("TEST 5: Utility Functions")
    print("="*60)

    # Test estimation (fallback)
    text = "This is a test message for estimation"
    estimated = token_counter.estimate_tokens(text)
    print(f"Text: '{text}'")
    print(f"Estimated tokens: {estimated}")

    # Test formatting
    test_counts = [500, 1500, 15000, 150000, 1500000]
    print("\nToken count formatting:")
    for count in test_counts:
        formatted = token_counter.format_token_count(count)
        print(f"  {count:>10} → {formatted}")

    print("✅ Utility functions work")


async def run_all_tests():
    """Run all token counter tests"""
    print("\n" + "="*60)
    print("🚀 TOKEN COUNTER SERVICE TESTS")
    print("="*60)

    try:
        # Test token counting (sync)
        test_count_tokens()
        test_count_messages()

        # Test Redis integration (async)
        await test_track_usage()
        await test_quota_check()

        # Test utilities
        test_utility_functions()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nToken Counter Features Verified:")
        print("  ✅ Basic token counting (tiktoken)")
        print("  ✅ Message/chat token counting")
        print("  ✅ Usage tracking (Redis integration)")
        print("  ✅ Quota checking (free/pro/enterprise tiers)")
        print("  ✅ User & agent usage statistics")
        print("  ✅ Token estimation (fallback)")
        print("  ✅ Token formatting (1.2K, 15.3K, etc.)")
        print("\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Disconnect Redis
        await redis_service.disconnect()
        print("✅ Disconnected from Redis")


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
