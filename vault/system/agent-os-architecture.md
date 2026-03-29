# Agent OS Architecture

_Source: TARS (Harish's Agent System)  
Received: March 23, 2026  
Status: Reference Implementation_

---

## Overview

AI agent operating system built on OpenClaw, running on Mac Mini M1. One primary agent (TARS) coordinates specialized subagents, each owning a domain. System runs 24/7, communicates via Telegram, sends email, manages calendars, runs scheduled deliveries, and accumulates knowledge over time.

---

## Six Layers + Cross-Cutting Concerns

### Layer 1: Identity & Governance

**Core Files (loaded every session):**
| File | Purpose |
|------|---------|
| `SOUL.md` | Persona definition — communication style, humor, character |
| `IDENTITY.md` | Agent metadata — name, role, contact info |
| `AGENTS.md` | Operational kernel — startup sequence, config rules, daily memory protocol |
| `USER.md` | User profile — identity, timezone, relationships, routine |

**Key Design Decisions:**
- Persona (`SOUL.md`) separated from operations (`AGENTS.md`)
- Failure-tested rules (🔒) are sacred — never prune
- Each subagent gets its own `AGENTS.md`

---

### Layer 2: Memory, Preferences & Knowledge

#### 2A. Memory System (Three Tiers)

```
Daily Logs ──► MEMORY.md ──► Vector Search
(working)     (curated)      (semantic)
```

| Tier | Location | Horizon | Content |
|------|----------|---------|---------|
| Daily | `memory/YYYY-MM-DD.md` | 1-2 days | Everything — decisions, failures, context |
| Curated | `MEMORY.md` | 6+ months | Scheduling, priorities, operational decisions |
| Vector | SQLite + sqlite-vec | Unlimited | Semantic search across all memory |

**Rules:**
- Read today + yesterday on session start
- Create today's file immediately if missing
- Write immediately, don't batch
- Capture *why* X over Y — not just what happened
- Promote to MEMORY.md only facts with 6+ month relevance

#### 2B. Context Management

**Bootstrap Injection:** These files auto-loaded every session:
```
AGENTS.md, SOUL.md, USER.md, HEARTBEAT.md, MEMORY.md, 
TOOLS.md, IDENTITY.md, QUEUE.md
```

**Startup Sequence:**
1. Read IDENTITY.md + SOUL.md + USER.md
2. Read today + yesterday's daily memory
3. Create today's memory file if missing
4. Read RESUME.md if present (restore context, then delete)
5. Read QUEUE.md — check blocked items, pull next active task

**Context Budget:**
- >60% usage: alert
- >80% usage: escalate
- Use `head`, `grep`, `--limit` — never `cat` full files

#### 2C. Preferences

Taste data separated from identity:
```
data/preferences/
├── diet-preferences.md
├── entertainment-preferences.md
├── drink-preferences.md
├── learning-preferences.md
└── media-preferences.md
```

**Distinction:**
- User moves cities → `USER.md` changes
- User discovers they like sushi → preferences change

#### 2D. Knowledge System

Three compounding sources:

1. **Obsidian Vault** — ~1,880 notes across 8 domains, vector embeddings
2. **Oracle Research** — Deep research → `outputs/research/` → auto-ingested nightly
3. **Learning Briefs** — Weekly briefs from 40+ sources

**Knowledge Pipeline:**
```
Sources → Staging → Processing → Vault → Access
```

- Readwise → Inbox → vault-processor (Sun 5 AM) → Notes + embeddings
- Oracle → outputs/research/ → vault-ingest-research (nightly 2 AM)
- **Critical:** ALL research goes to `outputs/research/` — no project folders

---

### Layer 3: Work Management

#### 3A. Work Queue (QUEUE.md)

Five sections:
| Section | Purpose |
|---------|---------|
| **Blocked** | Active work stalled, waiting on user (gets Apple Reminder) |
| **Active** | Currently being worked on |
| **Up Next** | Scoped and ready for autonomous pickup |
| **Backlog** | Ideas/briefs exist but not scoped |
| **Done This Week** | Completed (auto-pruned after 7 days) |

**Lifecycle:**
```
Backlog → Up Next → Active → Done
              ↑         |
              └──── Blocked ──┘
```

**Up Next Readiness Criteria** (ALL must be true):
1. Brief exists with scope defined
2. Next action is concrete (not "TBD")
3. No blocking questions for user
4. Autonomy Tier 1 or 2

#### 3B. Briefs

Each significant work item gets:
```
dossiers/briefs/B-XXX.md
├── Problem statement
├── Proposed approach
├── Plan with sub-tasks
├── Autonomy tier assignments
└── Success criteria
```

#### 3C. Autonomy Framework

| Tier | Name | Rule | Examples |
|------|------|------|----------|
| 1 | Just Do It | Execute without asking | File ops, research, heartbeat checks |
| 2 | Do It, Then Report | Execute, then notify | Subagent spawns, config changes |
| 3 | Propose First | Wait for approval | External comms, spending, structural changes |

---

### Layer 4: Team & Delegation

#### 4A. Agent Roster

**Vertical Agents** (domain owners):
| Agent | Domain | Capabilities |
|-------|--------|--------------|
| Scout | Dining & Concierge | Restaurant DB (800+ entries), vibe data |
| Marquee | Entertainment & Media | Taste profiles, release tracking |
| Mise | Cooking & Meal Planning | Recipe DB, diet preferences |

**Horizontal Agents** (function owners):
| Agent | Function |
|-------|----------|
| Oracle | Research & Learning |
| Pixel | Design & Visual |
| Runner | Execution & Delivery |

**TARS** (Coordinator) — routes work, coordinates agents, interfaces with user.

#### 4B. Delegation Protocol

```
1. TARS identifies work belonging to subagent domain
2. Crafts task prompt with context
3. sessions_spawn creates isolated session
4. Agent executes and announces result
5. TARS reviews output and delivers (or iterates)
```

#### 4C. Vertical Agent Stack

Every domain agent follows this architecture:

```
PREFERENCE PROFILE
        ↓ match against
RECOMMENDATION CORPUS
        ↓ filter + score
PICKS
```

#### Autonomous Knowledge Loops

Agents detect and fill their own knowledge gaps:
```
Agent uses data → assesses sufficiency → flags gaps 
→ enrichment runs → data improves → next request succeeds
```

- Gap detection + public enrichment = Tier 1 (autonomous)
- New source addition = Tier 2 (log and notify)

---

### Layer 5: Capabilities (Tools + Skills)

#### 5A. Tools (Platform Primitives)

Fixed set from OpenClaw:
- `web_search`, `web_fetch` — information retrieval
- `browser` — Playwright automation
- `exec`, `process` — shell commands
- `memory_search`, `memory_get` — agent memory
- `cron` — scheduling
- `message` — channel delivery
- `image`, `tts` — media generation
- `sessions_spawn`, `subagents` — orchestration

#### 5B. Skills (Packaged Workflows)

Higher-level than tools, lower-level than agents. Opinionated, reusable.

Examples: Apple Reminders, Apple Notes, Media Library, Daily Briefing, Vault Search, 1Password

Each skill directory:
```
skills/skill-name/
├── SKILL.md          # Instructions
├── scripts/          # Helper scripts
└── references/       # Reference files
```

#### 5C. Information Layer

Perishable data kept fresh via Knowledge Loops:
- Movie releases (TMDB, weekly)
- Streaming drops
- Restaurant data (Google Places)
- Weather (on demand)
- Email (every heartbeat)
- Calendar (on demand)

**Key Distinction:**
- Knowledge compounds (vault, research)
- Information expires (releases, hours)

---

### Layer 6: Delivery & Scheduling

#### Scheduled Deliveries

| Delivery | Schedule | Channel |
|----------|----------|---------|
| Daily Briefing | 10:00 AM ET daily | Telegram |
| Learning Brief | Mon 8:00 AM ET | Telegram |
| Learning Accountability | Fri 4:00 PM ET | Telegram |
| Drink Pick | Wed 5:00 PM ET | Telegram |
| Plex Digest | Fri 1:00 PM ET | Email |
| Meal Plan | Sat 12:00 PM ET | Telegram |
| Weekend Kickoff | Thu 5:00 PM ET | Telegram |

#### Background Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| Nightly Sync | 2:00 AM daily | Places, recipes, diet prefs, backups |
| Research Ingest | 2:00 AM daily | outputs/research/ → vault |
| Vault Processor | Sun 5:00 AM | Readwise inbox → vault |

---

## Cross-Cutting: Model Stack

| Agent | Primary | Fallback |
|-------|---------|----------|
| TARS (main) | Claude Opus 4.6 | Sonnet 4.6 |
| Runner | Kimi K2.5 (free) | Sonnet 4.6 |
| Oracle | Gemini 3.1 Pro | Opus 4.6 |
| Marquee/Mise/Scout | Kimi K2.5 (free) | Sonnet 4.6 |
| Pixel | Sonnet 4.6 | Kimi K2.5 |
| Heartbeat | Kimi K2.5 (free) | — |
| Coding | Codex (GPT-5.3) | — |

**Cost Optimization:** Vertical agents use Kimi K2.5 (free) for routine. Opus for coordination.

---

## Cross-Cutting: Upgrade Mechanism

- Monthly OS review (first Friday of month)
- Each component scored 1-5
- Any component scoring ≤2 gets automatic upgrade brief
- Failure-tested rules accumulate from production — never pruned

---

## Directory Structure Reference

```
~/.openclaw/workspace/
├── AGENTS.md, SOUL.md, IDENTITY.md, USER.md
├── MEMORY.md, QUEUE.md, TOOLS.md, HEARTBEAT.md
├── memory/              # Daily logs
├── agents/              # Subagent workspaces
│   ├── researcher/      # Oracle
│   ├── media/           # Marquee
│   ├── chef/            # Mise
│   ├── concierge/       # Scout
│   ├── design/          # Pixel
│   └── runner/          # Runner
├── dossiers/
│   ├── briefs/          # B-001 through B-024+
│   ├── jobs/            # Cron job definitions
│   └── os-reviews/      # Monthly scorecards
├── wiki/                # System docs
├── skills/              # Packaged workflows
├── scripts/             # Utility scripts
├── data/preferences/    # Taste profiles
├── outputs/research/    # Research staging
└── specs/               # System specs
```

---

## 10 Key Principles to Replicate

1. **Task-First:** Every work item exists in queue before execution
2. **Aggressive Memory:** Write everything, curate later. Daily logs should be messy.
3. **Separate Persona from Operations:** `SOUL.md` can change without touching `AGENTS.md`
4. **Failure-Tested Rules are Sacred:** Mark production failures with 🔒, never prune
5. **Knowledge Compounds:** All research → one staging area → auto-ingested vault
6. **Autonomy Has Tiers:** Not everything needs approval; spending/external comms always do
7. **Vertical Agents Own Domains:** Coordinator doesn't freelance in another's area
8. **Preference → Corpus → Picks:** Every recommendation follows this three-layer pattern
9. **Knowledge Loops are Autonomous:** Agents detect and fill their own data gaps
10. **Context Budget Matters:** Monitor usage, alert before overflow, use targeted reads

---

*Documented by main agent — March 24, 2026*
