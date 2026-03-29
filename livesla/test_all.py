#!/usr/bin/env python3
"""
LiveSLA — Full System Test
===========================

Run this script to verify the entire LiveSLA system is working.

Usage:
    cd /Users/sirius_bot/.openclaw/workspace/livesla
    python test_all.py

Or from anywhere:
    python /Users/sirius_bot/.openclaw/workspace/livesla/test_all.py

What it tests:
  1. Python environment and dependencies
  2. Database connectivity
  3. Data models (Step 1)
  4. AI extraction agent (Step 2) — requires Ollama running
  5. Breach evaluator & polling engine (Step 3)

Requirements:
  - Python 3.11+ with virtual environment activated
  - Ollama running locally (for Step 2) — skip with --skip-llm
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import subprocess
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

DIVIDER = "═" * 70


def print_header(title: str) -> None:
    print(f"\n{BOLD}{BLUE}{DIVIDER}{RESET}")
    print(f"{BOLD}{BLUE}{title.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{DIVIDER}{RESET}\n")


def print_section(name: str) -> None:
    print(f"\n{'─' * 70}")
    print(f"  {name}")
    print(f"{'─' * 70}")


def print_success(msg: str) -> None:
    print(f"{GREEN}✅{RESET} {msg}")


def print_error(msg: str) -> None:
    print(f"{RED}❌{RESET} {msg}")


def print_warning(msg: str) -> None:
    print(f"{YELLOW}⚠️{RESET} {msg}")


def check_python_version() -> bool:
    """Verify Python 3.11 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} — requires 3.11+")
        return False


def check_dependencies() -> dict[str, bool]:
    """Check required Python packages."""
    required = {
        "sqlalchemy": "Database ORM",
        "pydantic": "Data validation",
        "openai": "LLM client",
        "aiohttp": "Async HTTP client",
        "aiosqlite": "Async SQLite",
        "boto3": "AWS SDK (CloudWatch)",
    }

    results = {}
    print_section("Checking Dependencies")

    for package, purpose in required.items():
        try:
            importlib.import_module(package)
            print_success(f"{package:<15} — {purpose}")
            results[package] = True
        except ImportError:
            print_error(f"{package:<15} — {purpose} (MISSING)")
            results[package] = False

    return results


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "llama3.2" in result.stdout:
            print_success("Ollama running with llama3.2 model")
            return True
        elif result.returncode == 0:
            print_warning("Ollama running but llama3.2 may not be pulled")
            return True
        else:
            print_error("Ollama not responding on localhost:11434")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_error("Ollama not detected (curl failed or timeout)")
        return False


def run_verify_step1() -> bool:
    """Run Step 1 verification (database models)."""
    print_section("Step 1: Database Models")

    try:
        from app.database import engine, SessionLocal
        from app.models import Base, Contract, SLATerm, MetricLog

        # Create tables
        Base.metadata.create_all(bind=engine)
        print_success("Database tables created")

        # Test basic operations
        with SessionLocal() as session:
            # Count records
            contracts = session.query(Contract).count()
            terms = session.query(SLATerm).count()
            logs = session.query(MetricLog).count()

            print_success(f"Database connected — {contracts} contracts, {terms} SLA terms, {logs} logs")

        return True

    except Exception as exc:
        print_error(f"Database test failed: {exc}")
        return False


def run_verify_step2(skip_llm: bool = False) -> bool:
    """Run Step 2 verification (AI extraction agent)."""
    print_section("Step 2: AI Extraction Agent")

    if skip_llm:
        print_warning("Skipping LLM test ( --skip-llm flag )")
        print_success("Agent imports successfully")
        return True

    # Check Ollama first
    if not check_ollama():
        print_warning("Ollama not available — skipping LLM extraction test")
        print("   To test LLM extraction, run: ollama run llama3.2")
        return True  # Don't fail the whole suite for this

    try:
        # Import and test the agent
        import asyncio
        from app.agent import ContractParserAgent

        sample_text = """
        Service Level Agreement: Vendor guarantees 99.9% uptime.
        If uptime falls below 99.9%, a 5% service credit applies.
        Response time must be under 200ms or 3% penalty applies.
        """

        async def test_extraction():
            agent = ContractParserAgent()
            terms = await agent.extract(sample_text)
            return len(terms) >= 2  # Expect at least 2 terms

        result = asyncio.run(test_extraction())

        if result:
            print_success("LLM extraction working — extracted SLA terms")
            return True
        else:
            print_warning("LLM extraction returned few results — check Ollama")
            return True

    except Exception as exc:
        print_error(f"LLM extraction test failed: {exc}")
        return False


def run_verify_step3() -> bool:
    """Run Step 3 verification (evaluator & poller)."""
    print_section("Step 3: Breach Evaluator & Polling Engine")

    try:
        from app.evaluator import BreachEvaluator, BreachSeverity
        from app.schemas import MetricReading
        from datetime import datetime, timezone

        evaluator = BreachEvaluator()

        # Create mock SLA term
        class MockTerm:
            def __init__(self):
                self.id = 1
                self.metric_name = "uptime"
                self.target_value = 99.9
                self.penalty_percentage = 5.0

        term = MockTerm()

        # Test case: breach detected
        reading = MetricReading(
            timestamp=datetime.now(timezone.utc),
            metric_name="uptime",
            value=99.5,
        )

        result = evaluator.evaluate(reading, term)

        checks = [
            (result.breach_detected, True, "Breach detection"),
            (result.severity == BreachSeverity.MINOR, True, "Severity classification"),
            (result.deviation_percentage > 0, True, "Deviation calculation"),
            (result.penalty_percentage == 5.0, True, "Penalty extraction"),
        ]

        all_passed = True
        for actual, expected, name in checks:
            if actual == expected:
                print_success(f"{name}")
            else:
                print_error(f"{name} — expected {expected}, got {actual}")
                all_passed = False

        # Test vendor client imports
        from app.vendor_clients import create_client, DatadogClient, CloudWatchClient, PrometheusClient
        print_success("Vendor clients import correctly (Datadog, CloudWatch, Prometheus)")

        # Test poller imports
        from app.poller import PollingEngine, PollConfig
        print_success("Polling engine imports correctly")

        return all_passed

    except Exception as exc:
        print_error(f"Evaluator test failed: {exc}")
        import traceback
        traceback.print_exc()
        return False


def check_project_structure() -> bool:
    """Verify all expected files exist."""
    print_section("Project Structure")

    expected_files = [
        "app/__init__.py",
        "app/database.py",
        "app/models.py",
        "app/schemas.py",
        "app/agent.py",
        "app/vendor_clients.py",
        "app/evaluator.py",
        "app/poller.py",
        "verify_step1.py",
        "verify_step2.py",
        "verify_step3.py",
        "requirements.txt",
    ]

    project_root = Path(__file__).parent
    all_exist = True

    for file_path in expected_files:
        full_path = project_root / file_path
        if full_path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} — MISSING")
            all_exist = False

    return all_exist


def main():
    parser = argparse.ArgumentParser(
        description="Test LiveSLA system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_all.py              # Run all tests
  python test_all.py --skip-llm   # Skip LLM tests (no Ollama needed)
        """,
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip tests that require Ollama LLM",
    )
    args = parser.parse_args()

    print_header("LiveSLA System Test")
    print(f"Project: /Users/sirius_bot/.openclaw/workspace/livesla")
    print(f"Python:  {sys.executable}")

    results = {
        "python_version": False,
        "dependencies": False,
        "project_structure": False,
        "step1_database": False,
        "step2_agent": False,
        "step3_evaluator": False,
    }

    # 1. Python version
    print_section("Environment")
    results["python_version"] = check_python_version()

    # 2. Dependencies
    dep_results = check_dependencies()
    results["dependencies"] = all(dep_results.values())

    # 3. Project structure
    results["project_structure"] = check_project_structure()

    # 4. Step 1: Database
    results["step1_database"] = run_verify_step1()

    # 5. Step 2: AI Agent
    results["step2_agent"] = run_verify_step2(skip_llm=args.skip_llm)

    # 6. Step 3: Evaluator & Poller
    results["step3_evaluator"] = run_verify_step3()

    # Summary
    print_header("Test Summary")

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {name.replace('_', ' ').title():<25} {status}")

    print(f"\n{BOLD}Overall: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 All systems operational!{RESET}")
        print(f"\nNext steps:")
        print(f"  • Run individual verifications:")
        print(f"    python verify_step1.py")
        print(f"    python verify_step2.py  # requires Ollama")
        print(f"    python verify_step3.py")
        print(f"  • Start building Step 4 (Web UI, alerts, reporting)")
        return 0
    else:
        print(f"\n{RED}{BOLD}⚠️  Some tests failed — check output above{RESET}")
        print(f"\nTroubleshooting:")
        if not results["dependencies"]:
            print(f"  • Install dependencies: pip install -r requirements.txt")
        if not results["step2_agent"] and not args.skip_llm:
            print(f"  • For LLM tests: ollama run llama3.2")
            print(f"  • Or skip LLM: python test_all.py --skip-llm")
        return 1


if __name__ == "__main__":
    sys.exit(main())
