# OpenClaw Agent Dashboard

A real-time, interactive dashboard for monitoring all your OpenClaw agents.

## Features

- **Live Agent Status**: See which agents are active, idle, or have errors
- **Workload Monitoring**: Visual workload bars with color-coded stress levels
- **Action Items**: Clickable items that need your attention
- **Auto-Refresh**: Updates every 30 seconds
- **Token Tracking**: Monitor API usage across all agents

## How to Use

### Opening the Dashboard

**Option 1: Quick Start (with live updates)**

Run the simple HTTP server:

```bash
cd ~/.openclaw/workspace
python3 dashboard_server.py
```

Then open: **http://localhost:8080/dashboard.html**

**Option 2: Direct file (static view only)**

If you just want to view without live updates:

```bash
open dashboard.html
```

*Note: Live data refresh won't work when opening directly due to browser security. Use Option 1 for full functionality.*

### Action Items

The **"Needs Your Attention"** section at the top shows items agents need from you:

- Click the action button to mark items as resolved
- High priority items appear first
- Items are color-coded by agent

### Understanding Workload

Each agent card shows a workload bar:
- 🟢 **Green (0-30%)**: Low stress, healthy
- 🟡 **Yellow (30-70%)**: Moderate load, monitor
- 🔴 **Red (70%+)**: High stress, consider redistribution

### Status Indicators

- **Active**: Agent is currently working
- **Idle**: Agent waiting for next scheduled task
- **Error**: Agent encountered issues (check action items)

## Data Updates

The dashboard reads from `dashboard-data.json`. To update with real data:

1. The main agent writes current metrics to `dashboard-data.json`
2. Dashboard auto-refreshes every 30 seconds
3. Or press Cmd+R (Ctrl+R) to refresh manually

## Agent Roster

| Agent | Role | Schedule | For |
|-------|------|----------|-----|
| 💪 Dax | Personal Trainer | 4:30 AM | Workouts (Aditya daily, Natasha Mon/Wed/Fri) |
| 🧘 Guru | Spirituality Guide | 6:00 AM | Morning meditation & reflection |
| 📚 Sol | Tutor (Academic) | 7:00 AM | Evaan's math, science, English |
| 🏛️ Atlas | Tutor (Philosophy) | 5:15 PM | Evaan's history, big questions |
| 👨‍🍳 Raju | Head Chef | 7:30 PM | Dinner planning, shopping lists |
| 📅 Calendar Monitor | Departure Alerts | Every 15 min | Travel time calculations |
| 🔍 Error Review | EOD Improvement | 10:30 PM | Daily error analysis |
| 👁️ Bob | The Auditor | Every hour | Quality assurance |

## Communicating with Agents

When you resolve an action item in the dashboard:

1. The dashboard logs your response
2. The main agent checks `dashboard-data.json` for updates
3. Agents receive your feedback on their next run

Or simply message the main agent directly with responses.

## Customization

Edit `dashboard.html` to:
- Change refresh interval (default: 30 seconds)
- Add new agents
- Modify workload thresholds
- Change color scheme

## Troubleshooting

**Dashboard shows old data:**
- Wait 30 seconds for auto-refresh
- Or refresh the page manually

**Action items not updating:**
- Check that `dashboard-data.json` exists and is readable
- Verify JSON syntax is valid

**Colors look wrong:**
- Use a modern browser (Chrome, Firefox, Safari, Edge)
- Enable JavaScript

## Files

- `dashboard.html` - The main dashboard interface
- `dashboard-data.json` - Live data feed (updated by agents)
- `README-dashboard.md` - This file
