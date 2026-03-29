# Lossless-Claw Improvements

## Implemented Enhancements

### 1. HEARTBEAT_OK Pruning (Default On)
**File:** `config/hearbeat-pruning.patch`

Changes default `LCM_PRUNE_HEARTBEAT_OK` from `false` to `true`.

**Impact:** 
- Reduces storage by 30-50% for typical OpenClaw setups
- Removes noise from heartbeat polling cycles
- Preserves actual conversation content

### 2. lcm_stats Command
**File:** `tools/lcm-stats.ts`

New tool for visibility into LCM performance:
- Total messages stored
- Compression ratio (raw vs summarized tokens)
- DAG depth
- Storage used (SQLite size)
- Retrieval hit rate
- Cost tracking (tokens used for summarization)

### 3. Memory Search Integration
**File:** `tools/lcm-memory-search.ts`

Unified search across:
- MEMORY.md (curated long-term memory)
- LCM SQLite (raw conversation history)
- Agent registry context

Returns structured results with source attribution.

### 4. Sub-Agent Context Inheritance
**File:** `bridge/sub-agent-context.ts`

Passes parent session's LCM DAG to sub-agents:
- Sub-agents can `lcm_expand` parent context
- Critical for long-running research tasks
- Maintains continuity across session spawns

## Usage

```bash
# Check LCM statistics
openclaw tools lcm-stats

# Unified memory search
openclaw tools lcm-memory-search "what did we decide about X?"

# Sub-agent inherits context automatically
sessions_spawn --inherit-lcm --task "research project"
```
