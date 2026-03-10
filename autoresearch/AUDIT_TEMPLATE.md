# Experiment Audit Trail

_This file tracks every step of an autoresearch experiment. Sub-agents MUST fill this out._

## Experiment Metadata

| Field | Value |
|-------|-------|
| **Agent** | <!-- e.g., sol, dax, guru --> |
| **Experiment ID** | <!-- e.g., sol-2026-03-09-hooks --> |
| **Branch** | <!-- e.g., experiments/sol-2026-03-09-hooks --> |
| **Date** | <!-- YYYY-MM-DD --> |
| **Hypothesis** | <!-- What we're testing --> |

---

## Pre-Flight Checks (BEFORE starting)

### File Access Verification

| File | Path | Status | Evidence |
|------|------|--------|----------|
| Agent prompt | `agents/{agent}/prompt.md` | ⬜ | First line: "..." |
| Program instructions | `program.md` | ⬜ | First line: "..." |
| Baseline data | `baselines/{agent}_baseline.json` | ⬜ | APS: ## |
| Previous experiments | `experiments/` | ⬜ | N prior experiments found |
| Context cache | `../shared/context-cache.json` | ⬜ | Read: yes/no |

### Git State Verification

| Check | Command | Expected | Actual | Status |
|-------|---------|----------|--------|--------|
| Current branch | `git branch --show-current` | `experiments/...` | | ⬜ |
| Clean working tree | `git status --porcelain` | Empty | | ⬜ |
| On main? | `git rev-parse --abbrev-ref HEAD` | No | | ⬜ |

---

## Experiment Execution (DURING)

### Step 1: Read & Understand

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Read agent prompt v2.0 | ⬜ | Key constraint identified: ... |
| Read APS rubric | ⬜ | Target score range: ##-## |
| Reviewed baseline | ⬜ | Baseline APS: ## |
| Checked prior experiments | ⬜ | N experiments reviewed |

### Step 2: Generate Variants

| Variant | Hook Style | Word Count | APS Score | Output Snippet |
|---------|------------|------------|-----------|----------------|
| Baseline | | | | "..." |
| Variant A | | | | "..." |
| Variant B | | | | "..." |
| Variant C | | | | "..." |

### Step 3: Scoring Verification

**Rubric Version Used:** <!-- e.g., v2.0 -->

| Sample | Word Count | Bonuses Applied | Penalties Applied | Final APS | Calculation Verified? |
|--------|------------|-----------------|-------------------|-----------|----------------------|
| Baseline | | -## | +## | ## | ⬜ |
| Variant A | | -## | +## | ## | ⬜ |
| Variant B | | -## | +## | ## | ⬜ |

**Scoring Notes:**
<!-- Document any judgment calls made -->

---

## Post-Flight Checks (AFTER completing)

### Output Verification

| Check | Command/File | Status | Evidence |
|-------|--------------|--------|----------|
| result.json exists | `ls experiments/{id}/result.json` | ⬜ | File size: ## bytes |
| Valid JSON | `jq . experiments/{id}/result.json` | ⬜ | No parse errors |
| Required fields present | See checklist below | ⬜ | All fields found |
| Word counts accurate | Manual count verified | ⬜ | Counts match |

### result.json Required Fields

- [ ] `agent` (string)
- [ ] `experiment` (string)
- [ ] `hypothesis` (string)
- [ ] `date` (string)
- [ ] `baseline` (object with `output`, `word_count`, `aps_score`)
- [ ] `improved` (object with `output`, `word_count`, `aps_score`)
- [ ] `comparison` (object with `improvement`, `percent_better`)
- [ ] `change_made` (string)

### Git Operations

| Operation | Command | Status | Evidence |
|-----------|---------|--------|----------|
| Changes staged | `git add -A` | ⬜ | |
| Commit created | `git commit -m "..."` | ⬜ | Hash: |
| On correct branch | `git log --oneline -1` | ⬜ | Branch: |

---

## Issues & Anomalies

<!-- Document anything unexpected -->

| Issue | Severity | Description | Resolution |
|-------|----------|-------------|------------|
| | | | |

---

## Sign-Off

**Sub-agent certification:**

I certify that:
- [ ] All files were read and understood
- [ ] APS scoring was applied consistently per rubric v2.0
- [ ] Output was validated before commit
- [ ] All changes are on the experiment branch (not main)
- [ ] No system files were modified

**Experiment status:** ⬜ SUCCESS | ⬜ PARTIAL | ⬜ FAILED

**Notes for human review:**
<!-- Anything the human should know -->

---

## Human Review (filled by main agent)

| Check | Status | Notes |
|-------|--------|-------|
| Audit trail complete | ⬜ | |
| Scoring verified | ⬜ | |
| Git history clean | ⬜ | |
| Ready to merge | ⬜ | |

**Reviewer:** _______________ **Date:** _______________
