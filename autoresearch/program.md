# Program: OpenClaw Agent Optimization

_Instructions for the autonomous research agent_

## Goal

Optimize OpenClaw agent prompts to maximize user engagement, relevance, and delivery reliability. Focus on the "silent verticals" first (agents that run without user feedback).

## Target Agents (in priority order)

1. **Dax** (Personal Trainer) — 4:30 AM daily
   - Current issue: Predictable format, declining engagement
   - Success metric: User replies with 👍 or engages within 2h

2. **Guru** (Spirituality Guide) — 5:15 AM daily
   - Current issue: Too verbose for morning delivery
   - Success metric: Compact wisdom, actionable takeaway

3. **Sol** (Academic Tutor) — 7:00 AM daily
   - Current issue: Sometimes too complex for 7-year-old
   - Success metric: Evaan asks follow-up questions

## Experiment Loop

```
FOR each experiment:
  1. CHECKOUT new branch: experiments/dax-{timestamp}
  
  2. MODIFY agent prompt based on hypothesis
     - Read current prompt from agents/{agent}/prompt.md
     - Apply ONE change at a time (controlled variable)
     - Options: tone, length, structure, personalization
  
  3. RUN dry-test delivery
     - Use sessions_spawn with runtime="subagent"
     - Capture output quality metrics
  
  4. EVALUATE results (see APS scoring below)
  
  5. COMMIT or REVERT
     - IF APS < baseline: git commit -m "dax: shorter intro, APS 72→68"
     - IF APS >= baseline: git checkout -- agents/{agent}/prompt.md
  
  6. MERGE to main after 5 consecutive improvements
     - OR create PR for human review if unsure
```

## APS Scoring (Agent Performance Score)

Lower is better. Baseline targets:

| Agent | Current APS | Target APS | Primary Lever |
|-------|-------------|------------|---------------|
| dax | ~75 | 60 | Hook quality, brevity |
| guru | ~70 | 55 | Compactness, actionability |
| sol | ~80 | 65 | Age-appropriateness |

### Scoring Formula

```python
def calculate_aps(output, delivery_status, user_feedback=None):
    score = 100
    
    # Length penalty (excessive length = bad)
    words = len(output.split())
    if words > 150: score -= (words - 150) * 0.1
    
    # Structure bonus (has clear sections)
    if has_clear_sections(output): score -= 5
    
    # Delivery penalty (any errors)
    if delivery_status != "success": score += 20
    
    # Engagement bonus (if we have feedback data)
    if user_feedback:
        if user_feedback.engaged: score -= 15
        if user_feedback.replied: score -= 10
    
    return max(0, score)
```

## Hypothesis Bank (test these)

### Dax
- [ ] Shorter hook (< 10 words)
- [ ] Lead with emoji + action, not greeting
- [ ] Remove "Good morning" intros
- [ ] Add "Time to..." imperative opens
- [ ] Include "Why this matters" one-liner

### Guru
- [ ] Max 3 sentences
- [ ] Lead with question, not statement
- [ ] End with single action item
- [ ] Remove "Today we explore..." preamble

### Sol
- [ ] Start with kid-friendly hook (dinosaurs, space, legos)
- [ ] One concept max per lesson
- [ ] Always end with "Ask your parents..." question
- [ ] Use Evaan's interests (check context-cache.json)

## Constraints

- One variable change per experiment
- Max 10 experiments per night
- Never modify: schedules, credentials, USER.md, MEMORY.md
- All commits must reference this program.md
- If unsure, ask human via Telegram

## Current Baseline

See `baselines/` directory for current agent outputs.

## Success Criteria

Stop when:
- 3 consecutive agents hit target APS for 3 days
- OR human says "this is good enough"

Then: Move to next agent in priority list.
