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
| **Natasha** | Wife | Workouts Mon/Wed/Fri only, work lunches |
| **Evaan** | Child, age 7 | Tutoring: Academic (7 AM), Philosophy/Arts (5:15 PM) |

**Household:** San Francisco, CA. Kids breakfast = waffles/pancakes. 3-4 home-cooked dinners/week, 3-4 order-in.

---

## Cron Schedule (Backup Reference)

If jobs disappear, recreate from `~/.openclaw/cron/jobs.json`:

| Time | Job | Purpose | Delivery |
|------|-----|---------|----------|
| 4:30 AM | Personal Trainer | Workouts (Aditya daily + Natasha Mon/Wed/Fri) | Telegram |
| 6:00 AM | Spirituality Guide | Meditation + Stoic reflection | Telegram |
| 7:00 AM | Tutor - Academic | Math/Science/English/Phonics (Evaan, age 7) | Telegram |
| 5:15 PM | Tutor - Philosophy | History, world religions, big questions (Evaan) | Telegram |
| 7:30 PM | Head Chef | Dinner planning + shopping list | Telegram |

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
- **Head Chef** — Only 7:30 PM cron or direct questions

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
| **Guru** | Spirituality Guide | 6:00 AM | Morning contemplation, wisdom traditions |
| **Sol** | Tutor (Academic) | 7:00 AM | Evaan's math, science, English, phonics |
| **Atlas** | Tutor (Philosophy) | 5:15 PM | Evaan's history, stories, big questions |
| **Raju** | Head Chef | 7:30 PM | Dinner planning, shopping lists |

**How to use:** Address them by name for direct requests. *"Dax, give me a core workout"* or *"Raju, something with salmon."*

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
