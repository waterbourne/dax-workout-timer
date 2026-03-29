"""
Step 2 Verification — Run the ContractParserAgent against sample legal text.
=============================================================================

Requires a local LLM running on localhost:11434 (Ollama default).

Run:  python verify_step2.py

Env overrides:
    LLM_BASE_URL=http://localhost:11434/v1
    LLM_MODEL=qwen3
"""

import asyncio
import logging
import sys

from app.agent import ContractParserAgent, ExtractionError

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
logger = logging.getLogger(__name__)

DIVIDER = "─" * 60

# ---------------------------------------------------------------------------
# Sample legal text — simulates what a PDF parser would hand us.
# ---------------------------------------------------------------------------
SAMPLE_CONTRACT_TEXT = """\
MASTER SERVICES AGREEMENT — EXHIBIT B: SERVICE LEVEL COMMITMENTS

Section 4.1 — Uptime Guarantee
The Vendor ("CloudHost Inc") shall ensure that its production hosting
infrastructure maintains a Monthly Uptime Percentage of no less than
ninety-nine point nine percent (99.9%). "Monthly Uptime Percentage" is
calculated as total minutes in the calendar month minus minutes of
Downtime, divided by total minutes in the month, multiplied by 100.
In the event that Monthly Uptime Percentage falls below the stated
threshold, the Client ("Acme Corp") shall be entitled to a service
credit equal to five percent (5%) of the monthly contract fees.

Section 4.2 — API Response Time
The Vendor guarantees that the 95th-percentile response time for all
production API endpoints shall not exceed two hundred milliseconds
(200 ms) measured over any rolling 24-hour period. Should the Vendor
fail to meet this obligation, a penalty of three percent (3%) of the
monthly contract value shall be applied.

Section 4.3 — Incident Resolution
Critical severity incidents (Severity 1) must be resolved within four
(4) hours of acknowledgement. Failure to resolve within this window
shall result in a penalty of ten percent (10%) of the monthly fees for
each occurrence, capped at 30% per calendar month.

Section 4.4 — Error Rate
The aggregate error rate across all production endpoints shall not
exceed zero point one percent (0.1%) of total requests in any calendar
month. Breach of this threshold entitles the Client to a service credit
of two percent (2%) of the monthly contract fees.
"""


async def main() -> None:
    print(f"\n{DIVIDER}")
    print("Step 2 │ Contract Parser Agent — Extraction Test")
    print(DIVIDER)

    print(f"\n📄 Input: {len(SAMPLE_CONTRACT_TEXT)} chars of legal text")
    print(f"   Sections: 4.1 (Uptime), 4.2 (API Response), "
          f"4.3 (Incident Resolution), 4.4 (Error Rate)")

    agent = ContractParserAgent()

    print(f"\n{DIVIDER}")
    print("🤖 Calling local LLM …\n")

    try:
        terms = await agent.extract(SAMPLE_CONTRACT_TEXT)
    except ExtractionError as exc:
        print(f"  ❌ Extraction failed: {exc}")
        sys.exit(1)

    print(f"  ✅ Extracted {len(terms)} SLA terms:\n")

    for i, term in enumerate(terms, 1):
        print(f"  ┌─ Term {i} ──────────────────────────────────")
        print(f"  │ metric_name       : {term.metric_name}")
        print(f"  │ target_value      : {term.target_value}")
        print(f"  │ penalty_percentage : {term.penalty_percentage}%")
        print(f"  │ description       : {term.description}")
        print(f"  └────────────────────────────────────────────\n")

    # ── Sanity checks ───────────────────────────────────────────────────
    print(f"{DIVIDER}")
    print("🔍 Validation checks:\n")

    metric_names = {t.metric_name for t in terms}
    expected = {"uptime", "response_time_ms", "resolution_time_hours", "error_rate"}

    # We check overlap rather than exact match — LLM naming may vary slightly
    overlap = metric_names & expected
    if len(overlap) >= 3:
        print(f"  ✅ Found {len(overlap)}/4 expected metrics: {overlap}")
    else:
        print(f"  ⚠️  Only matched {len(overlap)}/4 expected metrics.")
        print(f"     Got: {metric_names}")
        print(f"     Expected (approx): {expected}")

    for term in terms:
        if term.metric_name in ("uptime",) and abs(term.target_value - 99.9) < 0.01:
            print(f"  ✅ Uptime target correctly extracted: {term.target_value}")
        if term.metric_name in ("uptime",) and abs(term.penalty_percentage - 5.0) < 0.01:
            print(f"  ✅ Uptime penalty correctly extracted: {term.penalty_percentage}%")

    print(f"\n{DIVIDER}")
    print("🎉  Step 2 verification complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
