# Concept: Three-Tier Memory System

_Adopted from TARS Agent OS_

---

## The Tiers

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: DAILY LOGS                                         │
│  Location: memory/YYYY-MM-DD.md                             │
│  Horizon: 1-2 days                                          │
│  Content: Everything — messy, complete, timestamped         │
│  Access Pattern: Read today + yesterday on session start    │
└─────────────────────────────────────────────────────────────┘
                             ↓
                    (manual curation)
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: MEMORY.md                                          │
│  Location: MEMORY.md                                        │
│  Horizon: 6+ months                                         │
│  Content: Curated long-term facts, decisions, constraints   │
│  Access Pattern: Loaded in main session only (security)     │
└─────────────────────────────────────────────────────────────┘
                             ↓
                    (vector embeddings)
                             ↓
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: VECTOR SEARCH                                      │
│  Backend: SQLite + sqlite-vec                               │
│  Horizon: Unlimited                                         │
│  Content: Semantic search across all memory                 │
│  Access Pattern: memory_search tool before context queries  │
└─────────────────────────────────────────────────────────────┘
```

---

## Rules

### For Daily Logs
- **Write aggressively** — decisions, failures, context learned
- **Create immediately** — if missing, create before ending session
- **Don't batch** — write as things happen
- **Capture "why"** — not just what happened

### For MEMORY.md
- **6+ month horizon** — will this matter in 6 months?
- **Promote manually** — review daily logs, curate what matters
- **Security boundary** — only load in main session (direct chats)
- **Update freely** — this is long-term memory

### For Vector Search
- **Search first** — use `memory_search` before answering context questions
- **Hybrid scoring** — 70% vector, 30% BM25
- **Curate embeddings** — not everything needs vector indexing

---

## Comparison to TARS System

| Aspect | TARS System | Our System | Gap |
|--------|-------------|------------|-----|
| Daily logs | ✅ `memory/YYYY-MM-DD.md` | ✅ Same | None |
| Curated memory | ✅ `MEMORY.md` | ✅ Same | None |
| Vector search | ✅ SQLite + sqlite-vec | ❌ Not implemented | **Medium** |
| Vault compounding | ✅ Obsidian + auto-ingest | ⚠️ New vault/ dir | **Medium** |

**Next Steps:**
1. Implement `memory_search` with sqlite-vec backend
2. Set up vault auto-ingestion pipeline
3. Create embeddings for key documents

---

*Documented: 2026-03-24*
