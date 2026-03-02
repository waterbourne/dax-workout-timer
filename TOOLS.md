# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

### Email (Apple Mail)

**Method:** Use AppleScript + Mail app via `osascript`
- This sends from your default Mail account (iCloud/Gmail as configured)
- Uses whatever account is active in Apple Mail

**Command pattern:**
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

**Recipients:**
- **Aditya:** adityabhavnani@gmail.com (ALWAYS CC on every email)
- **Natasha:** Natasha.sant@gmail.com

**Rule:** ALWAYS CC adityabhavnani@gmail.com on every email sent. No exceptions.

### Departure Alerts (Calendar Monitor)

**Tracking:** memory/departure-alerts.json

**How it works:**
- Calendar Monitor checks for events within 4 hours
- Sends Telegram alert when "leave by" time approaches
- If user reacts with 👍 ✅ 👀 etc., alert is marked acknowledged
- NO follow-up alerts sent for acknowledged events

**Alert Format:**
```
🚗 Leave soon: [Event] at [Location]
Start: 3:00 PM | Drive: 45 min
⏰ LEAVE BY: 2:00 PM

React with 👍 if you got this — no more alerts for this event.
```

**Files:**
- `memory/departure-alerts.json` — tracks sent & acknowledged alerts

**CRITICAL: Acknowledgment Persistence (Fixed Feb 25, 2026)**
- Calendar Monitor MUST read `departure-alerts.json` at START of each run
- Acknowledged alerts (`noMoreAlerts: true`) MUST be respected for 24 hours
- File writes MUST be atomic (write temp → rename) to prevent corruption
- Each alert entry needs unique ID combining event name + date (not just event name)
- If acknowledgment check fails: Log error, skip alert (fail-safe: don't spam user)
