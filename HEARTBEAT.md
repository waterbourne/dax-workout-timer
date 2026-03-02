# HEARTBEAT.md

## Daily Checks (Rotate through these)

### 1. Orchestrator Health (NEW - High Priority)
**Frequency:** Every heartbeat
- [ ] Read `orchestrator/state.json` - Check user state, travel mode
- [ ] Read `shared/agent-registry.json` - Verify all agents healthy
- [ ] Read `orchestrator/delivery-queue.json` - Check queue depth
- [ ] Look for alerts in `state.json` system_state.health.alerts

**Alert if:**
- Queue depth > 5
- Any agent shows consecutive_errors > 2
- System health != "healthy"
- Delivery channel status != "healthy"

### 2. Agent Coordination Status (NEW)
**Frequency:** Every 2-3 heartbeats
- [ ] Check `dependencies` in state.json
- [ ] Verify Guru completes before Sol runs
- [ ] Check execution_lock - should be unlocked when idle
- [ ] Look for stuck agents (running > timeout)

### 3. Cron Health Check
**Frequency:** Daily
- Run: `openclaw cron list | grep -E "(Dax|Guru|Sol|Atlas|Raju)"`
- Verify: 5 jobs configured (Raju may be disabled for travel)
- Check: Timeouts updated (180s for Sol, Dax, Raju)
- Check: Schedules updated (Guru 5:15 AM, Raju 7:00 PM)

### 4. Delivery Pipeline Health (NEW)
**Frequency:** Daily
- [ ] Check `orchestrator/delivery-queue.json` statistics
- [ ] Verify delivery success rate > 95%
- [ ] Check dead letter queue - should be empty
- [ ] Verify fallback channel (iMessage) healthy

### 5. Context Sharing (NEW)
**Frequency:** Every 2-3 heartbeats
- [ ] Read `shared/context-cache.json`
- [ ] Check recent topics from each agent
- [ ] Look for pending cross-agent references
- [ ] Verify no stale entries (>30 days)

### 6. Calendar Check
**Frequency:** Every heartbeat
- Check Bhavnani fam cal for upcoming events
- Note any prep needed
- Update `orchestrator/state.json` if travel detected

### 7. Travel Mode Check (NEW)
**Frequency:** Every heartbeat
- Read `user_state.travel` in state.json
- If status changed → notify relevant agents
- Verify Raju disabled when traveling
- Verify Dax in travel mode if departing soon

### 8. Silent Verticals
- Spirituality: No action unless asked (The Way app)
- Head Chef: Only responds to 7:00 PM cron or direct questions (or travel mode)

### 9. Error Review Check
**Frequency:** Daily
- Read: `memory/error-log.md`
- Read: `memory/bob-audit-log.md`
- Review any errors from today
- Identify patterns and root causes
- Update AGENTS.md/TOOLS.md with new rules if needed

### 10. Daily Memory Log (NEW - High Priority)
**Frequency:** Every heartbeat after 8:00 PM
- [ ] Check if `memory/YYYY-MM-DD.md` exists for today's date
- [ ] If missing AND time is after 8:00 PM → CREATE IT
- [ ] If missing AND time is after 11:00 PM → CREATE IT + note the delay

**What to log:**
- Agent deliveries (Dax, Guru, Sol, Atlas, Raju, etc.)
- User requests and decisions made
- Errors encountered and fixes applied
- System changes (cron updates, config changes)
- Significant conversations or insights
- Travel mode changes, calendar events

**Format:**
```markdown
## YYYY-MM-DD - Day Name

### Morning Agents
- Dax: [workout focus]
- Guru: [theme/question]
- Sol: [topics covered]

### User Interactions
- [Time]: [What was requested] → [What was done]

### System Changes
- [What changed and why]

### Errors/Lessons
- [What went wrong] → [How fixed]

### Notes
- [Anything else worth remembering]
```

**Rule:** If the file doesn't exist by 8 PM, I MUST create it before ending the session. No exceptions.

---

## When to Alert

**🚨 CRITICAL (Immediate Telegram + iMessage):**
- Delivery queue backing up (>10 messages)
- All delivery channels failing
- Agent stuck in execution_lock > 10 minutes
- Dead letter queue has entries

**⚠️ WARNING (Telegram, respect quiet hours):**
- Queue depth > 5
- Agent consecutive errors > 2
- Delivery success rate < 95%
- Fallback channel usage > 10%

**ℹ️ INFO (Log only):**
- Individual agent timeout (retries will handle)
- Rate limiting events (expected occasionally)
- Context cache rotation

---

## New Orchestration State Tracking

Track these in `memory/heartbeat-state.json`:

```json
{
  "lastChecks": {
    "orchestrator": 1703275200,
    "agent_health": 1703275200,
    "delivery_queue": 1703275200,
    "context_cache": 1703275200,
    "travel_mode": 1703275200,
    "email": 1703275200,
    "calendar": 1703260800,
    "weather": null
  },
  "orchestratorStatus": {
    "systemHealthy": true,
    "queueDepth": 0,
    "agentsWithIssues": [],
    "lastAlert": null
  }
}
```

---

## Migration Checklist

**Phase 1 (Feb 19-22):**
- [x] ARCHITECTURE.md created
- [x] AGENTS.md v2.0 created
- [x] orchestrator/ state.json, schedule.yaml created
- [x] shared/ agent-registry.json, context-cache.json created
- [ ] HEARTBEAT.md updated with orchestration checks

**Phase 2 (Feb 22-Mar 1):**
- [ ] Schedule Manager implemented
- [ ] Sequential execution working
- [ ] Sol waits for Guru
- [ ] Cron schedules updated in system

**Phase 3 (Mar 2-11):**
- [ ] Queue processor running
- [ ] Telegram → iMessage fallback working
- [ ] Dead letter queue monitored
- [ ] Delivery success rate > 99%

**Phase 4 (Mar 12-21):**
- [ ] Context sharing active
- [ ] Travel mode auto-detection
- [ ] Work hours awareness
- [ ] All metrics at target
