#!/usr/bin/env python3
"""
Dashboard Data Updater
Used by agents to update their metrics in the dashboard
"""
import json
import os
from datetime import datetime, timezone

DASHBOARD_FILE = "dashboard-data.json"

def load_dashboard_data():
    """Load current dashboard data"""
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, 'r') as f:
            return json.load(f)
    return None

def save_dashboard_data(data):
    """Save dashboard data"""
    with open(DASHBOARD_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_agent(agent_id, tasks=None, errors=None, tokens=None, status=None, workload=None):
    """Update an agent's metrics"""
    data = load_dashboard_data()
    if not data:
        return False
    
    for agent in data['agents']:
        if agent['id'] == agent_id:
            if tasks is not None:
                agent['tasks'] = tasks
            if errors is not None:
                agent['errors'] = errors
            if tokens is not None:
                agent['tokens'] = tokens
            if status is not None:
                agent['status'] = status
            if workload is not None:
                agent['workload'] = workload
            agent['lastActivity'] = datetime.now(timezone.utc).isoformat()
            break
    
    # Update summary
    data['summary']['tasksToday'] = sum(a['tasks'] for a in data['agents'])
    data['summary']['errorsToday'] = sum(a['errors'] for a in data['agents'])
    data['summary']['tokensToday'] = sum(a['tokens'] for a in data['agents'])
    data['lastUpdate'] = datetime.now(timezone.utc).isoformat()
    
    save_dashboard_data(data)
    return True

def add_action_item(agent, text, action="Respond", priority="medium"):
    """Add an action item that needs user attention"""
    data = load_dashboard_data()
    if not data:
        return False
    
    new_id = max([a['id'] for a in data['actionItems']], default=0) + 1
    
    data['actionItems'].append({
        'id': new_id,
        'agent': agent,
        'text': text,
        'action': action,
        'resolved': False,
        'priority': priority,
        'created': datetime.now(timezone.utc).isoformat()
    })
    
    data['lastUpdate'] = datetime.now(timezone.utc).isoformat()
    save_dashboard_data(data)
    return True

def resolve_action_item(item_id):
    """Mark an action item as resolved"""
    data = load_dashboard_data()
    if not data:
        return False
    
    for item in data['actionItems']:
        if item['id'] == item_id:
            item['resolved'] = True
            break
    
    data['lastUpdate'] = datetime.now(timezone.utc).isoformat()
    save_dashboard_data(data)
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python update_dashboard.py update <agent_id> [tasks] [errors] [tokens]")
        print("  python update_dashboard.py action <agent> <text> [priority]")
        print("  python update_dashboard.py resolve <item_id>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "update" and len(sys.argv) >= 3:
        agent_id = sys.argv[2]
        tasks = int(sys.argv[3]) if len(sys.argv) > 3 else None
        errors = int(sys.argv[4]) if len(sys.argv) > 4 else None
        tokens = float(sys.argv[5]) if len(sys.argv) > 5 else None
        update_agent(agent_id, tasks=tasks, errors=errors, tokens=tokens)
        print(f"Updated {agent_id}")
    
    elif cmd == "action" and len(sys.argv) >= 4:
        agent = sys.argv[2]
        text = sys.argv[3]
        priority = sys.argv[4] if len(sys.argv) > 4 else "medium"
        add_action_item(agent, text, priority=priority)
        print(f"Added action item from {agent}")
    
    elif cmd == "resolve" and len(sys.argv) >= 3:
        item_id = int(sys.argv[2])
        resolve_action_item(item_id)
        print(f"Resolved action item {item_id}")
    
    else:
        print("Invalid command")
