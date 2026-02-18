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

---

## Review Template (End of Day)

At end of each day, review this log and:
1. **Patterns** — Are there recurring error types?
2. **Root causes** — Systemic issues or one-offs?
3. **File updates** — What rules need adding/updating?
4. **Research needed** — Any errors needing deeper investigation?

Update MEMORY.md with distilled lessons.
