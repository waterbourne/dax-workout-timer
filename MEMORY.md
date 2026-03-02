# MEMORY.md - Long-Term Memory

## Email Policy (Critical)

**ONLY the main agent can send emails. Sub-agents (cron jobs) CANNOT email.**

### Rules
1. **Sender:** Use Apple Mail via `osascript` (sends from default Mail account)
2. **Always CC:** adityabhavnani@gmail.com on every email — no exceptions
3. **Recipients:**
   - Aditya: adityabhavnani@gmail.com
   - Natasha: Natasha.sant@gmail.com
4. **Who can email:** Main agent only (direct chat sessions)
5. **Who cannot email:** Sub-agents (Personal Trainer, Spirituality Guide, Tutor, Head Chef) — they use Telegram only

### Method
```bash
osascript -e 'tell application "Mail"
    set theMessage to make new outgoing message with properties {subject:"SUBJECT", content:"BODY", visible:false}
    tell theMessage
        make new to recipient at end of to recipients with properties {address:"TO_EMAIL"}
        make new cc recipient at end of cc recipients with properties {address:"adityabhavnani@gmail.com"}
        send
    end tell
end tell'
```

---

## Family Structure

| Person | Role | Notes |
|--------|------|-------|
| **Aditya** | Primary user | Daily workouts, meditation, deep work 6-10 AM |
| **Natasha** | Wife | Workouts Mon/Wed/Fri only, **BODYWEIGHT ONLY** (no equipment), work lunches |
| **Evaan** | Child, age 7 | Tutoring: Academic (7 AM), Philosophy/Arts (5:15 PM) |

**Household:** San Francisco, CA. Kids breakfast = waffles/pancakes. 3-4 home-cooked dinners/week, 3-4 order-in.

---

## Cron Schedule (Backup Reference)

If jobs disappear, recreate from `~/.openclaw/cron/jobs.json`:

| Time | Job | Purpose | Delivery |
|------|-----|---------|----------|
| 4:30 AM | Personal Trainer | Workouts (Aditya daily + Natasha Mon/Wed/Fri) | Telegram |
| 5:15 AM | Spirituality Guide | Meditation + Stoic reflection | Telegram |
| 7:00 AM | Tutor - Academic | Math/Science/English/Phonics (Evaan, age 7) | Telegram |
| 9:00 AM | Atelier Master | Daily painting missions, art instruction | Telegram |
| 5:15 PM | Tutor - Philosophy | History, world religions, big questions (Evaan) | Telegram |
| 7:00 PM | Head Chef | Dinner planning + shopping list | Telegram |

---

## Communication Preferences

| Channel | Use For |
|---------|---------|
| **Telegram** | Primary. All sub-agent deliveries, direct chat |
| **Apple Mail** | Only main agent can send. Always CC adityabhavnani@gmail.com |
| **TUI** | Secondary interface |

## Travel Awareness

Agents must check for upcoming travel and adjust accordingly:
- **Raju (Head Chef):** If traveling tomorrow → suggest road food, travel snacks, or prep
- **Calendar Monitor:** No departure alerts while traveling (use location context)
- **All agents:** Be aware user may be offline/unresponsive during trips

---

## Silent Verticals (No Proactive Contact)

These agents ONLY respond to their cron schedule or direct questions:
- **Spirituality Guide** — Uses The Way app (Henry Shukman), no action unless asked
- **Head Chef** — Only 7:00 PM cron or direct questions
- **Atelier Master** — Only 9:00 AM cron or direct questions

---

## Spirituality

- **App:** The Way by Henry Shukman
- **Practice:** Daily meditation, Stoic reflection
- **Approach:** Direct, calm, no fluff

---

## Sub-Agent Names

| Name | Role | Schedule | For |
|------|------|----------|-----|
| **Dax** | Personal Trainer | 4:30 AM | Workouts (Aditya daily, Natasha Mon/Wed/Fri) |
| **Guru** | Spirituality Guide | 5:15 AM | Morning contemplation, wisdom traditions |
| **Sol** | Tutor (Academic) | 7:00 AM | Evaan's math, science, English, phonics |
| **Balthazar** | Atelier Master | 9:00 AM | Daily painting missions, art instruction |
| **Atlas** | Tutor (Philosophy) | 5:15 PM | Evaan's history, stories, big questions |
| **Raju** | Head Chef | 7:00 PM | Dinner planning, shopping lists |

**How to use:** Address them by name for direct requests. *"Dax, give me a core workout"* or *"Raju, something with salmon."* or *"Balthazar, what's today's painting mission?"*

---

## Calendar & Departure Monitoring

**Active monitoring:** Every 15 minutes via cron job

**Data source:** Bhavnani fam cal iCal feed (bypasses Apple Calendar sync issues)
- URL: `calendar.google.com/calendar/ical/on9f1k6ou2052pvqhlahg0ogus@group.calendar.google.com/...`
- Config: `calendar_config.yaml`

**What I do:**
- Fetch iCal feed and parse ALL events including recurring (RRULE)
- Calculate recurring instances (WEEKLY, BYDAY=WE, etc.)
- Look up directions/travel time to locations
- Calculate "leave by" time (event start - drive time - 15 min buffer)
- Send Telegram alert if leave time is within 60 minutes

**Format:**
```
🚗 Leave soon: [Event] at [Location]
Start: 3:00 PM | Drive: 45 min
⏰ LEAVE BY: 2:00 PM
```

**Default departure location:** San Francisco, CA

---

## Notes
- This policy is enforced in TOOLS.md (reference) and USER.md (preference)
- Sub-agents are configured for Telegram-only delivery with explicit channel=telegram in their cron jobs
- Calendar: "Bhavnani fam cal" = primary family planning calendar (Apple Calendar syncs Google)

## Daily Memory Logging Rule (Added Feb 24, 2026)
**Enforcement:** HEARTBEAT.md Section 10
- Check after 8:00 PM: Does `memory/YYYY-MM-DD.md` exist?
- If missing → CREATE IT immediately before ending session
- If missing after 11:00 PM → CREATE IT + note the delay

**What gets logged:** Agent deliveries, user interactions, system changes, errors/lessons, travel changes, significant conversations

---

## System Configuration Changes

### Heartbeat Interval Optimization (Feb 23, 2026)
**Change:** Reduce heartbeat frequency to preserve resources
- **Phase 1:** 45-minute intervals (starting today)
- **Phase 2:** 60-minute intervals (after 1-week validation)
- **Review Date:** March 2, 2026
- **Metrics to Track:**
  - Response latency
  - Missed alerts or delayed notifications
  - Resource usage patterns
  - User satisfaction with responsiveness
- **Rollback Trigger:** If any critical alerts missed or latency >5 min

**Implementation:** Gateway config patch required (user to execute)

---

## Cron Job Delivery Fixes (Feb 23, 2026)

**Issue:** Multiple agents (Sol, Atlas, Dax, Guru) failing with "Action send requires a target" or timeouts.

**Root Cause:** Sub-agents not explicitly calling message tool with proper target parameters.

**Fix Applied:**
- Updated all agent cron jobs with explicit delivery instructions
- Added CRITICAL DELIVERY section to each prompt specifying:
  - action: send
  - channel: telegram
  - target: 8584092724
- Reduced timeouts: Sol 180s→120s, others 90s
- Added "SEND IMMEDIATELY" directive to prevent waiting

**Agents Updated:**
- Sol (Academic Tutor) — 5 consecutive errors resolved
- Atlas (Philosophy Tutor) — 5 consecutive errors resolved  
- Dax (Personal Trainer) — 3 consecutive errors resolved
- Guru (Spirituality Guide) — timeout issue resolved

**Raju (Head Chef) — CRITICAL FIX:**
- **Feb 23, 10:30 PM:** Discovered Raju's cron job was MISSING entirely
- User returned from travel Feb 22, but cron job never re-created
- **Action:** Created new Raju cron job (7:00 PM daily) with proper delivery config
- Status: ✅ Active and ready for tomorrow

**Verification:** Sol manually spawned at 7:30 AM to test delivery.

---

## Lessons Learned (Continuous Improvement)

### February 2026 — Model Configuration & Delivery Reliability

**Anthropic Model Validation — Pre-Flight Checks Required (Feb 26, 2026)**
- **Bug:** Calendar Monitor and other cron jobs failing with HTTP 404 for `claude-3-opus-20240229`
- **Root Cause:** Model ID invalid or account lacks access; no validation before deployment
- **Impact:** ~800k tokens wasted on failed runs, zero output delivered
- **Fix:** All jobs migrated to `moonshot/kimi-k2.5` 
- **Rule:** ALWAYS validate model availability before cron deployment; `openclaw models list <provider>` is your friend
- **Prevention:** Add model validation step to AGENTS.md cron creation checklist

**Multi-Agent Delivery Failures — Pattern Analysis (Feb 27, 2026)**
- **Bug:** Multiple agents (Dax, Sol, Balthazar, Atlas, Raju) failing with different error types:
  - "Unsupported channel: telegram" 
  - "cron announce delivery failed"
  - "cron: job execution timed out"
- **Root Cause:** Mixed issues - delivery layer instability + insufficient timeouts for deep-reasoning agents
- **Pattern:** Balthazar (150s) and Atlas (180s) hitting timeout despite 180s limit - deep reasoning + delivery exceeds timeout
- **Fix Needed:** 
  1. Increase timeouts: Balthazar 150s→200s, Error Review 120s→180s
  2. Investigate Telegram delivery channel reliability
- **Rule:** Content generation + delivery must fit within timeout; add 30s buffer for delivery layer

### February 2026 — Calendar & Delivery Reliability

**Departure Alert Acknowledgments — Persistence Matters (Feb 25, 2026)**
- **Bug:** User acknowledged alert with 👍 at 2:36 PM, but received 5 more alerts through 3:34 PM
- **Root Cause:** `departure-alerts.json` wasn't being read/written properly between cron runs (stale data from Feb 18)
- **Fix:** Atomic file operations + unique alert IDs (event + date combo) + fail-safe behavior (skip alert if state unclear)
- **Rule:** When a user acknowledges something, that acknowledgment MUST persist and be respected — persistence failures are user experience failures

**Calendar Parsing — The Hard Way**
- RRULE validation is non-negotiable: BYDAY, UNTIL, EXDATE, and especially DTSTART must be validated
- **Critical rule:** Before sending ANY departure alert, verify DTSTART date == TODAY
- Future-date alerts (e.g., March 5 event alerted on Feb 18) are worse than no alert at all
- Event conflation (mixing name from one event with location from another) is data corruption — validate name+location+datetime match

**Search Strategy — Simple > Clever**
- Use the user's exact search terms first — don't over-engineer
- Cast a wide net (30+ days) before filtering
- Show raw results, then refine — don't hide potentially relevant matches

**Timeouts — Content Generation Takes Time**
- Sol (Academic Tutor): 90s → 180s timeout (lesson generation + delivery needs time)
- Raju (Head Chef): 90s → 120s timeout (meal planning + travel checks add complexity)
- When adding new logic (travel checks, cross-references), account for increased execution time

**Telegram Delivery — Intermittent, Not Broken**
- Delivery failures throughout Feb 19 were transient API issues, not agent logic errors
- Pattern: 2-hour stability windows followed by brief failures — classic rate limiting or connectivity
- Bob's recovery confirmed: Some agents fail while others succeed, indicating intermittent capacity, not systematic failure
- **Action:** Monitor for sustained patterns before declaring crisis; most "crises" resolve within hours
