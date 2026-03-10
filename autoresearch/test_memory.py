#!/usr/bin/env python3
"""
Quick Memory Test for Autoresearch Sub-Agents
Validates that context propagates correctly between runs
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def test_file_propagation():
    """Test 1: Can we write and read files?"""
    print("\n🧪 Test 1: File Propagation")
    
    test_file = Path("/Users/sirius_bot/.openclaw/workspace/autoresearch/test-runs/.memory_test")
    test_data = {"timestamp": datetime.now().isoformat(), "test_id": "001"}
    
    try:
        # Write
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        # Read
        with open(test_file) as f:
            read_data = json.load(f)
        
        # Validate
        if read_data["test_id"] == test_data["test_id"]:
            print("   ✅ File write/read works")
            return True
        else:
            print("   ❌ Data mismatch")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()

def test_json_validation():
    """Test 2: Can we validate experiment JSONs?"""
    print("\n🧪 Test 2: JSON Validation")
    
    experiments_dir = Path("/Users/sirius_bot/.openclaw/workspace/autoresearch/experiments")
    if not experiments_dir.exists():
        print("   ⚠️  No experiments directory")
        return True  # Not a failure, just no data
    
    exp_dirs = [d for d in experiments_dir.iterdir() if d.is_dir()]
    if not exp_dirs:
        print("   ⚠️  No experiments to validate")
        return True
    
    valid_count = 0
    invalid_count = 0
    
    for exp_dir in exp_dirs:
        result_file = exp_dir / "result.json"
        if not result_file.exists():
            continue
        
        try:
            with open(result_file) as f:
                data = json.load(f)
            
            # Check required fields
            required = ["agent", "experiment", "date"]
            missing = [f for f in required if f not in data]
            
            if missing:
                print(f"   ⚠️  {exp_dir.name}: Missing fields {missing}")
                invalid_count += 1
            else:
                valid_count += 1
                
        except json.JSONDecodeError as e:
            print(f"   ❌ {exp_dir.name}: Invalid JSON - {e}")
            invalid_count += 1
    
    if valid_count > 0 and invalid_count == 0:
        print(f"   ✅ All {valid_count} experiment JSONs valid")
        return True
    elif invalid_count > 0:
        print(f"   ❌ {invalid_count} invalid, {valid_count} valid")
        return False
    else:
        print("   ⚠️  No experiment files found")
        return True

def test_context_cache():
    """Test 3: Does context cache exist and have valid structure?"""
    print("\n🧪 Test 3: Context Cache")
    
    cache_file = Path("/Users/sirius_bot/.openclaw/workspace/shared/context-cache.json")
    
    if not cache_file.exists():
        print("   ⚠️  No context cache found (optional)")
        return True
    
    try:
        with open(cache_file) as f:
            data = json.load(f)
        
        # Check structure
        if "version" in data and "cross_agent_context" in data:
            print("   ✅ Context cache structure valid")
            return True
        else:
            print("   ⚠️  Context cache missing expected fields")
            return True  # Warning, not failure
            
    except json.JSONDecodeError as e:
        print(f"   ❌ Context cache invalid JSON: {e}")
        return False

def test_agent_prompts():
    """Test 4: Do agent prompts exist and have required sections?"""
    print("\n🧪 Test 4: Agent Prompts")
    
    agents_dir = Path("/Users/sirius_bot/.openclaw/workspace/autoresearch/agents")
    
    if not agents_dir.exists():
        print("   ❌ No agents directory")
        return False
    
    agents = [d for d in agents_dir.iterdir() if d.is_dir()]
    if not agents:
        print("   ❌ No agents found")
        return False
    
    all_valid = True
    for agent_dir in agents:
        prompt_file = agent_dir / "prompt.md"
        if not prompt_file.exists():
            print(f"   ❌ {agent_dir.name}: No prompt.md")
            all_valid = False
            continue
        
        content = prompt_file.read_text()
        
        # Check for v2.0 markers
        has_version = "v2.0" in content or "AutoResearch Learnings" in content
        has_format = "Output Format" in content or "```" in content
        
        if has_version and has_format:
            print(f"   ✅ {agent_dir.name}: Valid prompt")
        else:
            print(f"   ⚠️  {agent_dir.name}: Missing v2.0 markers")
    
    return all_valid

def main():
    print("\n🔍 Autoresearch Memory Test")
    print("=" * 40)
    
    tests = [
        ("File Propagation", test_file_propagation),
        ("JSON Validation", test_json_validation),
        ("Context Cache", test_context_cache),
        ("Agent Prompts", test_agent_prompts),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            results.append((name, False))
    
    # Report
    print("\n" + "=" * 40)
    print("📊 Results")
    print("=" * 40)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "✅" if p else "❌"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ Memory system working — safe to run experiments")
        return 0
    else:
        print("\n⚠️  Some tests failed — review before experiments")
        return 1

if __name__ == "__main__":
    sys.exit(main())
