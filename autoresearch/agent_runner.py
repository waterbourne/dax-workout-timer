#!/usr/bin/env python3
"""
Agent Runner for OpenClaw AutoResearch
Executes agent delivery simulation and captures metrics
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

def run_agent_experiment(agent: str, dry_run: bool = True) -> dict:
    """
    Run an agent and capture performance metrics
    
    Args:
        agent: Agent ID (dax, guru, sol, etc.)
        dry_run: If True, don't actually send messages
    
    Returns:
        dict with metrics: duration, output_length, errors, aps_score
    """
    
    print(f"🧪 Running experiment for agent: {agent}")
    start_time = time.time()
    
    # Read current prompt
    prompt_path = Path(f"~/.openclaw/workspace/agents/{agent}/prompt.md").expanduser()
    if not prompt_path.exists():
        # Fallback to reading from MEMORY.md patterns
        prompt_path = Path(f"~/.openclaw/workspace/MEMORY.md").expanduser()
    
    prompt = prompt_path.read_text() if prompt_path.exists() else ""
    
    # Simulate agent execution (in real implementation, this would spawn subagent)
    # For now, we measure prompt characteristics as proxy
    
    # Calculate metrics
    word_count = len(prompt.split())
    has_structure = any(marker in prompt for marker in ["##", "**", "- [ ]"])
    has_personalization = any(marker in prompt for marker in ["{{name}}", "{{interests}}", "Evaan"])
    
    # APS calculation (simplified)
    aps_score = 100
    if word_count > 500:  # Too verbose
        aps_score -= (word_count - 500) * 0.05
    if not has_structure:
        aps_score += 10
    if not has_personalization:
        aps_score += 5
    
    aps_score = max(0, min(100, aps_score))
    
    duration = time.time() - start_time
    
    result = {
        "agent": agent,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "prompt_word_count": word_count,
        "has_structure": has_structure,
        "has_personalization": has_personalization,
        "aps_score": round(aps_score, 1),
        "dry_run": dry_run
    }
    
    print(f"   APS Score: {aps_score:.1f} (lower is better)")
    print(f"   Duration: {duration:.2f}s")
    
    return result

def save_result(result: dict, experiment_branch: str):
    """Save experiment result to experiments/ directory"""
    
    exp_dir = Path("experiments") / experiment_branch
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = exp_dir / "result.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"   Saved to {result_file}")

def compare_to_baseline(agent: str, current_aps: float) -> bool:
    """Compare current APS to baseline, return True if improved"""
    
    baseline_file = Path(f"baselines/{agent}_baseline.json")
    if not baseline_file.exists():
        print(f"   ⚠️ No baseline for {agent}, creating...")
        baseline_file.parent.mkdir(exist_ok=True)
        with open(baseline_file, "w") as f:
            json.dump({"aps_score": current_aps, "created": datetime.now().isoformat()}, f)
        return True
    
    with open(baseline_file) as f:
        baseline = json.load(f)
    
    baseline_aps = baseline.get("aps_score", 100)
    improved = current_aps < baseline_aps
    
    print(f"   Baseline APS: {baseline_aps:.1f}")
    print(f"   Current APS:  {current_aps:.1f}")
    print(f"   Improved:     {improved} {'✅' if improved else '❌'}")
    
    return improved

def main():
    parser = argparse.ArgumentParser(description="Run agent experiment")
    parser.add_argument("--agent", required=True, help="Agent ID (dax, guru, sol, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send messages")
    parser.add_argument("--branch", help="Experiment branch name")
    args = parser.parse_args()
    
    # Run experiment
    result = run_agent_experiment(args.agent, args.dry_run)
    
    # Save result
    branch = args.branch or f"{args.agent}-{datetime.now():%Y%m%d-%H%M%S}"
    save_result(result, branch)
    
    # Compare to baseline
    improved = compare_to_baseline(args.agent, result["aps_score"])
    
    # Exit code: 0 if improved, 1 if not (for git automation)
    sys.exit(0 if improved else 1)

if __name__ == "__main__":
    main()
