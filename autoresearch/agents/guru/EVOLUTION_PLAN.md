# Guru v2.0 Evolution Plan

## The Problem
Guru's messages were stuck in a loop:
- Same abstract opening structure ("What if...")
- Preamble-heavy ("The Stoics believed...")
- No clear progression or variety
- Actionability unclear
- User engagement: 25% (baseline)

## What Sol's Autoresearch Proved
Sol's evolution from APS 80 → 15 demonstrated:
1. **Rotation prevents monotony**: LEGO/Space/Dino 40/30/30 split
2. **Concrete hooks win**: "LEGO uses triangles" beats "Engineering principles state"
3. **Length discipline**: 45-55 words is the engagement sweet spot
4. **Single concept rule**: One idea, fully explored
5. **Actionable close**: "Ask your parents" creates engagement

## Guru v2.0 Adaptations

### Rotation System (Like Sol's Theme Days)
| Day | Tradition | Hook Style | Example Observation |
|-----|-----------|------------|---------------------|
| Monday | Stoicism | Obstacle framing | "Your coffee spills. Traffic stalls." |
| Tuesday | Zen | Present-moment | "You checked your phone twice reading this." |
| Wednesday | Bhagavad Gita | Duty/purpose | "Three tasks compete for your attention." |
| Thursday | Stoicism | Choice/control | "Someone cuts you off in traffic." |
| Friday | Zen | Paradox/riddle | "The more you chase calm, the faster it runs." |
| Saturday | Bhagavad Gita | Service/sacrifice | "You have one hour. Yourself or others?" |
| Sunday | Integration | Cross-tradition | "Stoics say control. Zen says let go." |

### Structural Formula (Applied Daily)
```
🧘 [OBSERVATION: Concrete, 8-12 words]

[INSIGHT: Tradition + principle, 15-20 words]

[ACTION: "Today:" + specific, 10-15 words]
```

**Total: 45-55 words** (same as Sol's proven target)

### Key Changes from v1.0

| Aspect | v1.0 (Old) | v2.0 (New) |
|--------|-----------|-----------|
| Opening | Abstract question ("What if...") | Concrete observation ("Your coffee spills...") |
| Attribution | "The Stoics believed" (reporting) | "Marcus Aurelius:" (direct) |
| Tradition mixing | Sometimes mixed | Strictly one per day |
| Length | Unstructured, often verbose | 45-55 words hard limit |
| Action | "Reflect on..." (vague) | "Say 'not mine' silently" (observable) |
| Rotation | None (repetitive) | 7-day cycle |

## Files Created

1. **`prompt-v2.0.md`** — New agent prompt with rotation system
2. **`APS_RUBRIC_GURU.md`** — Scoring rubric (target: 25-40 APS)
3. **`update-v2.0.sh`** — Script to apply the update
4. **`EVOLUTION_PLAN.md`** — This document

## Testing Protocol

### Phase 1: Validation (Today)
- [x] Generate test output using v2.0 prompt
- [ ] Score with APS rubric
- [ ] Verify word count, structure, rotation

### Phase 2: Deployment (Tomorrow)
- [ ] Run `update-v2.0.sh` to apply new prompt
- [ ] Monitor 5:15 AM delivery
- [ ] Score actual output

### Phase 3: Iteration (Week 1)
- [ ] Daily APS scoring
- [ ] Track user engagement (replies, reactions)
- [ ] Adjust if APS > 40 after 3 days

### Phase 4: Baseline Update (Week 2)
- [ ] Calculate new baseline APS
-- [ ] Update `baselines/guru_baseline.json`
- [ ] Mark autoresearch_status as "in_progress" in agent-registry.json

## Success Metrics

| Metric | Baseline (v1.0) | Target (v2.0) |
|--------|----------------|---------------|
| APS Score | 70 | 25-40 |
| User Engagement | 25% | 40%+ |
| Word Count | Variable (60-120) | 45-55 |
| Reply Rate | Low | Medium |

## Comparison: Old vs New

### v1.0 (Yesterday's Actual Message)
```
You optimize your mornings for deep work. Four hours of flow. Systems, 
signals, scanner improvements. The autoresearch runs. Everything measured, 
refined, made efficient.

Then family time begins. 5 PM. Dinner with Natasha and Evaan.

But here's the question the Stoics would press on you: *When you are with 
them, are you truly there?* Epictetus taught that attention is the only 
thing fully ours — and the only thing we can truly give. A divided mind 
is not presence. It is absence wearing presence's mask.

Zen has a word for this: *mushin* — no-mind. Not emptiness, but fullness. 
When you eat, just eat. When you play, just play. Not while planning 
tomorrow's scanner upgrade or reviewing SPY signals.

The Bhagavad Gita's karma yoga speaks to you here. Action without 
attachment to results. But there's a deeper cut: *attachment to the act 
of optimizing itself.* You are building systems so you can be present. 
At what point does the building become the barrier?

You chose quality over quantity in your values. But quality is not a 
setting you configure. It is a state you enter. The same presence you 
bring to 6 AM code — that single-pointedness — does it follow you to 
the dinner table?

Or has efficiency become your default mode, even in places that ask 
for something else?

**Burning question:** If Evaan remembers these years, will he remember 
you *there* — or you *nearby, thinking about systems*?
```
**Word count:** 248 words  
**APS Score:** ~85 (multiple traditions, verbose, abstract opening, no clear action)

### v2.0 (Target)
```
🧘 Your coffee spills. Traffic stalls. Plans break.
Marcus Aurelius: "You have power over your mind — not outside events."
Today: Notice one external frustration and say "not mine" silently.
```
**Word count:** 49 words  
**APS Score:** ~15 (concrete, one tradition, compact, actionable)

## Why This Will Work

1. **Same pattern as Sol**: Concrete hook → Single concept → Actionable close
2. **Rotation prevents fatigue**: Like LEGO/Space/Dino, different traditions keep it fresh
3. **Observable actions**: "Say 'not mine'" is clearer than "be present"
4. **Length discipline**: 45-55 words respects morning attention spans
5. **Direct attribution**: "Marcus Aurelius:" beats "The Stoics believed"

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Too terse loses depth | Daily rotation provides variety; Sunday integration ties threads |
| Concrete observations feel forced | Build library of 20+ observations, rotate |
| User misses longer format | If engagement drops, test 60-70 word version |
| One-tradition-per-day feels rigid | Sunday = integration day for cross-tradition insights |

## Next Actions

1. **Review test output** from subagent when complete
2. **Apply update** via `update-v2.0.sh`
3. **Monitor tomorrow's 5:15 AM delivery**
4. **Score and iterate** through the week
