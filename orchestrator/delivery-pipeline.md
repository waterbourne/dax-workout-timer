# Delivery Pipeline with Retry Logic

**Version:** 2.0  
**Last Updated:** 2026-02-19  
**Status:** Active

---

## Overview

The delivery pipeline provides resilient, multi-channel message delivery with automatic fallback and retry logic. Agents no longer send messages directly—instead they submit to a queue that handles delivery orchestration.

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────────────────┐
│   Agent     │────▶│ Delivery     │────▶│ Channel Router                  │
│ Generates   │     │ Queue        │     │ ┌──────────┐ ┌──────────┐      │
│ Content     │     │ (orchestrator│     │ │Telegram  │ │iMessage  │      │
│             │     │/delivery-   │     │ │ Primary  │→│Fallback  │      │
└─────────────┘     │ queue.json)  │     │ └──────────┘ └──────────┘      │
                    └──────────────┘     └─────────────────────────────────┘
                                                  │
                                                  ▼
                    ┌──────────────┐     ┌─────────────────────────────────┐
                    │ Dead Letter  │◀────│ Retry Logic                     │
                    │ Queue        │     │ • Exponential backoff           │
                    │ (manual      │     │ • Channel fallback              │
                    │  review)     │     │ • Rate limit handling           │
                    └──────────────┘     └─────────────────────────────────┘
```

---

## Queue Submission Protocol

### For Agents

Instead of calling the `message` tool directly:

```yaml
# OLD WAY (Deprecated)
tool: message
action: send
channel: telegram
target: "8584092724"
message: "Your workout..."

# NEW WAY (Current)
# 1. Generate content
# 2. Add to orchestrator/delivery-queue.json "queue" array
# 3. Let orchestrator handle delivery
```

### Submission Format

```json
{
  "queue": [
    {
      "id": "del_dax_20260219_001",
      "agent": "dax",
      "agent_emoji": "💪",
      "content": "## 💪 Morning Workout...",
      "content_type": "markdown",
      "priority": "high",
      "channels": ["telegram", "imessage"],
      "target": "8584092724",
      "max_length": 4000,
      "submitted_at": "2026-02-19T04:30:15-08:00",
      "status": "pending",
      "attempts": 0,
      "scheduled_delivery": "2026-02-19T04:30:00-08:00",
      "context": {
        "user_state": "home",
        "quiet_hours": false
      }
    }
  ]
}
```

---

## Channel Configuration

### Telegram (Primary)

```yaml
priority: 1
enabled: true
limits:
  message_length: 4000 characters
  messages_per_minute: 10
  messages_per_hour: 50
  burst_limit: 5
config:
  target: "8584092724"
  timeout: 30 seconds
retry_policy:
  max_retries: 3
  backoff: exponential [1s, 2s, 4s]
  on_rate_limit: wait and retry with longer backoff
  on_timeout: retry up to max_retries
  on_permanent_error: fallback to iMessage
```

### iMessage (Fallback)

```yaml
priority: 2
enabled: true
limits:
  message_length: 10000 characters (effectively unlimited)
  messages_per_minute: 20
  messages_per_hour: 100
config:
  target: "+1415XXXXXXX"  # Configure with actual number
  timeout: 30 seconds
retry_policy:
  max_retries: 2
  backoff: linear [2s, 4s]
  on_timeout: retry once
  on_failure: queue to dead letter
```

### WhatsApp (Backup - Not Configured)

```yaml
priority: 3
enabled: false
limits:
  message_length: 4096
note: "Configure gateway channels.whatsapp to enable"
```

---

## Retry Logic

### Exponential Backoff

```python
def get_retry_delay(attempt, backoff_type="exponential"):
    """
    attempt: 0-indexed retry attempt
    backoff_type: "exponential" or "linear"
    """
    if backoff_type == "exponential":
        return min(2 ** attempt, 60)  # Cap at 60 seconds
    elif backoff_type == "linear":
        return (attempt + 1) * 2
```

### Retry Decision Matrix

| Error Type | Retry | Backoff | Max Retries | Fallback |
|------------|-------|---------|-------------|----------|
| Timeout | Yes | Exponential | 3 | After retries |
| Rate Limit | Yes | Exponential ×2 | 5 | After retries |
| Network Error | Yes | Exponential | 3 | After retries |
| Authentication | No | - | 0 | Immediate |
| Invalid Target | No | - | 0 | Immediate |
| Message Too Long | No | - | 0 | Chunk or fallback |

### Fallback Sequence

```
Attempt Telegram (3 retries with exponential backoff)
    ↓ (if all fail)
Attempt iMessage (2 retries with linear backoff)
    ↓ (if all fail)
Queue to Dead Letter + Alert Admin
```

---

## Rate Limiting

### Per-Channel Limits

```json
{
  "rate_limiting": {
    "telegram": {
      "messages_per_minute": 10,
      "messages_per_hour": 50,
      "current_minute_count": 0,
      "current_hour_count": 0,
      "last_reset_minute": "2026-02-19T08:00:00-08:00",
      "last_reset_hour": "2026-02-19T08:00:00-08:00"
    }
  }
}
```

### Rate Limit Handling

1. **Detection:** Monitor response for rate limit errors (HTTP 429)
2. **Backoff:** Wait with exponential backoff starting at 2 seconds
3. **Retry:** Attempt delivery again
4. **Fallback:** If rate limit persists, switch to fallback channel
5. **Logging:** Log rate limit events for pattern analysis

---

## Dead Letter Queue

### Purpose

Messages that fail delivery on all channels are queued here for manual review.

### Configuration

```json
{
  "dead_letter_queue": {
    "enabled": true,
    "max_size": 100,
    "retention_hours": 168,
    "alert_threshold": 1,
    "alert_channels": ["telegram", "imessage"]
  }
}
```

### Entry Format

```json
{
  "id": "del_dax_20260219_001",
  "agent": "dax",
  "content": "...",
  "failed_at": "2026-02-19T04:35:00-08:00",
  "failures": [
    {
      "channel": "telegram",
      "error": "Rate limit exceeded",
      "attempts": 5
    },
    {
      "channel": "imessage",
      "error": "Device unreachable",
      "attempts": 2
    }
  ],
  "manual_review_required": true
}
```

### Alerting

When a message enters the dead letter queue:
1. Log to error-log.md
2. Send Telegram alert: "🚨 Delivery failed for Dax message. Check dead letter queue."
3. If Telegram fails, try iMessage
4. Update dashboard with dead letter count

---

## Routing Logic

### Default Routing

```yaml
routing:
  default_channel: telegram
  fallback_sequence: [telegram, imessage]
```

### Message Size Routing

```yaml
oversized_messages:
  threshold: 4000
  strategy: fallback_to_imessage
  chunk_if_no_alternative: true
  chunk_size: 3800
  chunk_separator: "\n\n---\n\n(continued)"
```

### Quiet Hours

```yaml
quiet_hours:
  enabled: true
  start: "22:00"
  end: "06:00"
  action: queue_until_end
  exceptions:
    - critical_alerts
    - departure_alerts
```

### Travel Mode

```yaml
travel_mode:
  enabled: true
  prefer_imessage_when_traveling: false
  reduce_frequency: true
```

---

## Agent Implementation Guide

### Step 1: Read User State

```javascript
// Always check user state before generating
const userState = read("orchestrator/state.json");
const isTraveling = userState.user_state.travel.status === "traveling";
const quietHours = isQuietHours();
```

### Step 2: Generate Content

```javascript
// Generate your content as normal
const content = generateWorkout(...);
```

### Step 3: Submit to Queue

```javascript
// Add to queue instead of sending directly
const deliveryEntry = {
  id: `del_${agent}_${timestamp}`,
  agent: "dax",
  content: content,
  priority: "high",
  channels: ["telegram", "imessage"],
  submitted_at: new Date().toISOString(),
  status: "pending"
};

addToDeliveryQueue(deliveryEntry);
```

### Step 4: Update Agent Registry

```javascript
// Record completion
updateAgentRegistry(agent, {
  last_run: timestamp,
  status: "success"
});
```

### Step 5: Do Not Retry

**IMPORTANT:** Do not implement your own retry logic. The pipeline handles all retries and fallbacks.

---

## Monitoring

### Metrics Tracked

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| queue_depth | Messages waiting | >5 warning, >10 critical |
| delivery_success_rate | % successful | <95% warning, <90% critical |
| fallback_usage_rate | % using fallback | >10% warning |
| avg_delivery_time | Time to deliver | >10s warning |
| dead_letter_count | Failed messages | >0 alert |

### Health Checks

```yaml
health_checks:
  interval: 60 seconds
  checks:
    - queue_depth
    - channel_connectivity
    - rate_limit_status
    - dead_letter_queue_size
```

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| Timeout | Slow generation | Increase timeout in agent-registry |
| Rate Limit | Too many messages | Backoff and retry |
| Auth Failed | Token expired | Alert admin |
| Invalid Target | Wrong ID | Alert admin |
| Network Error | Connectivity | Retry with backoff |

### Logging

All delivery events logged to:
- `orchestrator/delivery-queue.json` (current state)
- `memory/error-log.md` (errors)
- `shared/delivery-log.json` (history)

---

## Testing

### Test Scenarios

1. **Normal delivery:** Submit message, verify Telegram delivery
2. **Telegram failure:** Simulate Telegram failure, verify iMessage fallback
3. **Rate limiting:** Send 15 messages quickly, verify proper backoff
4. **Oversized message:** Send 5000 char message, verify iMessage routing
5. **Quiet hours:** Submit during 23:00, verify queueing

### Test Commands

```bash
# Check queue status
cat orchestrator/delivery-queue.json | jq '.queue'

# Check dead letter queue
cat orchestrator/delivery-queue.json | jq '.dead_letter_queue'

# View delivery statistics
cat orchestrator/delivery-queue.json | jq '.statistics'
```

---

## Migration from Direct Delivery

### Current (Direct)

```javascript
// Agent generates and sends directly
tool: message
action: send
channel: telegram
target: "8584092724"
message: content
```

### Target (Queue-Based)

```javascript
// Agent generates and submits to queue
const entry = {
  agent: "dax",
  content: content,
  priority: "high",
  channels: ["telegram", "imessage"]
};
addToDeliveryQueue(entry);
```

### Backward Compatibility

During migration:
1. Agents can still use direct delivery
2. Queue-based delivery is preferred
3. Both methods work simultaneously
4. Eventually deprecate direct delivery

---

## Configuration Files

| File | Purpose |
|------|---------|
| `orchestrator/delivery-queue.json` | Queue state and configuration |
| `orchestrator/channel-router.yaml` | Routing rules (if separated) |
| `shared/delivery-log.json` | Delivery history |

---

**See Also:**
- `ARCHITECTURE.md` - System architecture
- `AGENTS.md` - Agent operational rules
- `shared/agent-registry.json` - Agent configurations
