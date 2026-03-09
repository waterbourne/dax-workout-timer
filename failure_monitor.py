#!/usr/bin/env python3
"""
Failure Monitor - Watch for consecutive agent failures and trigger System Debugger
"""

import subprocess
import json
import sys

def check_agent_failures():
    """Check cron jobs for consecutive failures"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse table output
        failed_agents = []
        lines = result.stdout.split("\n")
        
        for line in lines[1:]:  # Skip header
            if "error" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    job_id = parts[0]
                    # Extract job name (between ID and schedule)
                    name_parts = []
                    for i, part in enumerate(parts[1:], 1):
                        if part in ["cron", "every"]:
                            break
                        name_parts.append(part)
                    job_name = " ".join(name_parts) if name_parts else "Unknown"
                    
                    failed_agents.append({
                        "name": job_name,
                        "jobId": job_id,
                        "errors": 1,  # Table shows status, not exact count
                        "lastError": "Status shows error"
                    })
        
        return failed_agents
        
    except Exception as e:
        print(f"Error checking agents: {e}")
        return []

def trigger_debugger(agents):
    """Trigger System Debugger for failed agents"""
    try:
        # Run debugger immediately
        result = subprocess.run(
            ["openclaw", "cron", "run", "eb502bd5-1de7-4f99-8397-5b994e8ddfea"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"Triggered System Debugger for {len(agents)} failed agent(s)")
        return result.returncode == 0
        
    except Exception as e:
        print(f"Failed to trigger debugger: {e}")
        return False

if __name__ == "__main__":
    failed = check_agent_failures()
    
    if failed:
        print(f"⚠️  Detected {len(failed)} agent(s) with 3+ consecutive failures:")
        for agent in failed:
            print(f"  - {agent['name']}: {agent['errors']} errors ({agent['lastError'][:50]}...)")
        
        if trigger_debugger(failed):
            print("✅ System Debugger triggered")
            sys.exit(0)
        else:
            print("❌ Failed to trigger System Debugger")
            sys.exit(1)
    else:
        print("✅ All agents healthy (no 3+ consecutive failures)")
        sys.exit(0)
