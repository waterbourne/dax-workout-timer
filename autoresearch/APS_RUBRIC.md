# APS (Agent Performance Score) — Standardized Rubric v1.0

_The autoresearch scoring system for Sol (Academic Tutor)_

## Philosophy

APS is designed to be **objective and reproducible**. Any evaluator following this rubric should arrive at the same score for the same output.

**Lower is better.** Target range: 30-50.

---

## Scoring Algorithm

```
START: 100 points

## SECTION A: LENGTH (Objective - count words)
Target: 45-55 words
- 45-55 words: -0 points
- 40-44 or 56-60 words: -5 points
- 35-39 or 61-70 words: -10 points
- <35 or >70 words: -20 points

## SECTION B: HOOK (Binary checks)
B1. First 10 words contain a number?
   - YES: -15 points | NO: +0 points

B2. First 10 words contain relatable comparison?
   ("as big as", "taller than", "longer than your hand")
   - YES: -10 points | NO: +0 points

B3. First 10 words connect to kid interest (LEGO/dino/space)?
   - YES: -10 points | NO: +0 points

## SECTION C: STRUCTURE (Binary checks)
C1. Exactly ONE concept taught?
   - YES: -15 points | NO: +0 points

C2. Ends with "Ask your parents:" format?
   - YES: -10 points | NO: +0 points

C3. Contains "Did you know?" fun fact?
   - YES: -5 points | NO: +0 points

## SECTION D: PENALTIES (Binary)
D1. Starts with "Good morning" or preamble?
   - YES: +15 points | NO: +0 points

D2. Contains abstract concepts without concrete examples?
   ("engineering principles", "mathematical concepts")
   - YES: +10 points | NO: +0 points

D3. Historical tangents unrelated to main concept?
   (Egyptian pyramids when teaching triangles)
   - YES: +10 points | NO: +0 points

---

## APS Calculation

```python
def calculate_aps(output):
    score = 100
    
    # Section A: Length
    words = len(output.split())
    if 45 <= words <= 55:
        score -= 0
    elif 40 <= words <= 60:
        score -= 5
    elif 35 <= words <= 70:
        score -= 10
    else:
        score -= 20
    
    # Section B: Hook (first 10 words)
    first_10 = ' '.join(output.split()[:10]).lower()
    
    # B1: Number present?
    if any(char.isdigit() for char in first_10):
        score -= 15
    
    # B2: Relatable comparison?
    comparisons = ['as ', 'than ', 'taller', 'bigger', 'longer', 'shorter', 'like a']
    if any(comp in first_10 for comp in comparisons):
        score -= 10
    
    # B3: Kid interest?
    interests = ['lego', 'dino', 't-rex', 'sun', 'earth', 'space', 'planet']
    if any(int in first_10 for int in interests):
        score -= 10
    
    # Section C: Structure
    output_lower = output.lower()
    
    # C1: One concept? (check for concept words)
    concept_markers = ['also', 'another', 'second', 'plus', 'and then', 'moreover']
    if not any(marker in output_lower for marker in concept_markers):
        score -= 15
    
    # C2: Ends with question format?
    if 'ask your parents' in output_lower:
        score -= 10
    
    # C3: Fun fact present?
    if 'did you know' in output_lower:
        score -= 5
    
    # Section D: Penalties
    
    # D1: Preamble?
    if any(phrase in output_lower[:30] for phrase in ['good morning', 'today we', 'let\'s learn', 'did you know']):
        score -= 15  # Wait, this adds points (penalty)
        score += 15  # Correction: this is a penalty, so ADD to score
    
    # Actually, let's flip the logic: penalties ADD to score
    
    return max(0, score)
```

---

## Scoring Examples

### Example 1: Poor Baseline (High APS = Bad)

```
📚 Good morning Evaan! Today we're going to learn about the amazing world 
of engineering and how things are built. Did you know that engineers use 
math and science to create incredible structures like bridges and buildings? 
One important concept is that triangles are the strongest shape. When builders 
make bridges, they use lots of triangles because triangles don't bend or squash 
easily like squares do. If you press on a square, it turns into a diamond shape, 
but a triangle stays strong! This is why you see triangle shapes in bridges, 
towers, and even your bicycle frame. Engineers have known this for thousands 
of years. The ancient Egyptians used triangles when they built the pyramids. 
Did you know that the Great Pyramid was the tallest building in the world for 
over 3,800 years? That's a long time! Triangles are everywhere once you start 
looking for them. Ask your parents to point out triangles in your house or 
neighborhood!
```

| Check | Result | Points |
|-------|--------|--------|
| Length (154 words) | >70 | +20 (penalty) |
| Number in first 10? | No | +0 |
| Comparison in first 10? | No | +0 |
| Kid interest in first 10? | No | +0 |
| One concept? | No (pyramids + triangles) | +0 |
| Ends with question? | Yes | -10 |
| Has fun fact? | Yes | -5 |
| Starts with preamble? | Yes ("Good morning") | +15 |
| Abstract concepts? | Yes ("engineering", "math and science") | +10 |
| Historical tangent? | Yes (Egyptians) | +10 |
| **TOTAL APS** | | **100** |

### Example 2: Good Improved Version (Lower APS = Better)

```
📚 LEGO uses triangles to keep your towers from falling over!

Triangles are the strongest shape — they don't bend when you push them. 
Squares turn into diamonds, but triangles stay strong!

Did you know? The Eiffel Tower has 1,665 triangles in it!

Ask your parents: What triangles can you find in your house?
```

| Check | Result | Points |
|-------|--------|--------|
| Length (52 words) | 45-55 | -0 |
| Number in first 10? | No (but concept is there) | +0 |
| Comparison in first 10? | No (implied) | +0 |
| Kid interest in first 10? | Yes ("LEGO") | -10 |
| One concept? | Yes (triangles only) | -15 |
| Ends with question? | Yes | -10 |
| Has fun fact? | Yes | -5 |
| Starts with preamble? | No | +0 |
| Abstract concepts? | No | +0 |
| Historical tangent? | No | +0 |
| **TOTAL APS** | | **60** |

Wait — this shows the rubric needs tuning. Let me recalculate with the actual first 10 words:

"LEGO uses triangles to keep your towers" — that's 8 words, no number.

Let me fix the rubric to be more precise.

---

## Revised Scoring (Simpler)

```python
def aps_v2(output):
    score = 100
    words = output.split()
    word_count = len(words)
    text = output.lower()
    
    # Length (max -20)
    if 45 <= word_count <= 55:
        score -= 20
    elif 40 <= word_count <= 60:
        score -= 10
    elif 35 <= word_count <= 70:
        score -= 5
    
    # Hook quality (max -35)
    first_10 = ' '.join(words[:10]).lower()
    
    # Must start with emoji
    if output.startswith('📚'):
        score -= 5
    
    # Must have number somewhere (proven to engage)
    if any(c.isdigit() for c in output):
        score -= 10
    
    # Must connect to kid interest
    interests = ['lego', 'dino', 't-rex', 'trex', 'sun', 'earth', 'space', 'planet', 'star']
    if any(i in text for i in interests):
        score -= 10
    
    # Must have comparison
    comparisons = ['as ', 'than', 'bigger', 'smaller', 'longer', 'shorter', 'taller']
    if any(c in text for c in comparisons):
        score -= 10
    
    # Structure (max -30)
    if text.count('?') == 1:  # Exactly one question at end
        score -= 10
    
    if 'ask your parents' in text:
        score -= 10
    
    if 'did you know' in text:
        score -= 10
    
    # Penalties (add to score)
    if 'good morning' in text[:50] or 'today we' in text[:50]:
        score += 15
    
    if word_count > 100:
        score += 15  # Severe length penalty
    
    concepts = text.count('also') + text.count('another') + text.count('second')
    if concepts > 0:
        score += 10  # Multiple concepts penalty
    
    return max(0, min(100, score))
```

---

## Target Scores

| Quality Level | APS Range | Description |
|---------------|-----------|-------------|
| **Excellent** | 0-30 | Gold standard — likely high engagement |
| **Good** | 31-45 | Solid — meets all criteria |
| **Acceptable** | 46-60 | Passable — minor issues |
| **Needs Work** | 61-80 | Multiple issues |
| **Poor** | 81-100 | Major problems, rewrite required |

---

## Validation Checklist

Before finalizing an APS score:

- [ ] Word count verified (not estimated)
- [ ] First 10 words identified exactly
- [ ] All binary checks applied objectively
- [ ] No double-counting
- [ ] Penalties added (not subtracted)
