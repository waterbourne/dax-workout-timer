# LiveSLA

B2B SaaS platform for PDF contract → SLA extraction → breach monitoring.

## Quick Test

```bash
cd /Users/sirius_bot/.openclaw/workspace/livesla
python test_all.py
```

Or skip LLM tests (no Ollama needed):
```bash
python test_all.py --skip-llm
```

## What's Built

| Step | Component | Status |
|------|-----------|--------|
| 1 | Database models (Contract, SLATerm, MetricLog) | ✅ |
| 2 | AI extraction agent (local LLM via Ollama) | ✅ |
| 3 | Polling engine + breach evaluator | ✅ |
| 4 | Web UI + alerting | ⏳ |

## Project Structure

```
livesla/
├── app/
│   ├── __init__.py
│   ├── database.py        # SQLite + async support
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic validation
│   ├── agent.py           # LLM contract parser
│   ├── vendor_clients.py  # Datadog, CloudWatch, Prometheus
│   ├── evaluator.py       # Breach detection logic
│   └── poller.py          # Async polling engine
├── verify_step1.py        # Test data models
├── verify_step2.py        # Test AI extraction
├── verify_step3.py        # Test evaluator
├── test_all.py            # Run all tests ⭐
├── requirements.txt
└── livesla.db             # SQLite database
```

## Individual Tests

```bash
# Step 1: Database
python verify_step1.py

# Step 2: AI extraction (requires Ollama)
ollama run llama3.2  # in another terminal
python verify_step2.py

# Step 3: Evaluator (no external deps)
python verify_step3.py
```

## Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
- `sqlalchemy`, `aiosqlite` — Database
- `pydantic` — Validation
- `openai` — LLM client
- `aiohttp` — HTTP client
- `boto3` — AWS CloudWatch

## Environment Variables (Optional)

```bash
# For vendor APIs (production)
export DATADOG_API_KEY="..."
export DATADOG_APP_KEY="..."
export AWS_REGION="us-east-1"
export PROMETHEUS_URL="http://localhost:9090"

# For LLM (defaults work for local Ollama)
export LLM_MODEL="llama3.2"
export LLM_BASE_URL="http://localhost:11434/v1"
```
