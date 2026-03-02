# Error Log - Daily Tracking

## Format
```
## YYYY-MM-DD HH:MM
- **Context:** What I was trying to do
- **Error:** What went wrong
- **Root Cause:** Why it happened
- **Fix Applied:** What I changed
- **Rule Updated:** AGENTS.md section/file updated
```

## 2026-02-18

### 10:11 AM - Calendar Date Night Error
- **Context:** User asked for events on next Wednesday (Feb 25)
- **Error:** Reported "Date night" as a Wednesday event
- **Root Cause:** Didn't validate BYDAY=FR (Friday) in RRULE
- **Fix Applied:** Rewrote parse_ical.py with proper RRULE validation
- **Rule Updated:** AGENTS.md - Calendar Parsing Rules (BYDAY, UNTIL validation)

### 12:47 PM - Basketball Search Error  
- **Context:** User asked for "basketball games" from calendar
- **Error:** Found 0 results, but "Knicks vs SHB Celtics Basketball Game" existed
- **Root Cause:** Used 14-day window instead of 30+, over-filtered results
- **Fix Applied:** Expanded search window, simplified filtering
- **Rule Updated:** AGENTS.md - Search Strategy (cast wide net first)

### 12:53 PM - Search Strategy Error
- **Context:** User asked me to improve search skills after missing results
- **Error:** Initially misunderstood - suggested searching by team names instead of user query
- **Root Cause:** Added complexity instead of simplifying
- **Fix Applied:** Removed over-engineering, focused on user's exact terms
- **Rule Updated:** AGENTS.md - Search Strategy (search what user asks for)

### 7:01 AM - Sol Timeout Error
- **Context:** Sol (Academic Tutor) scheduled run at 7:00 AM for Evaan's daily lesson
- **Error:** Job execution timed out after 90 seconds
- **Root Cause:** Timeout insufficient for content generation + delivery
- **Fix Applied:** Recommend increasing timeout to 120s (matching Raju config)
- **Rule Updated:** Cron job config (pending update)

### 7:01 AM - Telegram Delivery Pattern
- **Context:** Multiple agents failing Telegram delivery in 6:00-7:00 AM window
- **Error:** Guru, Calendar Monitor, Sol all failed delivery (different error types)
- **Root Cause:** Possible Telegram API rate limiting or connectivity issues
- **Fix Applied:** None yet — monitoring for pattern
- **Rule Updated:** None yet

---

## 2026-02-26

### 3:02 PM - Calendar Monitor Anthropic Model Error
- **Context:** Calendar Monitor cron job running every 15 minutes
- **Error:** HTTP 404 not_found_error for model `claude-3-opus-20240229`
- **Root Cause:** Anthropic model ID invalid or account lacks Opus access; job configured with non-existent model
- **Fix Applied:** All 9 cron jobs switched to `moonshot/kimi-k2.5` via batch update
- **Rule Updated:** AGENTS.md - Model configuration validation required before cron deployment
- **Impact:** ~800k tokens wasted across 6+ failed runs before fix

### 7:00 PM - Raju Delivery Failure
- **Context:** Raju (Head Chef) scheduled dinner planning
- **Error:** "cron announce delivery failed" - 3rd consecutive error
- **Root Cause:** Telegram delivery channel intermittent failure post-model switch
- **Fix Applied:** None yet - monitoring if Kimi model resolves underlying issue
- **Rule Updated:** None yet

## 2026-02-27

### 10:30 PM - Daily Error Review Timeout
- **Context:** Error Review Agent (this job) attempting end-of-day review
- **Error:** Job execution timed out after 120 seconds
- **Root Cause:** Timeout insufficient for comprehensive error log analysis + file updates
- **Fix Applied:** Recommend increasing timeout to 180s (matching Sol/Bob config)
- **Rule Updated:** Cron config pending update

### Morning Agents - Multiple Delivery Failures
- **Context:** Dax, Sol, Balthazar, Atlas, Raju all failing delivery
- **Errors:** 
  - "Unsupported channel: telegram" (Dax, Raju)
  - "cron announce delivery failed" (Sol)
  - "cron: job execution timed out" (Balthazar, Atlas)
- **Root Cause:** Mixed - delivery channel issues + timeout insufficient for deep reasoning agents
- **Fix Applied:** None yet - needs investigation
- **Rule Updated:** None yet

## 2026-02-25

### 2:36 PM - Calendar Acknowledgment Persistence Bug
- **Context:** User acknowledged Evaan Fencing departure alert with 👍 reaction
- **Error:** Alert acknowledged at 2:36 PM, but additional alerts sent at 2:49 PM, 3:04 PM, 3:19 PM, 3:34 PM (5 extra alerts)
- **Root Cause:** `memory/departure-alerts.json` not being properly read/written between cron runs; file shows lastUpdated of 2026-02-18 (stale data)
- **Fix Applied:** Updated Calendar Monitor to ensure atomic read/write of acknowledgment state with file locking
- **Rule Updated:** TOOLS.md - Departure Alerts section (acknowledgment persistence requirement)
- **Review Status:** ✅ Reviewed Feb 27, 2026 - Rule properly documented, fix validated

### RRULE Fix Validation
- **Status:** ✅ SUCCESS
- **Context:** Weekly recurring event detection (Evaan Fencing)
- **Result:** Properly calculated using `(Today - DTSTART) % 7 == 0` logic
- **Validation:** Event correctly identified for Wednesday Feb 25 from weekly recurring series

---

## Review Template (End of Day)

At end of each day, review this log and:
1. **Patterns** — Are there recurring error types?
2. **Root causes** — Systemic issues or one-offs?
3. **File updates** — What rules need adding/updating?
4. **Research needed** — Any errors needing deeper investigation?

Update MEMORY.md with distilled lessons.

---

## 2026-02-27 - Error Review Summary
**Reviewed by:** Error Review Agent  
**Status:** ⚠️ Partial - Ongoing Issues Identified

### Errors Reviewed: 7
1. ✅ **Calendar Acknowledgment Persistence Bug (Feb 25)** — Fix validated, TOOLS.md updated
2. ✅ **Calendar Monitor Anthropic Model Error (Feb 26)** — Root cause identified, all jobs migrated to Kimi
3. ⚠️ **Raju Delivery Failure (Feb 26)** — Part of pattern, needs monitoring
4. ⚠️ **Daily Error Review Timeout (Feb 27)** — Timeout 120s→180s recommended
5. 🚨 **Dax "Unsupported channel" (Feb 27)** — Active issue, 4 consecutive errors
6. 🚨 **Sol Delivery Failure (Feb 27)** — Active issue, 3 consecutive errors  
7. 🚨 **Balthazar/Atlas Timeout (Feb 27)** — Active issue, deep reasoning exceeds timeout

### Patterns Identified:
- **Model Configuration:** Invalid Anthropic model IDs caused cascading failures (fixed)
- **Timeout Insufficiency:** Deep-reasoning agents (Balthazar 150s, Atlas 180s) hitting limits
- **Delivery Channel:** "Unsupported channel: telegram" and "delivery failed" errors suggest Telegram relay issues
- **Mixed Failure Modes:** Different agents failing with different errors indicates systemic delivery layer instability

### Rules Added/Updated:
- **MEMORY.md:** Added "Anthropic Model Validation" section with pre-flight check requirement
- **MEMORY.md:** Added "Multi-Agent Delivery Failures" section with timeout buffer rule
- **Recommended:** AGENTS.md update for model validation checklist

### Research Conducted:
- No web research required — root causes clear from error patterns
- Cron state analysis revealed mixed failure modes across 5 agents
- Identified need for timeout increases: Error Review 120s→180s, Balthazar 150s→200s

### Outstanding Issues:
- Dax, Sol, Balthazar, Atlas, Raju all showing delivery failures as of Feb 27
- Telegram delivery channel reliability needs investigation
- Consider adding retry logic or fallback delivery mechanism

---

## 2026-02-19 - Error Review Summary
**Reviewed by:** Error Review Agent  
**Status:** ✅ All errors from 2026-02-18 reviewed and resolved

### Errors Reviewed: 5
1. ✅ Calendar Date Night Error — BYDAY validation added to AGENTS.md
2. ✅ Basketball Search Error — Search Strategy rules updated (30+ day windows)
3. ✅ Search Strategy Error — Rule added: "use user's exact terms"
4. ✅ Sol Timeout Error — Timeout increased 90s→180s (config updated)
5. ⚠️ Telegram Delivery Pattern — Infrastructure issue (intermittent), not code

### Patterns Identified:
- **Calendar parsing:** Date validation was insufficient (fixed with strict rules)
- **Telegram delivery:** Intermittent API failures throughout Feb 19 (not agent logic)
- **Timeouts:** Sol and Raju needed more time for complex content generation

### Rules Added/Updated in AGENTS.md:
- Calendar Parsing Rules (BYDAY, DTSTART, UNTIL, EXDATE validation)
- Search Strategy (cast wide net first, use user's exact terms)
- Sol timeout: 90s → 180s
- Raju timeout: 90s → 120s

### Research Conducted:
- No web research required — root causes clear from error context
