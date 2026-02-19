# ARCHITECTURE.md - OpenClaw Multi-Agent System Architecture

**Version:** 2.0  
**Date:** 2026-02-19  
**Status:** Infrastructure Overhaul - Phase 1  

---

## Executive Summary

The OpenClaw system is evolving from 5 independent vertical agents (Dax, Guru, Sol, Atlas, Raju) to a coordinated multi-agent platform with centralized orchestration, shared memory, and resilient delivery.

### Current Pain Points (Solved by This Architecture)
1. **Delivery Conflicts** - Multiple agents hitting Telegram simultaneously
2. **Timeout Issues** - 90-120s insufficient for complex generation + delivery
3. **Context Silos** - Agents unaware of each other's work and user state
4. **No Fallback** - Telegram failures = silent message loss
5. **Rush Hour** - 6-7 AM cluster causing resource contention
6. **Silent Failures** - Errors accumulating without proactive detection

---

## Core Architecture Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Schedule  │  │   Router    │  │   State     │  │  Health Monitor │ │
│  │   Manager   │  │             │  │   Manager   │  │                 │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────┘ │
└─────────┼────────────────┼────────────────┼─────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT POOL (Verticals)                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐ │
│  │  Dax   │ │  Guru  │ │  Sol   │ │  Atlas │ │  Raju  │ │   Bob      │ │
│  │ 💪     │ │ 🧘     │ │ 📚     │ │ 🏛️    │ │ 👨‍🍳    │ │ 👁️       │ │
│  │Fitness │ │Spirit  │ │Academic│ │Philosophy│ │ Chef  │ │ Auditor   │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SHARED MEMORY LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  User State │  │   Agent     │  │   Context   │  │   Delivery      │ │
│  │   Store     │  │   Memory    │  │   Cache     │  │   Queue         │ │
│  │             │  │   Registry  │  │             │  │                 │ │
│  │ • Travel    │  │ • Capabilities│ │ • Cross-ref │  │ • Batched       │ │
│  │ • Work hrs  │  │ • Schedules │  │ • History   │  │ • Prioritized   │ │
│  │ • Family    │  │ • Status    │  │ • Preferences│ │ • Retry state   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DELIVERY PIPELINE                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Channel Router (Priority: Telegram → iMessage → WhatsApp)      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │ Telegram │  │BlueBubbles│  │ WhatsApp │  │   Dead Letter    │ │   │
│  │  │ Primary  │→ │iMessage  │→ │Fallback │→ │    Queue         │ │   │
│  │  │  4000c   │  │  No limit│  │  Backup  │  │ (Manual Review)  │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Orchestration Layer

### 1.1 Schedule Manager

**Problem:** Current cron jobs run independently with no coordination, causing 6-7 AM rush hour.

**Solution:** Time-sliced scheduling with workload balancing.

```yaml
# orchestrator/schedule.yaml
scheduling_rules:
  # Spread morning load across 3.5 hours instead of 2.5
  morning_window:
    start: "04:00"
    end: "08:00"
    slot_duration_minutes: 45  # Each agent gets a dedicated slot
    
  agents:
    dax:
      time: "04:30"  # Unchanged - early bird
      priority: high
      max_runtime_seconds: 180  # Increased from 90
      
    guru:
      time: "05:15"  # Moved earlier (was 06:00)
      priority: medium
      max_runtime_seconds: 120
      
    sol:
      time: "07:00"  # Unchanged
      priority: high
      max_runtime_seconds: 180  # Academic content needs time
      dependencies:
        - guru  # Don't run until Guru completes
      
    atlas:
      time: "17:15"  # Slightly later (was 17:15)
      priority: medium
      max_runtime_seconds: 150
      
    raju:
      time: "19:00"  # Earlier (was 19:30)
      priority: medium
      max_runtime_seconds: 180
      # Travel-aware: Skip if departing tomorrow
      skip_conditions:
        - user_state.travel.departing_within_hours: 24

  # Sequential execution within time windows
  execution_mode: sequential  # NOT parallel - prevents resource contention
  
  # Global rate limiting
  rate_limits:
    telegram_per_minute: 10
    telegram_per_hour: 50
    global_tokens_per_hour: 500000
```

### 1.2 Router

The Router determines which agent should handle a request and manages agent-to-agent handoffs.

```yaml
# orchestrator/routing-rules.yaml
routing:
  # Intent-based routing
  intents:
    fitness:
      keywords: ["workout", "exercise", "gym", "training", "cardio", "weights"]
      agent: dax
      
    spirituality:
      keywords: ["meditation", "mindfulness", "stoic", "zen", "contemplation", "philosophy life"]
      agent: guru
      
    academic_tutoring:
      keywords: ["math", "science", "homework", "school", "phonics", "evaan learning"]
      agent: sol
      
    philosophy_history:
      keywords: ["history", "ancient", "civilization", "story", "big questions", "evaan story"]
      agent: atlas
      
    cooking:
      keywords: ["dinner", "recipe", "cook", "food", "meal", "shopping list", "ingredients"]
      agent: raju

  # Cross-agent context sharing
  context_propagation:
    # When Raju plans dinner, Dax knows not to schedule evening workout
    - trigger: raju.dinner_plan_created
      notify: [dax]
      data: [meal_time, complexity]
      
    # When travel detected, all agents get travel context
    - trigger: calendar.travel_detected
      notify: [dax, guru, sol, atlas, raju]
      data: [destination, departure_time, return_time]
      
    # When Sol teaches a topic, Atlas can reference it
    - trigger: sol.topic_covered
      notify: [atlas]
      data: [subject, key_concepts]
```

### 1.3 State Manager

Centralized user state that all agents can read (and some can write).

```json
// orchestrator/state.json
{
  "user_state": {
    "location": {
      "current": "San Francisco, CA",
      "timezone": "America/Los_Angeles",
      "home": "San Francisco, CA"
    },
    "travel": {
      "status": "home",  // home, departing_soon, traveling, returning
      "next_trip": {
        "destination": "Carmel Valley Ranch",
        "departure": "2026-02-19T10:00:00-08:00",
        "return": "2026-02-22T18:00:00-08:00",
        "departing_within_hours": 2
      },
      "travel_history": [...]
    },
    "work_hours": {
      "deep_work": "06:00-10:00",
      "meetings": "10:00-17:00",
      "current_focus": "family time"  // Overrides work hours
    },
    "family": {
      "members": [
        {"name": "Aditya", "role": "primary_user", "workout_days": "daily"},
        {"name": "Natasha", "role": "wife", "workout_days": ["Mon", "Wed", "Fri"]},
        {"name": "Evaan", "role": "child", "age": 7, "grade": 2}
      ],
      "events": {
        "upcoming_birthdays": [],
        "school_calendar": "..."
      }
    },
    "preferences": {
      "delivery_channel": "telegram",  // telegram, imessage, whatsapp
      "quiet_hours": "22:00-06:00",
      "do_not_disturb": false
    }
  },
  "system_state": {
    "last_agent_run": {
      "agent": "dax",
      "timestamp": "2026-02-19T04:30:00-08:00",
      "status": "success"
    },
    "next_scheduled_run": {
      "agent": "guru",
      "timestamp": "2026-02-19T05:15:00-08:00"
    },
    "health": {
      "status": "healthy",
      "last_check": "2026-02-19T08:26:00-08:00",
      "alerts": []
    }
  }
}
```

---

## 2. Shared Memory Schema

### 2.1 Memory Hierarchy

```
memory/
├── orchestrator/
│   ├── state.json              # Real-time user/system state
│   ├── schedule.yaml           # Scheduling configuration
│   ├── routing-rules.yaml      # Intent routing
│   └── delivery-queue.json     # Pending deliveries
├── shared/
│   ├── agent-registry.json     # All agent capabilities & status
│   ├── context-cache.json      # Cross-agent context
│   └── delivery-log.json       # All deliveries with status
├── daily/
│   └── YYYY-MM-DD.md           # Daily logs (existing)
└── archive/
    └── (rotated files)
```

### 2.2 Agent Registry

```json
// shared/agent-registry.json
{
  "agents": {
    "dax": {
      "name": "Dax",
      "role": "Personal Trainer",
      "emoji": "💪",
      "capabilities": ["workout_creation", "fitness_tracking", "progression_planning"],
      "schedule": "04:30 AM daily",
      "priority": "high",
      "timeouts": {"generation": 120, "delivery": 30},
      "dependencies": [],
      "notifications": ["dinner_time"],  // Context Dax receives
      "status": "idle",
      "health": {
        "last_run": "2026-02-19T04:30:00-08:00",
        "success_rate_7d": 0.98,
        "avg_runtime_seconds": 45
      }
    },
    "guru": {
      "name": "Guru",
      "role": "Spirituality Guide",
      "emoji": "🧘",
      "capabilities": ["meditation_guidance", "stoic_reflection", "wisdom_teaching"],
      "schedule": "05:15 AM daily",
      "priority": "medium",
      "timeouts": {"generation": 90, "delivery": 30},
      "dependencies": [],
      "notifications": [],
      "status": "idle",
      "health": {
        "last_run": "2026-02-19T05:15:00-08:00",
        "success_rate_7d": 0.95,
        "avg_runtime_seconds": 38
      }
    },
    "sol": {
      "name": "Sol",
      "role": "Academic Tutor",
      "emoji": "📚",
      "capabilities": ["math_tutoring", "science_tutoring", "phonics", "english"],
      "schedule": "07:00 AM daily",
      "priority": "high",
      "timeouts": {"generation": 150, "delivery": 30},
      "dependencies": ["guru"],
      "notifications": [],
      "status": "idle",
      "health": {
        "last_run": "2026-02-19T07:00:00-08:00",
        "success_rate_7d": 0.88,
        "avg_runtime_seconds": 95,
        "issues": ["timeout_errors"]
      }
    },
    "atlas": {
      "name": "Atlas",
      "role": "Philosophy Tutor",
      "emoji": "🏛️",
      "capabilities": ["history_teaching", "storytelling", "big_questions"],
      "schedule": "17:15 PM daily",
      "priority": "medium",
      "timeouts": {"generation": 120, "delivery": 30},
      "dependencies": [],
      "notifications": ["sol.topics"],
      "status": "idle",
      "health": {
        "last_run": "2026-02-19T05:15:00-08:00",
        "success_rate_7d": 0.91,
        "avg_runtime_seconds": 62
      }
    },
    "raju": {
      "name": "Raju",
      "role": "Head Chef",
      "emoji": "👨‍🍳",
      "capabilities": ["meal_planning", "recipe_creation", "shopping_lists", "travel_food"],
      "schedule": "19:00 PM daily",
      "priority": "medium",
      "timeouts": {"generation": 150, "delivery": 30},
      "dependencies": [],
      "notifications": ["travel.planned"],
      "status": "disabled",  // Travel mode - disabled
      "health": {
        "last_run": "2026-02-18T19:30:00-08:00",
        "success_rate_7d": 0.96,
        "avg_runtime_seconds": 87
      },
      "skip_reason": "User traveling to Carmel Valley Ranch"
    },
    "bob": {
      "name": "Bob",
      "role": "The Auditor",
      "emoji": "👁️",
      "capabilities": ["quality_assurance", "pattern_detection", "process_improvement"],
      "schedule": "Every hour",
      "priority": "high",
      "timeouts": {"generation": 120, "delivery": 30},
      "dependencies": [],
      "notifications": ["all.agent_outputs"],
      "status": "active",
      "health": {
        "last_run": "2026-02-19T08:00:00-08:00",
        "success_rate_7d": 0.94,
        "avg_runtime_seconds": 45
      }
    }
  }
}
```

### 2.3 Context Cache

```json
// shared/context-cache.json
{
  "cross_agent_context": {
    "recent_topics": {
      "sol": {
        "last_7_days": [
          {"date": "2026-02-19", "topic": "multiplication_patterns", "key_concepts": ["arrays", "skip_counting"]},
          {"date": "2026-02-18", "topic": "weather_systems", "key_concepts": ["precipitation", "cloud_formation"]}
        ]
      },
      "atlas": {
        "last_7_days": [
          {"date": "2026-02-18", "topic": "ancient_egypt", "key_concepts": ["pharaohs", "pyramids", "hieroglyphics"]}
        ]
      }
    },
    "pending_references": [
      {
        "from": "sol",
        "to": "atlas",
        "reference": "Evaan learned about measurement in math - could connect to ancient measurement systems",
        "expires": "2026-02-26"
      }
    ],
    "user_context": {
      "current_focus": "preparing_for_trip",
      "energy_level": "high",
      "family_dynamics": "normal"
    }
  }
}
```

---

## 3. Delivery Pipeline

### 3.1 Queue-Based Delivery

Instead of agents sending directly, they submit to a queue:

```json
// orchestrator/delivery-queue.json
{
  "queue": [
    {
      "id": "del_001",
      "agent": "dax",
      "content": "## 💪 Morning Workout...",
      "priority": "high",
      "channels": ["telegram", "imessage"],
      "target": "8584092724",
      "max_length": 4000,
      "submitted_at": "2026-02-19T04:30:15-08:00",
      "status": "pending",
      "attempts": 0,
      "scheduled_delivery": "2026-02-19T04:30:00-08:00"
    }
  ],
  "processing": {
    "batch_size": 3,
    "interval_seconds": 30,
    "current_batch": []
  },
  "rate_limiting": {
    "telegram": {
      "messages_per_minute": 10,
      "messages_per_hour": 50,
      "current_minute_count": 0,
      "current_hour_count": 2
    }
  }
}
```

### 3.2 Channel Router with Fallback

```yaml
# orchestrator/channel-router.yaml
channels:
  telegram:
    priority: 1
    enabled: true
    limits:
      message_length: 4000
      messages_per_minute: 10
      messages_per_hour: 50
    config:
      target: "8584092724"
      timeout_seconds: 30
      retry_policy:
        max_retries: 3
        backoff: exponential  # 1s, 2s, 4s
    
  imessage:
    priority: 2
    enabled: true
    limits:
      message_length: 10000  # No practical limit
      messages_per_minute: 20
    config:
      target: "+1415XXXXXXX"  # Aditya's number
      timeout_seconds: 30
      retry_policy:
        max_retries: 2
        backoff: linear
    
  whatsapp:
    priority: 3
    enabled: false  # Not currently configured
    limits:
      message_length: 4096
    config:
      target: null
      note: "Configure in gateway if needed"

routing_logic:
  # Try primary first
  default: telegram
  
  # Fallback sequence
  on_failure:
    - try: telegram
      retries: 3
    - try: imessage
      retries: 2
    - action: queue_to_dead_letter
      alert: true
      
  # Message size routing
  oversized_messages:
    threshold: 4000
    default: imessage
    chunk_if_no_alternative: true
    
  # User preference override
  user_preference:
    if_set: use_specified_channel
    if_unset: follow_default_routing
```

### 3.3 Retry Logic

```python
# Pseudocode for delivery retry
def deliver_with_retry(message, config):
    channels = config.channels_in_priority_order
    
    for channel in channels:
        retry_config = channel.retry_policy
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                result = attempt_delivery(message, channel)
                if result.success:
                    log_success(message.id, channel, attempt)
                    return DeliveryResult.success(channel)
                    
            except RateLimitError:
                wait(retry_config.backoff.delay(attempt))
                continue
                
            except TimeoutError:
                if attempt < retry_config.max_retries:
                    wait(retry_config.backoff.delay(attempt))
                    continue
                break  # Try next channel
                
            except PermanentError:
                break  # Try next channel
    
    # All channels exhausted
    queue_to_dead_letter(message)
    alert_admin(message)
    return DeliveryResult.failed()
```

---

## 4. Health Monitoring

### 4.1 Proactive Health Checks

```yaml
# orchestrator/health-monitor.yaml
health_checks:
  # Agent health
  agents:
    interval: 300  # 5 minutes
    checks:
      - check: last_run_within_expected
        threshold_minutes: 60
      - check: error_rate
        threshold: 0.10  # 10% errors in last 24h
      - check: timeout_rate
        threshold: 0.05  # 5% timeouts
      - check: avg_runtime_increase
        threshold: 50%  # Alert if 50% slower than baseline
        
  # Delivery health
  delivery:
    interval: 60  # 1 minute
    checks:
      - check: queue_depth
        warning: 5
        critical: 10
      - check: delivery_failure_rate
        threshold: 0.05
      - check: fallback_usage_rate
        threshold: 0.10  # Alert if >10% using fallback
        
  # System health
  system:
    interval: 600  # 10 minutes
    checks:
      - check: token_usage_per_hour
        warning: 400000
        critical: 500000
      - check: disk_space
        warning: 80%
        critical: 90%
      - check: gateway_connectivity

alerting:
  channels:
    - telegram: "8584092724"  # Primary
    - imessage: "+1415XXXXXXX"  # Fallback for critical
    
  severity_levels:
    info:
      - log_only: true
    warning:
      - log: true
      - telegram: true
      - suppress_hours: [22, 23, 0, 1, 2, 3, 4, 5, 6]  # Quiet hours
    critical:
      - log: true
      - telegram: true
      - imessage: true  # Override quiet hours
```

### 4.2 Self-Healing Actions

```yaml
# orchestrator/self-healing.yaml
auto_remediation:
  cron_job_failed:
    action: retry_immediately
    if_still_failing: recreate_job
    if_recurring: escalate_to_admin
    
  timeout_errors:
    action: increase_timeout_25%
    max_timeout: 300  # Cap at 5 minutes
    if_persisting: alert_admin
    
  delivery_failures:
    action: switch_to_fallback_channel
    if_all_failing: queue_and_alert
    
  agent_overload:
    detection: >3 consecutive timeouts OR >5 queue depth
    action: 
      - temporarily_disable_non_critical_agents
      - spread_load_over_time
      - alert_admin
```

---

## 5. Implementation Phases

### Phase 1 (Days 1-3): Foundation
- [x] Create ARCHITECTURE.md
- [ ] Update AGENTS.md with orchestration rules
- [ ] Create shared memory schema
- [ ] Implement delivery queue
- [ ] Update cron schedules with coordination

### Phase 2 (Days 4-10): Orchestration
- [ ] Build Schedule Manager
- [ ] Build Router
- [ ] Build State Manager
- [ ] Implement sequential execution
- [ ] Add dependency management

### Phase 3 (Days 11-20): Resilience
- [ ] Implement delivery pipeline with retry
- [ ] Add iMessage fallback
- [ ] Build dead letter queue
- [ ] Implement health monitoring
- [ ] Add self-healing actions

### Phase 4 (Days 21-30): Intelligence
- [ ] Cross-agent context sharing
- [ ] Travel mode automation
- [ ] Work hours awareness
- [ ] Dynamic scheduling
- [ ] Predictive load balancing

---

## 6. Migration Plan

### Current State → Target State

| Component | Current | Target | Migration |
|-----------|---------|--------|-----------|
| Scheduling | Independent cron | Orchestrated | Keep crons, add coordination layer |
| Execution | Parallel | Sequential | Add dependency waits |
| Delivery | Direct | Queued | Wrap existing sends in queue |
| Memory | Isolated | Shared | Add shared context reads |
| Fallback | None | 3-channel | Add fallback logic |
| Health | Reactive | Proactive | Add monitoring jobs |

### Backward Compatibility

All changes are additive:
- Existing cron jobs remain
- Agents can still read/write their own memory
- Telegram remains primary channel
- User interaction unchanged

---

## 7. Success Metrics

After 30 days, measure:

| Metric | Baseline | Target |
|--------|----------|--------|
| Delivery success rate | 85% | 99.5% |
| Message loss rate | 15% | 0.5% |
| Timeout errors per week | 5 | <1 |
| Average agent runtime | 65s | 45s |
| User complaints | 2/week | 0 |
| Silent failures | Unknown | 0 |
| Context-aware responses | 10% | 80% |

---

**Next:** See `AGENTS.md` for updated operational rules and `ROADMAP.md` for detailed 30-day plan.
