# QUEUE.md — Work Queue

_Single source of truth for all work. One entry per significant task. No orphaned projects._

---

## 🔴 BLOCKED

_Active work stalled, waiting on user or external dependency._

| ID | Task | Blocked Since | Blocker | Next Step |
|----|------|---------------|---------|-----------|
| — | — | — | — | — |

---

## 🟡 ACTIVE

_Currently being worked on. One human, one focus._

| ID | Task | Started | Due | Status |
|----|------|---------|-----|--------|
| QUEUE-002 | Study TARS architecture, extract adoption patterns | Mar 24 | Mar 24 | In progress |

---

## 🟢 UP NEXT

_Scoped, ready for autonomous pickup. All criteria met:_
- [ ] Brief exists with scope defined
- [ ] Next action is concrete (not "TBD")
- [ ] No blocking questions
- [ ] Autonomy Tier 1 or 2

| ID | Task | Autonomy Tier | Estimated Time | Dependencies |
|----|------|---------------|----------------|--------------|
| QUEUE-001 | Implement Harish Agent OS patterns | Tier 2 | 2-3 days | None |
| QUEUE-002 | Study TARS architecture docs | Tier 1 | 2 hours | QUEUE-001 |
| QUEUE-003 | Create skill modules directory | Tier 2 | 1 day | QUEUE-001 |

---

## 📋 BACKLOG

_Ideas and briefs that exist but aren't scoped yet._

| ID | Task | Rough Idea | Priority |
|----|------|------------|----------|
| — | — | — | — |

---

## ✅ DONE THIS WEEK

_Completed work. Auto-pruned after 7 days._

| ID | Task | Completed | Notes |
|----|------|-----------|-------|
| QUEUE-001 | Implement Harish Agent OS patterns | Mar 24 | QUEUE.md + vault/ + failure-tested rules |
| QUEUE-004 | LearnQuest design update (Pixel principles) | Mar 24 | Type scale, spacing tokens, touch targets, hierarchy, a11y |

---

## 📚 Reference

### Autonomy Framework

| Tier | Name | Rule | Examples |
|------|------|------|----------|
| 1 | Just Do It | Execute without asking | File operations, research, heartbeat checks |
| 2 | Do It, Then Report | Execute, then notify | Subagent spawns, config changes, scheduled deliveries |
| 3 | Propose First | Wait for approval | External comms, spending money, structural OS changes |

### Work Lifecycle

```
Backlog → Up Next → Active → Done
              ↑         |
              └──── Blocked ──┘
```

### ID Format
- `B-XXX` — Briefs (project definitions)
- `QUEUE-XXX` — Queue items (this file)
- `EXP-XXX` — Experiments
- `AGENT-XXX` — Agent-specific work

---

_Last updated: 2026-03-24 by main agent_
