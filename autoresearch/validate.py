#!/usr/bin/env python3
"""
Autoresearch Experiment Validator
Checks experiment integrity, validates JSON, verifies scoring
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class ExperimentValidator:
    def __init__(self, base_path: str = "/Users/sirius_bot/.openclaw/workspace/autoresearch"):
        self.base_path = Path(base_path)
        self.errors = []
        self.warnings = []
    
    def log_error(self, msg: str):
        self.errors.append(f"❌ {msg}")
    
    def log_warning(self, msg: str):
        self.warnings.append(f"⚠️  {msg}")
    
    def log_success(self, msg: str):
        print(f"✅ {msg}")
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("\n🔍 Autoresearch Experiment Validator\n")
        print("=" * 50)
        
        # Check 1: Directory structure
        self._validate_directory_structure()
        
        # Check 2: Baseline files
        self._validate_baselines()
        
        # Check 3: Experiment results
        self._validate_experiments()
        
        # Check 4: Agent prompts
        self._validate_agent_prompts()
        
        # Check 5: Git state
        self._validate_git_state()
        
        # Report
        return self._print_report()
    
    def _validate_directory_structure(self):
        """Verify required directories exist"""
        print("\n📁 Checking directory structure...")
        
        required_dirs = [
            "agents",
            "baselines", 
            "experiments",
            "test-runs"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                self.log_success(f"Directory exists: {dir_name}/")
            else:
                self.log_error(f"Missing directory: {dir_name}/")
                # Create it
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   Created: {dir_path}")
    
    def _validate_baselines(self):
        """Check baseline files are valid"""
        print("\n📊 Checking baselines...")
        
        baseline_dir = self.base_path / "baselines"
        if not baseline_dir.exists():
            self.log_error("baselines/ directory missing")
            return
        
        baselines = list(baseline_dir.glob("*_baseline.json"))
        if not baselines:
            self.log_warning("No baseline files found")
            return
        
        for baseline_file in baselines:
            try:
                with open(baseline_file) as f:
                    data = json.load(f)
                
                # Check required fields
                required = ["agent", "aps_score", "created"]
                for field in required:
                    if field not in data:
                        self.log_error(f"{baseline_file.name}: Missing field '{field}'")
                
                # Validate APS range
                aps = data.get("aps_score", 0)
                if not (0 <= aps <= 150):
                    self.log_warning(f"{baseline_file.name}: Unusual APS score: {aps}")
                
                self.log_success(f"Baseline valid: {baseline_file.name} (APS: {aps})")
                
            except json.JSONDecodeError as e:
                self.log_error(f"{baseline_file.name}: Invalid JSON - {e}")
            except Exception as e:
                self.log_error(f"{baseline_file.name}: Error reading - {e}")
    
    def _validate_experiments(self):
        """Check experiment result files"""
        print("\n🧪 Checking experiments...")
        
        experiments_dir = self.base_path / "experiments"
        if not experiments_dir.exists():
            self.log_error("experiments/ directory missing")
            return
        
        experiment_dirs = [d for d in experiments_dir.iterdir() if d.is_dir()]
        if not experiment_dirs:
            self.log_warning("No experiment directories found")
            return
        
        for exp_dir in experiment_dirs:
            result_file = exp_dir / "result.json"
            
            if not result_file.exists():
                self.log_error(f"{exp_dir.name}: Missing result.json")
                continue
            
            try:
                with open(result_file) as f:
                    data = json.load(f)
                
                # Check required fields
                required = ["agent", "experiment", "hypothesis", "date"]
                for field in required:
                    if field not in data:
                        self.log_error(f"{exp_dir.name}: Missing field '{field}'")
                
                # Validate baseline vs improved comparison
                if "baseline" in data and "improved" in data:
                    baseline_aps = data["baseline"].get("aps_score", 0)
                    improved_aps = data["improved"].get("aps_score", 0)
                    
                    if improved_aps >= baseline_aps:
                        self.log_warning(
                            f"{exp_dir.name}: No improvement "
                            f"(baseline: {baseline_aps}, improved: {improved_aps})"
                        )
                    else:
                        improvement = baseline_aps - improved_aps
                        self.log_success(
                            f"{exp_dir.name}: APS improved {baseline_aps} → {improved_aps} "
                            f"(-{improvement})"
                        )
                
                # Check word counts are reasonable
                if "baseline" in data:
                    wc = data["baseline"].get("word_count", 0)
                    if wc > 200:
                        self.log_warning(f"{exp_dir.name}: Baseline word count high ({wc})")
                
                if "improved" in data:
                    wc = data["improved"].get("word_count", 0)
                    if wc > 200:
                        self.log_warning(f"{exp_dir.name}: Improved word count high ({wc})")
                
            except json.JSONDecodeError as e:
                self.log_error(f"{exp_dir.name}: Invalid JSON - {e}")
            except Exception as e:
                self.log_error(f"{exp_dir.name}: Error - {e}")
    
    def _validate_agent_prompts(self):
        """Check agent prompts have required sections"""
        print("\n📝 Checking agent prompts...")
        
        agents_dir = self.base_path / "agents"
        if not agents_dir.exists():
            self.log_error("agents/ directory missing")
            return
        
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            
            prompt_file = agent_dir / "prompt.md"
            if not prompt_file.exists():
                self.log_error(f"{agent_dir.name}: Missing prompt.md")
                continue
            
            try:
                content = prompt_file.read_text()
                
                # Check for v2.0 markers
                checks = [
                    ("Version marker", "v2.0" in content or "AutoResearch Learnings" in content),
                    ("APS scoring section", "APS" in content),
                    ("Output format", "Output Format" in content or "```" in content),
                    ("Rules section", "Rules" in content),
                ]
                
                all_good = True
                for check_name, passed in checks:
                    if not passed:
                        self.log_warning(f"{agent_dir.name}: Missing {check_name}")
                        all_good = False
                
                if all_good:
                    self.log_success(f"Prompt valid: {agent_dir.name}/prompt.md")
                
            except Exception as e:
                self.log_error(f"{agent_dir.name}: Error reading prompt - {e}")
    
    def _validate_git_state(self):
        """Check git repository state"""
        print("\n🌿 Checking git state...")
        
        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.base_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log_error("Not a git repository")
                return
            
            # Check current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.base_path,
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip()
            
            if current_branch == "main":
                self.log_success(f"On main branch: {current_branch}")
            elif current_branch.startswith("experiments/"):
                self.log_warning(f"On experiment branch: {current_branch}")
            else:
                self.log_warning(f"On branch: {current_branch}")
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.base_path,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                self.log_warning("Uncommitted changes detected")
                for line in result.stdout.strip().split("\n")[:5]:
                    print(f"   {line}")
            else:
                self.log_success("Working tree clean")
            
            # Check recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=self.base_path,
                capture_output=True,
                text=True
            )
            
            print("\n   Recent commits:")
            for line in result.stdout.strip().split("\n")[:3]:
                print(f"   {line}")
                
        except Exception as e:
            self.log_error(f"Git check failed: {e}")
    
    def _print_report(self) -> bool:
        """Print final report"""
        print("\n" + "=" * 50)
        print("📋 VALIDATION REPORT")
        print("=" * 50)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All checks passed!")
            return True
        elif not self.errors:
            print(f"\n✅ No errors, {len(self.warnings)} warnings")
            return True
        else:
            print(f"\n❌ {len(self.errors)} errors found")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate autoresearch experiments")
    parser.add_argument(
        "--path",
        default="/Users/sirius_bot/.openclaw/workspace/autoresearch",
        help="Path to autoresearch directory"
    )
    args = parser.parse_args()
    
    validator = ExperimentValidator(args.path)
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
