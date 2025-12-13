# Token Management & Counting Documentation

**Complete guide to AI token counting, tracking, and quota management in NodeRush**

**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Token Counter Service](#token-counter-service)
3. [Usage Examples](#usage-examples)
4. [Quota Management](#quota-management)
5. [Integration with AI APIs](#integration-with-ai-apis)
6. [Testing](#testing)
7. [Best Practices](#best-practices)

---

## Overview

NodeRush uses **tiktoken** (OpenAI's tokenizer) to accurately count AI tokens for:
- **Billing**: Track costs per user/agent
- **Quotas**: Enforce free tier limits (50K tokens/day)
- **Analytics**: Usage statistics and trends
- **Optimization**: Identify high-usage patterns

### Why Accurate Token Counting?

❌ **Problem with estimation**: `len(text) / 4` is inaccurate
- Varies by language (English vs Chinese)
- Different tokenization rules per model
- Can undercount by 20-40%

✅ **Solution: tiktoken**
- Official OpenAI tokenizer
- Exact token counts
- Supports all GPT models
- Fast and reliable

---

## Token Counter Service

Located at: `backend/app/services/token_counter_service.py`

### Features

1. ✅ **Accurate counting** with tiktoken
2. ✅ **Multi-model support** (GPT-4, GPT-3.5, NVIDIA Nemotron)
3. ✅ **Chat format support** (messages with roles)
4. ✅ **Redis integration** (real-time tracking)
5. ✅ **Quota enforcement** (free/pro/enterprise tiers)
6. ✅ **Usage statistics** (daily, monthly, per-agent)
7. ✅ **Fallback estimation** (if tiktoken fails)

### API Reference

#### Count Tokens in Text

```python
from app.services.token_counter_service import token_counter

# Count tokens in simple text
text = "Hello, world!"
tokens = token_counter.count_tokens(text, model="gpt-4")
print(f"Tokens: {tokens}")  # Output: 4
```

#### Count Tokens in Chat Messages

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help?"}
]

tokens = token_counter.count_messages_tokens(messages, model="gpt-4")
print(f"Total tokens: {tokens}")  # Includes overhead
```

#### Track Token Usage

```python
await token_counter.track_usage(
    user_id="user_123",
    agent_id="agent_456",
    prompt_tokens=100,
    completion_tokens=50,
    model="gpt-4"
)
```

This stores in Redis:
- `tokens:user:user_123:day:2025-12-10` → 150 tokens
- `tokens:agent:agent_456:total` → 150 tokens
- `tokens:user:user_123:month:2025-12` → 150 tokens

#### Check Quota

```python
quota = await token_counter.check_quota(
    user_id="user_123",
    required_tokens=1000,
    tier="free"  # or "pro", "enterprise"
)

if quota["allowed"]:
    # Proceed with request
    pass
else:
    # Reject: quota exceeded
    raise HTTPException(
        status_code=402,
        detail=f"Daily quota exceeded. Used {quota['used_today']}/{quota['limit']}"
    )
```

Response:
```python
{
    "allowed": True,
    "used_today": 5000,
    "limit": 50000,
    "remaining": 45000,
    "required": 1000
}
```

#### Get Usage Statistics

```python
# User stats
stats = await token_counter.get_user_usage_stats("user_123")
print(stats)
# {
#     "today": {"total": 5000, "gpt-4": 3000, "gpt-3.5": 2000},
#     "month": {"total": 150000, "gpt-4": 100000, "gpt-3.5": 50000},
#     "breakdown": {...}
# }

# Agent stats
agent_stats = await token_counter.get_agent_usage_stats("agent_456")
print(agent_stats)
# {"total": 25000, "gpt-4": 25000}
```

---

## Usage Examples

### Example 1: AI API Call with Token Tracking

```python
from app.services.token_counter_service import token_counter

async def generate_ai_response(
    prompt: str,
    user_id: str,
    agent_id: str,
    model: str = "gpt-4"
):
    # 1. Count prompt tokens
    prompt_tokens = token_counter.count_tokens(prompt, model=model)

    # 2. Check quota before calling API
    quota = await token_counter.check_quota(
        user_id=user_id,
        required_tokens=prompt_tokens + 500,  # +500 estimated completion
        tier="free"
    )

    if not quota["allowed"]:
        raise HTTPException(
            status_code=402,
            detail=f"Daily quota exceeded. Used {quota['used_today']}/{quota['limit']}"
        )

    # 3. Call AI API
    response = await call_ai_api(prompt, model=model)

    # 4. Count completion tokens
    completion_tokens = token_counter.count_tokens(response, model=model)

    # 5. Track usage
    await token_counter.track_usage(
        user_id=user_id,
        agent_id=agent_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model=model
    )

    return response
```

### Example 2: Agent Generation with Token Tracking

```python
@router.post("/agents/generate")
async def generate_agent(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Count tokens in vibe prompt
    prompt_tokens = token_counter.count_tokens(request.vibe_prompt)

    # 2. Check quota
    quota = await token_counter.check_quota(
        user_id=str(current_user.id),
        required_tokens=prompt_tokens + 3000,  # Estimated generation tokens
        tier=current_user.subscription_tier
    )

    if not quota["allowed"]:
        raise QuotaExceededError(
            quota_type="AI tokens",
            limit=quota["limit"],
            current=quota["used_today"]
        )

    # 3. Generate agent (3-agent workflow)
    result = await three_agent_service.generate(request.vibe_prompt)

    # 4. Count completion tokens
    completion_tokens = (
        token_counter.count_tokens(result.get("architecture", "")) +
        token_counter.count_tokens(result.get("code", "")) +
        token_counter.count_tokens(result.get("review", ""))
    )

    # 5. Track usage
    await token_counter.track_usage(
        user_id=str(current_user.id),
        agent_id=str(result["agent_id"]),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model="nvidia/nemotron-nano-12b-v2-vl"
    )

    return result
```

### Example 3: Usage Dashboard Endpoint

```python
@router.get("/users/me/usage")
async def get_my_usage(
    current_user: User = Depends(get_current_user)
):
    """Get current user's token usage statistics"""

    # Get comprehensive stats
    stats = await token_counter.get_user_usage_stats(str(current_user.id))

    # Get quota info
    quota = await token_counter.check_quota(
        user_id=str(current_user.id),
        required_tokens=0,  # Just checking current status
        tier=current_user.subscription_tier
    )

    return {
        "user_id": str(current_user.id),
        "tier": current_user.subscription_tier,
        "usage": stats,
        "quota": {
            "daily_limit": quota["limit"],
            "used_today": quota["used_today"],
            "remaining": quota["remaining"],
            "percentage": (quota["used_today"] / quota["limit"]) * 100
        }
    }
```

---

## Quota Management

### Tier Limits

| Tier | Daily Limit | Monthly Limit | Cost |
|------|-------------|---------------|------|
| **Free** | 50,000 tokens | ~1.5M tokens | $0 |
| **Pro** | 500,000 tokens | ~15M tokens | $19/month |
| **Enterprise** | Unlimited | Unlimited | Custom |

### Quota Enforcement Flow

```
1. User makes API request
   ↓
2. Count prompt tokens (tiktoken)
   ↓
3. Check quota (Redis lookup)
   ↓
4. If quota exceeded → Reject (402 Payment Required)
   ↓
5. If quota OK → Call AI API
   ↓
6. Count completion tokens
   ↓
7. Track usage in Redis
   ↓
8. Return response to user
```

### Quota Reset

Quotas reset automatically:
- **Daily quota**: Resets at midnight UTC
- **Monthly quota**: Resets on 1st of each month
- **Redis TTL**: Auto-expiry handles cleanup

---

## Integration with AI APIs

### NVIDIA Nemotron Integration

```python
import httpx
from app.services.token_counter_service import token_counter

async def call_nemotron_api(prompt: str, user_id: str):
    # 1. Count prompt tokens
    prompt_tokens = token_counter.count_tokens(
        prompt,
        model="nvidia/nemotron-nano-12b-v2-vl"
    )

    # 2. Check quota
    quota = await token_counter.check_quota(
        user_id=user_id,
        required_tokens=prompt_tokens + 2000,
        tier="free"
    )

    if not quota["allowed"]:
        raise HTTPException(402, "Quota exceeded")

    # 3. Call API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

    result = response.json()

    # 4. Extract tokens from API response
    usage = result.get("usage", {})
    completion_tokens = usage.get("completion_tokens", 0)

    # Or count manually if not provided
    if completion_tokens == 0:
        completion_text = result["choices"][0]["message"]["content"]
        completion_tokens = token_counter.count_tokens(completion_text)

    # 5. Track usage
    await token_counter.track_usage(
        user_id=user_id,
        agent_id=None,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model="nvidia/nemotron-nano-12b-v2-vl"
    )

    return result
```

---

## Testing

### Run Token Counter Tests

```bash
cd backend
python test_token_counter.py
```

Tests verify:
- ✅ Token counting accuracy
- ✅ Message format counting
- ✅ Usage tracking (Redis)
- ✅ Quota checking
- ✅ Statistics retrieval
- ✅ Fallback estimation

### Manual Testing

```bash
# Start Python REPL
python

# Test token counting
from app.services.token_counter_service import token_counter

text = "Hello, world!"
tokens = token_counter.count_tokens(text)
print(f"Tokens: {tokens}")

# Test with GPT-4
tokens_gpt4 = token_counter.count_tokens(text, model="gpt-4")
print(f"GPT-4 tokens: {tokens_gpt4}")
```

---

## Best Practices

### 1. Always Check Quota Before API Calls

```python
# ✅ GOOD - Check quota first
quota = await token_counter.check_quota(user_id, required_tokens, tier)
if quota["allowed"]:
    response = await call_ai_api(prompt)

# ❌ BAD - Call API first, track after
response = await call_ai_api(prompt)  # May exceed quota
await token_counter.track_usage(...)
```

### 2. Track Both Prompt and Completion

```python
# ✅ GOOD - Track both
await token_counter.track_usage(
    prompt_tokens=100,
    completion_tokens=50
)

# ❌ BAD - Only track total
await token_counter.track_usage(
    prompt_tokens=150,
    completion_tokens=0
)
```

### 3. Use Model-Specific Counting

```python
# ✅ GOOD - Specify model
tokens = token_counter.count_tokens(text, model="gpt-4")

# ⚠️ OK - Use default
tokens = token_counter.count_tokens(text)  # Uses cl100k_base
```

### 4. Handle Quota Errors Gracefully

```python
try:
    quota = await token_counter.check_quota(...)
    if not quota["allowed"]:
        # Show user-friendly message
        remaining = quota["limit"] - quota["used_today"]
        reset_time = "midnight UTC"
        raise HTTPException(
            status_code=402,
            detail=f"Daily quota exceeded. {quota['remaining']} tokens remaining. Resets at {reset_time}."
        )
except Exception as e:
    # Fail open - allow request if quota check fails
    logger.error(f"Quota check failed: {e}")
```

### 5. Monitor Usage Trends

```python
# Get daily usage
stats = await token_counter.get_user_usage_stats(user_id)

# Alert if approaching limit
if stats["today"]["total"] > 45000:  # 90% of free tier
    # Send notification to user
    await send_quota_warning(user_id, stats)
```

---

## Additional Resources

- **Tiktoken Docs**: https://github.com/openai/tiktoken
- **Token Pricing**: https://openai.com/pricing
- **Redis Service**: See `REDIS_SERVICE.md`
- **Architecture**: See `ARCHITECTURE.md`

---

**Last Updated**: December 2025
**Version**: 1.0.0
