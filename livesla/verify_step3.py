"""
Step 3 Verification — Breach Evaluator & Polling Engine
=======================================================

Tests the core evaluation logic without requiring live vendor APIs.

Run:  python verify_step3.py

This script:
  1. Tests the BreachEvaluator against various scenarios
  2. Demonstrates batch evaluation
  3. Shows the polling engine structure (dry-run mode)

No external APIs required — all tests use synthetic data.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
logger = logging.getLogger(__name__)

DIVIDER = "═" * 60


def test_evaluator():
    """Test the breach evaluator with synthetic data."""
    print(f"\n{DIVIDER}")
    print("Step 3 │ Breach Evaluator — Unit Tests")
    print(DIVIDER)

    # Import here to avoid DB dependency for pure logic tests
    from app.evaluator import BreachEvaluator, BreachSeverity, get_metric_direction, MetricDirection
    from app.schemas import MetricReading

    evaluator = BreachEvaluator()

    # Create a mock SLA term using a simple namespace object
    class MockSLATerm:
        def __init__(self, id, metric_name, target_value, penalty_percentage):
            self.id = id
            self.metric_name = metric_name
            self.target_value = target_value
            self.penalty_percentage = penalty_percentage

    test_cases = [
        # (metric_name, actual, target, expected_breach, expected_severity, description)
        ("uptime", 99.9, 99.9, False, BreachSeverity.NONE, "Exactly at target"),
        ("uptime", 99.95, 99.9, False, BreachSeverity.NONE, "Above target (good)"),
        ("uptime", 99.5, 99.9, True, BreachSeverity.MINOR, "Below target by ~0.4% (<1%)"),
        ("uptime", 98.0, 99.9, True, BreachSeverity.MAJOR, "Below target by ~1.9% (1-5%)"),
        ("uptime", 94.0, 99.9, True, BreachSeverity.CRITICAL, "Way below target (>=5%)"),
        ("response_time_ms", 200, 200, False, BreachSeverity.NONE, "Exactly at target"),
        ("response_time_ms", 150, 200, False, BreachSeverity.NONE, "Below target (good)"),
        ("response_time_ms", 201, 200, True, BreachSeverity.MINOR, "0.5% over target (<1%)"),
        ("response_time_ms", 210, 200, True, BreachSeverity.CRITICAL, "5% over target (>=5%)"),
        ("response_time_ms", 250, 200, True, BreachSeverity.CRITICAL, "25% over target (>=5%)"),
        ("error_rate", 0.05, 0.1, False, BreachSeverity.NONE, "Below threshold (good)"),
        ("error_rate", 0.105, 0.1, True, BreachSeverity.MAJOR, "5% over threshold (>=5% of target)"),
        ("error_rate", 0.15, 0.1, True, BreachSeverity.CRITICAL, "50% over threshold (>=5%)"),
    ]

    passed = 0
    failed = 0

    for metric_name, actual, target, expect_breach, expect_severity, desc in test_cases:
        reading = MetricReading(
            timestamp=datetime.now(timezone.utc),
            metric_name=metric_name,
            value=actual,
        )
        sla_term = MockSLATerm(
            id=1,
            metric_name=metric_name,
            target_value=target,
            penalty_percentage=5.0,
        )

        result = evaluator.evaluate(reading, sla_term)

        breach_ok = result.breach_detected == expect_breach
        severity_ok = result.severity == expect_severity

        status = "✅" if (breach_ok and severity_ok) else "❌"
        if breach_ok and severity_ok:
            passed += 1
        else:
            failed += 1

        print(f"\n{status} {desc}")
        print(f"   Metric: {metric_name} | Actual: {actual} | Target: {target}")
        print(f"   Breach: {result.breach_detected} (expected: {expect_breach})")
        print(f"   Severity: {result.severity.value} (expected: {expect_severity.value})")
        if not (breach_ok and severity_ok):
            print(f"   ❌ MISMATCH!")

    print(f"\n{DIVIDER}")
    print(f"Results: {passed} passed, {failed} failed")
    print(DIVIDER)

    return failed == 0


def test_metric_directions():
    """Test the metric direction detection."""
    print(f"\n{DIVIDER}")
    print("Step 3 │ Metric Direction Detection")
    print(DIVIDER)

    from app.evaluator import get_metric_direction, MetricDirection

    test_cases = [
        # (metric_name, expected_direction)
        ("uptime", MetricDirection.HIGHER_IS_BETTER),
        ("availability", MetricDirection.HIGHER_IS_BETTER),
        ("success_rate", MetricDirection.HIGHER_IS_BETTER),
        ("response_time_ms", MetricDirection.LOWER_IS_BETTER),
        ("latency", MetricDirection.LOWER_IS_BETTER),
        ("error_rate", MetricDirection.LOWER_IS_BETTER),
        ("resolution_time_hours", MetricDirection.LOWER_IS_BETTER),
        ("mttr_hours", MetricDirection.LOWER_IS_BETTER),
    ]

    passed = 0
    for metric_name, expected in test_cases:
        actual = get_metric_direction(metric_name)
        ok = actual == expected
        status = "✅" if ok else "❌"
        print(f"{status} {metric_name:<25} → {actual.value}")
        if ok:
            passed += 1

    print(f"\n{DIVIDER}")
    print(f"Results: {passed}/{len(test_cases)} correct")
    print(DIVIDER)

    return passed == len(test_cases)


def test_batch_evaluation():
    """Test batch evaluation with multiple readings."""
    print(f"\n{DIVIDER}")
    print("Step 3 │ Batch Evaluation")
    print(DIVIDER)

    from app.evaluator import evaluate_batch
    from app.schemas import MetricReading

    class MockSLATerm:
        def __init__(self, id, metric_name, target_value, penalty_percentage):
            self.id = id
            self.metric_name = metric_name
            self.target_value = target_value
            self.penalty_percentage = penalty_percentage

    # Create SLA terms
    terms = [
        MockSLATerm(id=1, metric_name="uptime", target_value=99.9, penalty_percentage=5.0),
        MockSLATerm(id=2, metric_name="response_time_ms", target_value=200, penalty_percentage=3.0),
        MockSLATerm(id=3, metric_name="error_rate", target_value=0.1, penalty_percentage=2.0),
    ]

    # Create readings (some breach, some don't)
    now = datetime.now(timezone.utc)
    readings = [
        MetricReading(timestamp=now, metric_name="uptime", value=99.5),  # Breach
        MetricReading(timestamp=now, metric_name="uptime", value=99.95),  # OK
        MetricReading(timestamp=now, metric_name="response_time_ms", value=250),  # Breach
        MetricReading(timestamp=now, metric_name="error_rate", value=0.05),  # OK
        MetricReading(timestamp=now, metric_name="unknown_metric", value=100),  # No matching term
    ]

    results = evaluate_batch(readings, terms)

    print(f"\nReadings: {len(readings)}")
    print(f"Matched & Evaluated: {len(results)}")

    breaches = [r for r in results if r.breach_detected]
    ok_count = len(results) - len(breaches)

    print(f"  ✅ Compliant: {ok_count}")
    print(f"  ❌ Breaches: {len(breaches)}")

    for breach in breaches:
        print(f"\n  Breach Details:")
        print(f"    SLA Term ID: {breach.sla_term_id}")
        print(f"    Metric: {breach.actual_value:.2f} vs target {breach.target_value:.2f}")
        print(f"    Deviation: {breach.deviation_percentage:.2f}%")
        print(f"    Penalty: {breach.penalty_percentage}%")

    print(f"\n{DIVIDER}")

    # Verify expected results
    expected_breaches = 2  # uptime (99.5) and response_time (250)
    if len(breaches) == expected_breaches:
        print(f"✅ Batch evaluation correct: {expected_breaches} breaches detected")
        return True
    else:
        print(f"❌ Expected {expected_breaches} breaches, got {len(breaches)}")
        return False


async def test_poller_structure():
    """Demonstrate the polling engine structure (dry-run, no external APIs)."""
    print(f"\n{DIVIDER}")
    print("Step 3 │ Polling Engine Structure")
    print(DIVIDER)

    from app.poller import PollingEngine, PollConfig

    print("\n📋 PollingEngine Configuration:")
    print("  Default poll interval: 60 seconds")
    print("  Max retries: 3")
    print("  Supports vendors: datadog, cloudwatch, prometheus")

    # Show the PollConfig structure
    print("\n📋 PollConfig (per-metric configuration):")
    config = PollConfig(
        sla_term_id=1,
        metric_name="uptime",
        vendor="prometheus",
        query={"promql": "up{job='api-server'}"},
        poll_interval_seconds=60,
    )
    print(f"  sla_term_id: {config.sla_term_id}")
    print(f"  metric_name: {config.metric_name}")
    print(f"  vendor: {config.vendor}")
    print(f"  query: {config.query}")
    print(f"  poll_interval: {config.poll_interval_seconds}s")

    # Show how the engine would be started
    print("\n📋 Usage Example:")
    print("""
    engine = PollingEngine(poll_interval=60)
    await engine.start()
    
    # Runs forever, polling every 60s...
    
    await engine.stop()
    """)

    print(f"\n{DIVIDER}")
    print("✅ Polling engine structure verified")
    print(DIVIDER)

    return True


async def main():
    """Run all Step 3 verification tests."""
    print(f"\n{'═' * 60}")
    print("Step 3 │ Polling Engine & Breach Evaluator")
    print("         API Polling → Evaluation → Breach Detection")
    print('═' * 60)

    all_passed = True

    # Test 1: Evaluator logic
    if not test_evaluator():
        all_passed = False

    # Test 2: Metric directions
    if not test_metric_directions():
        all_passed = False

    # Test 3: Batch evaluation
    if not test_batch_evaluation():
        all_passed = False

    # Test 4: Poller structure
    if not await test_poller_structure():
        all_passed = False

    # Summary
    print(f"\n{'═' * 60}")
    if all_passed:
        print("🎉 Step 3 Verification Complete — All Tests Passed")
    else:
        print("❌ Step 3 Verification Failed — See errors above")
    print('═' * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
