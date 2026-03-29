# Knowledge Vault — Index

_Compounding knowledge base. Everything searchable, everything connected._

---

## Directory Structure

```
vault/
├── agents/          # Agent definitions, rosters, capabilities
├── concepts/        # Core ideas, frameworks, principles
├── decisions/       # Architectural and strategic decisions (ADRs)
├── lessons/         # Production failures and fixes (failure-tested rules)
├── projects/        # Project documentation, briefs
├── reference/       # External knowledge, cheat sheets
└── system/          # OS-level documentation
```

---

## Quick Links

### Agents
- [Agent OS Architecture (from TARS)](./system/agent-os-architecture.md) — Harish's complete system blueprint
- [Pixel Design Training](./agents/pixel-design-training.md) — Design agent skill modules

### Concepts
- [Three-Tier Memory System](./concepts/three-tier-memory.md)
- [Autonomous Knowledge Loops](./concepts/knowledge-loops.md)
- [Vertical vs Horizontal Agents](./concepts/agent-taxonomy.md)

### Decisions
- [Decision Record Template](./decisions/0000-template.md)

### Lessons
- [Failure-Tested Rules](./lessons/failure-tested-rules.md)

---

## How to Use This Vault

1. **Daily logs** go in `memory/YYYY-MM-DD.md` (working memory)
2. **Promote to vault** when knowledge has 6+ month relevance
3. **Link everything** — use `[[note-name]]` style links
4. **Tag aggressively** — `#concept #agent #decision #lesson`
5. **Search first** — use `memory_search` before asking

---

*Pattern adopted from TARS Agent OS (Harish/7islands)*
