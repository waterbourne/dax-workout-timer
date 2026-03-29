# LearnQuest Autoresearch Testing Program
## Agent Performance Score (APS) Rubric for Kids' Educational Game

### Test Flows (User Journeys)

#### FLOW 1: First-Time User (Onboarding)
1. Open app → see welcome
2. Check daily quest
3. Tap kingdom → open lesson
4. Complete lesson → XP gain
5. See level up (if applicable)
6. Check character screen
7. Return tomorrow → streak maintained

#### FLOW 2: Returning User (Daily Loop)
1. Open app → see today's quests
2. Complete Sol lesson
3. Complete Atlas story
4. Claim daily bonus
5. Check kingdom progress
6. Equip new gear if unlocked

#### FLOW 3: Parent Admin
1. Open admin panel
2. Add tomorrow's Sol lesson
3. Add tomorrow's Atlas story
4. Preview in app
5. Publish

### APS Scoring (0-100, lower is better)

**Bonuses (subtract from 100):**
- Lesson completes in < 5 taps: -20
- XP animation visible: -15
- Level up feels exciting: -15
- Kid wants to do second lesson: -10
- No confusion/frustration: -10
- Wants to return tomorrow: -10

**Penalties (add to 100):**
- Can't find today's lesson: +25
- XP gain not noticeable: +20
- No celebration on complete: +20
- Confusing navigation: +15
- Too much reading before action: +15
- App crashes or freezes: +50

### Target: APS < 30 (excellent)

### Test Protocol
1. Simulate each flow 3x
2. Time each interaction
3. Note confusion points
4. Score and log
5. Iterate on lowest scores