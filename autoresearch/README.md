# AutoResearch for OpenClaw Agents

_Experimental self-improvement system inspired by karpathy/autoresearch_

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  program.md │────▶│  Agent Loop  │────▶│  agent.md   │
│  (human)    │     │  (autonomous)│     │  (agent)    │
└─────────────┘     └──────────────┘     └──────┬──────┘
       ▲                                        │
       │         ┌──────────────┐               │
       └─────────│  Git commit  │◀──────────────┘
                 │  (if better) │
                 └──────────────┘
```

## Core Components

| File | Purpose | Modified By |
|------|---------|-------------|
| `program.md` | Agent instructions, success criteria, iteration strategy | Human |
| `agent_runner.py` | Executes agent, measures output quality | System |
| `evaluator.py` | Scores agent output (engagement, accuracy, etc.) | System |
| `experiments/` | Git branches for each experiment run | Auto |

## Metric: Agent Performance Score (APS)

Composite score (0-100) based on:
- **Engagement**: Did user respond/acknowledge? (40%)
- **Quality**: Grammar, structure, relevance (30%)
- **Timeliness**: Delivered within window? (20%)
- **Error-free**: No crashes, timeouts (10%)

Lower APS = better. Track via delivery queue + user feedback.

## Running Experiments

### 1. Setup (one-time)
```bash
cd ~/.openclaw/workspace/autoresearch
uv sync  # or pip install -r requirements.txt
```

### 2. Manual baseline
```bash
# Run agent once, measure output
uv run agent_runner.py --agent dax --dry-run
```

### 3. Autonomous mode
Spin up a sub-agent in this directory:

```
Hi, read program.md and kick off a new experiment. 
Let's iterate on Dax's workout prompts to improve engagement.
```

The agent will:
1. Read current Dax prompt from `agents/dax/prompt.md`
2. Modify it based on `program.md` instructions
3. Run a test delivery (dry-run)
4. Commit if APS improves, revert if not
5. Repeat

## Current Experiments

| Date | Agent | Variable Tested | Result | Commit |
|------|-------|-----------------|--------|--------|
| 2026-03-09 | dax | Shorter intros | TBD | - |

## Integration with OpenClaw

The autoresearch agent runs as a **separate cron job** that:
- Operates during low-traffic hours (2-4 AM)
- Works on a git feature branch
- Only modifies agent prompts/configs, not core system
- Creates PRs (or direct commits) for human review when significant improvement found

## Safety

- Runs in isolated workspace (`autoresearch/`)
- All changes go through git (revertible)
- Human maintains `program.md` (the "constitution")
- Agent cannot modify: schedules, credentials, system configs
