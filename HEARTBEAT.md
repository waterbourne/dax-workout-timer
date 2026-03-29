# HEARTBEAT.md

## Policy Change (March 23, 2026)
**NO MORE SPAM.**

Failure Monitor and System Debugger limited to **once daily at 9:00 AM**. 
Heartbeats only alert on CRITICAL issues (delivery queue backing up, all channels dead, agents stuck >30 min).

If everything's fine → `HEARTBEAT_OK` (silent).

---

## When to Alert (Revised)

**🚨 CRITICAL ONLY (Immediate Telegram + iMessage):**
- Delivery queue backing up (>10 messages)
- All delivery channels failing
- Agent stuck in execution_lock > 30 minutes
- Dead letter queue has entries

**⚠️ WARNING (Log to error-log.md only, NO message):**
- Individual agent failures (System Debugger covers this daily)
- Queue depth > 5
- Delivery success rate < 95%
- Stale health data

**ℹ️ INFO (Don't log):**
- Routine checks
- Agent successes
- Expected timeouts

---

## Daily Checks (Rotate Through — Silent Unless Critical)

### 1. Orchestrator Health
**Frequency:** Every heartbeat, but **only alert if CRITICAL**
- Read `orchestrator/state.json` — user state, travel mode
- Read `shared/agent-registry.json` — agent health
- Read `orchestrator/delivery-queue.json` — queue depth

**CRITICAL alert if:**
- Queue depth > 10
- All delivery channels failing
- Agent stuck > 30 min

**Otherwise:** HEARTBEAT_OK

### 2. Daily Memory Log
**Frequency:** Every heartbeat after 8:00 PM
- Check if `memory/YYYY-MM-DD.md` exists
- If missing AND time > 8:00 PM → CREATE IT
- If missing AND time > 11:00 PM → CREATE IT + note delay

**What to log:** Agent deliveries, user requests, errors, system changes

**Rule:** Create before ending session. No alerts for this.

---

## Agent Monitoring (Handled by System Debugger @ 9:00 AM Daily)

**Failure Monitor:** Runs once daily at 9:00 AM (was every 30 min)
**System Debugger:** Runs once daily at 10:00 AM (unchanged)

Both report via Telegram with a single summary message.

---

## Silent Verticals

- **Spirituality:** No action unless asked (The Way app)
- **Head Chef:** Only 7:00 PM cron or direct questions
- **Failure Monitor:** Once daily @ 9 AM, not every 30 min
- **System Debugger:** Once daily @ 10 AM

---

## Daily Memory Log Format

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

---

## Summary

| Component | Old Frequency | New Frequency | Delivery |
|-----------|---------------|---------------|----------|
| Heartbeat | Every 30 min | Every 30 min | Silent unless CRITICAL |
| Failure Monitor | Every 30 min | Daily @ 9 AM | Single summary message |
| System Debugger | Daily @ 10 AM | Daily @ 10 AM | Single summary message |

**Result:** You get ~3 messages in the morning (Dax, Guru, Morning Briefing) + 2 diagnostic summaries (9 AM, 10 AM). No more spam.
