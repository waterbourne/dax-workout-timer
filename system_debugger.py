#!/usr/bin/env python3
"""
System Debugger Agent - Analyze logs and diagnose issues
Triggered when agents fail consecutively or on demand
"""

import json
import re
from datetime import datetime, timedelta
import subprocess

def check_recent_failures():
    """Check for patterns in recent agent failures"""
    print("=== System Debugger Report ===")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check cron job status
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print("✅ Gateway cron system responsive")
    except Exception as e:
        print(f"❌ Gateway error: {e}")
        return
    
    # Read error log if exists
    try:
        with open("/Users/sirius_bot/.openclaw/workspace/memory/error-log.md", "r") as f:
            content = f.read()
            
        # Find recent errors (last 7 days)
        recent_errors = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if "##" in line and "2026-" in line:
                # Parse date
                try:
                    date_str = line.replace("##", "").strip().split()[0]
                    error_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if datetime.now() - error_date < timedelta(days=7):
                        recent_errors.append({
                            "date": date_str,
                            "context": "\n".join(lines[i:i+20])
                        })
                except:
                    pass
        
        print(f"📊 Recent errors (last 7 days): {len(recent_errors)}")
        
        # Look for patterns
        patterns = {
            "timeout": len([e for e in recent_errors if "timeout" in e["context"].lower()]),
            "delivery": len([e for e in recent_errors if "delivery" in e["context"].lower()]),
            "model": len([e for e in recent_errors if "model" in e["context"].lower()]),
            "calendar": len([e for e in recent_errors if "calendar" in e["context"].lower()])
        }
        
        print("\n🔍 Error Patterns:")
        for pattern, count in patterns.items():
            if count > 0:
                print(f"  - {pattern.capitalize()} issues: {count}")
                
    except FileNotFoundError:
        print("ℹ️  No error log found")
    except Exception as e:
        print(f"⚠️  Error reading log: {e}")
    
    # Check system resources
    print("\n💻 System Status:")
    try:
        # Check disk space
        result = subprocess.run(
            ["df", "-h", "/Users/sirius_bot/.openclaw"],
            capture_output=True,
            text=True
        )
        print(f"  Disk: {result.stdout.split()[11] if len(result.stdout.split()) > 11 else 'N/A'} used")
    except:
        print("  Disk: Unable to check")
    
    print("\n=== End Report ===")

if __name__ == "__main__":
    check_recent_failures()
