# Memory Test Sub-Agent Design

_A sub-agent that verifies context propagation and memory retention_

## Purpose

Before running real experiments, this sub-agent tests whether:
1. Files written by one sub-agent can be read by another
2. Git state persists across sub-agent runs
3. Context from previous experiments is accessible
4. Scoring is consistent between runs

## When to Use

- **Before major experiment batches:** Verify infrastructure works
- **After system changes:** Ensure memory still propagates
- **Debugging failures:** Isolate if issue is memory or logic
- **New agent onboarding:** Test that new agent can read/write context

---

## Test Suite Design

### Test 1: File Write/Read Propagation

**Objective:** Verify sub-agents can write and read shared files

**Sub-Agent A (Writer):**
```
Task: Write a test message to /shared/test-file.txt

Steps:
1. Generate a random string (e.g., "test-7843")
2. Write to /shared/test-file.txt
3. Report the string you wrote
```

**Sub-Agent B (Reader):**
```
Task: Read /shared/test-file.txt and report contents

Steps:
1. Read /shared/test-file.txt
2. Report the exact contents
3. Confirm you can read it
```

**Validation:**
- Contents match between Writer and Reader
- File exists after both complete
- No permission errors

---

### Test 2: Context Accumulation

**Objective:** Verify sub-agents can build on prior work

**Sub-Agent A (First Experiment):**
```
Task: Run experiment 1

1. Write result to /experiments/test-001/result.json:
   {"test": "001", "finding": "shorter is better"}
2. Commit to git
```

**Sub-Agent B (Second Experiment):**
```
Task: Run experiment 2, building on experiment 1

1. Read /experiments/test-001/result.json
2. Reference the finding from experiment 1 in your output
3. Write to /experiments/test-002/result.json:
   {"test": "002", "prior_finding": "...", "new_finding": "..."}
4. Confirm you read experiment 1's result
```

**Validation:**
- Experiment 2 references experiment 1's findings
- Both result files exist
- Git history shows both commits

---

### Test 3: Scoring Consistency

**Objective:** Verify APS scoring is deterministic

**Sub-Agent A (Score Sample A):**
```
Task: Score this output with APS rubric v2.0

Output: "📚 T-Rex was 40 feet long — that's a school bus!"

Steps:
1. Apply rubric v2.0 strictly
2. Document each bonus/penalty
3. Report final APS
4. Write to /test-runs/consistency-a.json
```

**Sub-Agent B (Score Same Sample):**
```
Task: Score the SAME output with APS rubric v2.0

Output: "📚 T-Rex was 40 feet long — that's a school bus!"

Steps:
1. Apply rubric v2.0 (don't read prior score)
2. Document each bonus/penalty
3. Report final APS
4. Write to /test-runs/consistency-b.json
```

**Validation:**
- Both sub-agents produce identical APS scores
- If different, rubric needs clarification

---

### Test 4: Git State Persistence

**Objective:** Verify sub-agents respect git branches

**Setup (Main Agent):**
```bash
git checkout -b experiments/memory-test
echo "baseline" > /test-runs/git-test.txt
git add -A && git commit -m "baseline"
```

**Sub-Agent (Modify and Commit):**
```
Task: Modify file and commit

1. Read /test-runs/git-test.txt (should say "baseline")
2. Append "-modified-by-subagent" to the file
3. Stage and commit
4. Report commit hash
```

**Validation (Main Agent):**
```bash
git log --oneline -3  # Should show sub-agent's commit
git show HEAD:test-runs/git-test.txt  # Should show modified content
```

---

### Test 5: Cross-Reference Validation

**Objective:** Verify sub-agents correctly read cross-references

**Setup:**
```json
// /shared/context-cache.json
{
  "sol": {
    "last_topic": "dinosaurs",
    "evaan_interests": ["dinosaurs", "space", "legos"]
  }
}
```

**Sub-Agent (Generate Lesson):**
```
Task: Generate a lesson using context-cache

1. Read /shared/context-cache.json
2. Check what Sol's last topic was
3. Pick a DIFFERENT topic from evaan_interests
4. Generate lesson on that topic
5. Confirm in output: "Chose [topic] because Sol last covered [last_topic]"
```

**Validation:**
- Sub-agent correctly reads context-cache
- Sub-agent avoids repetition (picks different topic)
- Output references prior context

---

## Memory Test Runner

A master script that orchestrates all tests:

```python
#!/usr/bin/env python3
# autoresearch/test_memory.py

import subprocess
import json
import sys

def run_memory_tests():
    results = {}
    
    # Test 1: File propagation
    print("\n🧪 Test 1: File Write/Read Propagation")
    spawn_subagent("memory-test-writer")
    result = spawn_subagent("memory-test-reader")
    results["file_propagation"] = validate_match("writer", "reader")
    
    # Test 2: Context accumulation
    print("\n🧪 Test 2: Context Accumulation")
    spawn_subagent("memory-test-exp-001")
    result = spawn_subagent("memory-test-exp-002")
    results["context_accumulation"] = validate_reference()
    
    # Test 3: Scoring consistency
    print("\n🧪 Test 3: Scoring Consistency")
    spawn_subagent("memory-test-score-a")
    spawn_subagent("memory-test-score-b")
    results["scoring_consistency"] = validate_scores_match()
    
    # Test 4: Git state
    print("\n🧪 Test 4: Git State Persistence")
    setup_git_test()
    spawn_subagent("memory-test-git")
    results["git_state"] = validate_git_commit()
    
    # Test 5: Cross-reference
    print("\n🧪 Test 5: Cross-Reference Validation")
    setup_context_cache()
    spawn_subagent("memory-test-crossref")
    results["cross_reference"] = validate_context_read()
    
    # Report
    print("\n" + "="*50)
    print("📊 MEMORY TEST RESULTS")
    print("="*50)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test}")
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = run_memory_tests()
    sys.exit(0 if success else 1)
```

---

## Integration with Experiment Workflow

### Pre-Experiment Checklist

Before batch of experiments:
```bash
cd autoresearch
python test_memory.py  # Verify infrastructure
python validate.py     # Check existing state
```

### Post-Experiment Validation

After experiments complete:
```bash
python validate.py --check-experiments  # Validate new experiments
```

---

## Failure Modes & Fixes

| Failure | Symptom | Likely Cause | Fix |
|---------|---------|--------------|-----|
| File not found | Reader can't find writer's file | Wrong path | Use absolute paths |
| Empty context | Sub-agent sees no prior experiments | Git branch mismatch | Verify branch before spawn |
| Inconsistent scoring | Same output, different APS | Subjective rubric | Make rubric binary |
| Git conflicts | Merge failures | Multiple sub-agents on same branch | One branch per experiment |
| Stale context | Sub-agent uses old data | context-cache not updated | Write to cache after each experiment |

---

## Example: Running Memory Test

```bash
# 1. Run memory validation
cd ~/.openclaw/workspace/autoresearch
python test_memory.py

# 2. If all pass, proceed with real experiments
python agent_runner.py --agent sol --experiment hook-optimization

# 3. Validate results
python validate.py
```

---

## Success Criteria

Memory system is working when:
- ✅ All 5 memory tests pass
- ✅ Experiments can read prior results
- ✅ Git history shows clean commits
- ✅ Scoring is consistent (±0 points on same input)
- ✅ Context cache updates propagate

Then: Safe to run autonomous experiments overnight.
