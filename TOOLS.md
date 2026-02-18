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
