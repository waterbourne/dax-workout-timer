# Failure-Tested Rules

_Production incidents that became rules. Marked with 🔒 — never prune._

---

## Agent Delivery

### 🔒 CRITICAL: Only Main Agent Can Email
**Incident:** Sub-agents (cron jobs) attempting to send emails violated policy.  
**Rule:** ONLY the main agent can send emails. Sub-agents use Telegram only.  
**Enforcement:** USER.md + TOOLS.md + MEMORY.md all reference this rule.  
**Date:** Feb 2026

### 🔒 Email Must Always CC Aditya
**Incident:** Emails sent without CC to primary user.  
**Rule:** ALWAYS CC adityabhavnani@gmail.com on every email. No exceptions.  
**Method:** Apple Mail via `osascript`.  
**Date:** Feb 2026

---

## Calendar & Alerts

### 🔒 Departure Alert Date Validation
**Incident:** March 5 event alerted on Feb 18. DTSTART not validated.  
**Rule:** Before sending ANY departure alert, verify DTSTART date == TODAY.  
**Fail-safe:** If validation fails, skip alert (don't spam).  
**Date:** Feb 25, 2026

### 🔒 Acknowledgment Persistence
**Incident:** User acknowledged alert with 👍, but received 5 more alerts.  
**Root Cause:** `departure-alerts.json` not read properly between runs.  
**Fix:** Atomic file operations + unique alert IDs (event + date).  
**Rule:** When user acknowledges something, that acknowledgment MUST persist.  
**Date:** Feb 25, 2026

---

## Cron & Agent Health

### 🔒 Model Validation Required
**Incident:** Calendar Monitor failing with HTTP 404 for invalid model ID (`claude-3-opus-20240229`).  
**Impact:** ~800k tokens wasted, zero output.  
**Rule:** ALWAYS validate model availability before cron deployment.  
**Method:** `openclaw models list <provider>`  
**Fix:** Migrated to `moonshot/kimi-k2.5`.  
**Date:** Feb 26, 2026

### 🔒 Timeout Buffer for Delivery
**Incident:** Balthazar (150s) and Atlas (180s) hitting timeouts despite limits.  
**Root Cause:** Content generation + delivery > timeout.  
**Rule:** Add 30s buffer for delivery layer. Content gen must fit within (timeout - 30s).  
**Fix:** Balthazar 150s→200s, Atlas kept at 180s but monitored.  
**Date:** Feb 27, 2026

### 🔒 Agent Registry Updates
**Incident:** `agent-registry.json` shows stale data (last updated March 10, agents ran daily since).  
**Impact:** Health metrics unreliable, early warning signs missed.  
**Rule:** Agents MUST write completion status to registry after each run.  
**Status:** Under investigation.  
**Date:** March 24, 2026

---

## Memory & Context

### 🔒 Daily Memory File Required
**Incident:** Sessions ending without daily log created.  
**Rule:** If `memory/YYYY-MM-DD.md` doesn't exist by 8:00 PM, CREATE IT before ending session.  
**Enforcement:** HEARTBEAT.md Section 9.  
**Date:** Feb 24, 2026

### 🔒 Context Discipline
**Incident:** Full file reads wasting context budget.  
**Rule:** Use `head`, `grep`, `--limit` — never `cat` full files for a few lines.  
**Alert Thresholds:** >60% alert, >80% escalate.  
**Date:** Adopted from TARS architecture, March 2026

---

## Communication

### 🔒 Message Spacing
**Incident:** Heartbeat + Failure Monitor + multiple agents created noise (~62 messages/day).  
**Rule:** Failure Monitor limited to once daily at 9:00 AM. Heartbeats silent unless critical.  
**Target Volume:** ~5 messages/day.  
**Date:** March 23, 2026

### 🔒 No Filler
**Incident:** Excessive "Great question!" and "I'd be happy to help!" responses.  
**Rule:** Be genuinely helpful, not performatively helpful. Actions > filler words.  
**Source:** SOUL.md core principle.  
**Date:** Ongoing

---

## Knowledge Management

### 🔒 Research Staging Area
**Incident:** Research scattered across project folders, not searchable.  
**Rule:** ALL research goes to `outputs/research/` regardless of project.  
**Pipeline:** `outputs/research/` → vault ingest (nightly) → searchable knowledge.  
**Source:** TARS architecture, March 2026

### 🔒 Failure-Tested Rules Are Sacred
**Incident:** Temptation to prune "old" rules during cleanup.  
**Rule:** Rules marked with 🔒 exist because something broke in production. Never prune.  
**Source:** TARS architecture principle #4.  
**Date:** Adopted March 2026

---

_Last updated: 2026-03-24_
