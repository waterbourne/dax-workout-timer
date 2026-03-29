# APS Rubric — Guru (Spirituality Guide) v2.0

_Standardized scoring for Guru's morning contemplation messages_

## Philosophy
Lower is better. Target range: 25-40.

Based on Sol's evolution, these factors drive engagement:
1. **Concrete observation** — Start with something they can notice today
2. **Single tradition** — Don't mix Stoicism + Zen in one message
3. **Compact wisdom** — 45-55 words optimal
4. **Actionable close** — "Today:" + specific thing to try

---

## Scoring Algorithm

```python
def calculate_guru_aps(output):
    score = 100
    words = output.split()
    word_count = len(words)
    text = output.lower()
    
    # === SECTION A: LENGTH (max -25 points) ===
    if 45 <= word_count <= 55:
        score -= 25  # Sweet spot
    elif 40 <= word_count <= 60:
        score -= 15  # Acceptable
    elif 35 <= word_count <= 70:
        score -= 5   # Edges
    else:
        score += 10  # Penalty for way off
    
    # === SECTION B: HOOK — Concrete Observation (max -25 points) ===
    first_15 = ' '.join(words[:15]).lower()
    
    # B1: Starts with observable action? (traffic, coffee, phone, etc.)
    observations = ['spill', 'traffic', 'coffee', 'phone', 'check', 'notice', 
                    'watch', 'listen', 'feel', 'see', 'hear', 'you']
    if any(obs in first_15 for obs in observations):
        score -= 15
    
    # B2: Present tense / immediate? (not "the Stoics believed")
    if 'you ' in first_15 or 'your ' in first_15:
        score -= 10
    
    # === SECTION C: TRADITION CLARITY (max -20 points) ===
    
    # C1: Exactly ONE tradition cited?
    traditions = ['marcus', 'aurelius', 'stoic', 'zen', 'zazen', 'koan', 
                  'bhagavad', 'gita', 'krishna', 'epictetus', 'seneca']
    tradition_count = sum(1 for t in traditions if t in text)
    if tradition_count == 1:
        score -= 15
    elif tradition_count > 1:
        score += 10  # Penalty for mixing
    
    # C2: Attribution clear but not academic?
    if any(phrase in text for phrase in ['believed that', 'taught us', 'philosophy of']):
        score += 5  # Weak attribution penalty
    
    # === SECTION D: ACTIONABILITY (max -20 points) ===
    
    # D1: Ends with "Today:" trigger?
    if 'today:' in text or 'today :' in text:
        score -= 10
    
    # D2: Action is observable/doable? (not "reflect on" or "consider")
    actions = ['say ', 'name ', 'write ', 'set ', 'notice ', 'count ', 
               'pause ', 'breathe ', 'watch ', 'listen ', 'feel ']
    if any(act in text for act in actions):
        score -= 10
    
    # === SECTION E: PENALTIES (add to score) ===
    
    # E1: Preamble?
    if any(phrase in text[:50] for phrase in ['today we', 'let us', 'we will', 
                                               'this morning', 'good morning']):
        score += 15
    
    # E2: Abstract opening? ("the present moment", "wisdom teaches")
    abstract = ['the present', 'wisdom', 'philosophy', 'ancient', 'teaches us',
                'reminds us', 'shows us']
    if any(abs in first_15 for abs in abstract):
        score += 10
    
    # E3: Multiple concepts?
    concept_markers = ['also', 'furthermore', 'additionally', 'second', 'third']
    if any(m in text for m in concept_markers):
        score += 10
    
    # E4: Question-only hook? (Questions are okay but need substance)
    if text.startswith('🧘 what if') or text.startswith('🧘 what'):
        score += 5  # Slight penalty for pure question hooks
    
    return max(0, min(100, score))
```

---

## Scoring Examples

### Example 1: Poor Baseline (High APS = Bad)

```
🧘 What if the obstacle IS the path?
The Stoics believed challenges reveal our character and help us grow 
as individuals. When we face difficulties with the right mindset, 
we can transform them into opportunities for personal development.
Today, name one difficulty you're grateful for and reflect on how 
it has shaped you.
```

| Check | Result | Points |
|-------|--------|--------|
| Length (50 words) | 45-55 | -25 |
| Observable hook? | No (abstract question) | +0 |
| Present/immediate? | No | +0 |
| One tradition? | Yes | -15 |
| Weak attribution? | Yes ("believed") | +5 |
| "Today:" trigger? | Yes | -10 |
| Observable action? | Yes ("name") | -10 |
| Preamble? | No | +0 |
| Abstract opening? | Yes ("What if") | +10 |
| Multiple concepts? | No | +0 |
| **TOTAL APS** | | **55** |

### Example 2: Good Improved Version (Lower APS = Better)

```
🧘 Your coffee spills. Traffic stalls. Plans break.
Marcus Aurelius: "You have power over your mind — not outside events."
Today: Notice one external frustration and say "not mine" silently.
```

| Check | Result | Points |
|-------|--------|--------|
| Length (49 words) | 45-55 | -25 |
| Observable hook? | Yes (spills, traffic, plans) | -15 |
| Present/immediate? | Yes ("Your", "You") | -10 |
| One tradition? | Yes (Marcus) | -15 |
| Weak attribution? | No (direct quote) | +0 |
| "Today:" trigger? | Yes | -10 |
| Observable action? | Yes ("notice", "say") | -10 |
| Preamble? | No | +0 |
| Abstract opening? | No | +0 |
| Multiple concepts? | No | +0 |
| **TOTAL APS** | | **15** |

### Example 3: Mediocre (Needs Work)

```
🧘 The present moment is all we truly have in this life.
Zen teaches that distraction is suffering and attention is freedom.
Sit quietly for two minutes and just breathe.
```

| Check | Result | Points |
|-------|--------|--------|
| Length (40 words) | 40-44 | -15 |
| Observable hook? | No (abstract concept) | +0 |
| Present/immediate? | No | +0 |
| One tradition? | Yes (Zen) | -15 |
| Weak attribution? | Yes ("teaches") | +5 |
| "Today:" trigger? | No | +0 |
| Observable action? | Yes ("sit", "breathe") | -10 |
| Preamble? | No | +0 |
| Abstract opening? | Yes ("present moment") | +10 |
| Multiple concepts? | No | +0 |
| **TOTAL APS** | | **75** |

---

## Target Scores

| Quality Level | APS Range | Description |
|---------------|-----------|-------------|
| **Excellent** | 0-25 | Gold standard — concrete, actionable, compact |
| **Good** | 26-40 | Solid — meets criteria |
| **Acceptable** | 41-55 | Passable — minor issues |
| **Needs Work** | 56-75 | Multiple issues |
| **Poor** | 76-100 | Major problems, rewrite required |

## Validation Checklist

Before finalizing an APS score:
- [ ] Word count verified (exact count, not estimate)
- [ ] First 15 words identified exactly
- [ ] Tradition count verified (search for keywords)
- [ ] Attribution style checked ("believed" vs direct quote)
- [ ] "Today:" presence confirmed
- [ ] Action verbs identified
- [ ] No double-counting penalties
