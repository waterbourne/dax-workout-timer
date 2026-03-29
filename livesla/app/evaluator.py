"""
LiveSLA — Breach Evaluator
===========================

Compares live metric readings against SLA targets and determines:
  • Did a breach occur?
  • What is the severity?
  • What penalty (if any) applies?

Evaluation Rules
----------------
    metric_type          comparison         breach_when
    ─────────────────────────────────────────────────────────────
    uptime              actual < target    99.5 < 99.9  → breach
    response_time_ms    actual > target    250 > 200    → breach
    error_rate          actual > target    0.5 > 0.1    → breach
    availability        actual < target    99.0 < 99.9  → breach

The evaluator is stateless — it receives a reading and an SLATerm,
returns an EvaluationResult. Persistence is the caller's responsibility.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from app.models import SLATerm
from app.schemas import MetricReading as MetricReadingSchema

logger = logging.getLogger(__name__)


class BreachSeverity(Enum):
    """Severity levels for SLA breaches."""

    NONE = "none"
    MINOR = "minor"      # < 1% deviation
    MAJOR = "major"      # 1-5% deviation
    CRITICAL = "critical"  # > 5% deviation


class MetricDirection(Enum):
    """Whether higher or lower values are better for a metric."""

    HIGHER_IS_BETTER = "higher_is_better"  # uptime, availability
    LOWER_IS_BETTER = "lower_is_better"    # response_time, error_rate


# ---------------------------------------------------------------------------
# Known metric types and their evaluation direction
# ---------------------------------------------------------------------------

METRIC_DIRECTIONS: dict[str, MetricDirection] = {
    # Higher is better (target is minimum acceptable)
    "uptime": MetricDirection.HIGHER_IS_BETTER,
    "availability": MetricDirection.HIGHER_IS_BETTER,
    "success_rate": MetricDirection.HIGHER_IS_BETTER,
    "delivery_rate": MetricDirection.HIGHER_IS_BETTER,
    # Lower is better (target is maximum acceptable)
    "response_time_ms": MetricDirection.LOWER_IS_BETTER,
    "response_time": MetricDirection.LOWER_IS_BETTER,
    "latency_ms": MetricDirection.LOWER_IS_BETTER,
    "latency": MetricDirection.LOWER_IS_BETTER,
    "error_rate": MetricDirection.LOWER_IS_BETTER,
    "failure_rate": MetricDirection.LOWER_IS_BETTER,
    "resolution_time_hours": MetricDirection.LOWER_IS_BETTER,
    "resolution_time": MetricDirection.LOWER_IS_BETTER,
    "mttr_hours": MetricDirection.LOWER_IS_BETTER,
}


def get_metric_direction(metric_name: str) -> MetricDirection:
    """Determine if higher or lower values are better for a metric.

    Falls back to LOWER_IS_BETTER if unknown (conservative default).
    """
    # Normalize metric name
    normalized = metric_name.lower().strip()

    # Direct lookup
    if normalized in METRIC_DIRECTIONS:
        return METRIC_DIRECTIONS[normalized]

    # Pattern matching for common suffixes
    if any(suffix in normalized for suffix in ["uptime", "availability", "success", "delivery"]):
        return MetricDirection.HIGHER_IS_BETTER
    if any(suffix in normalized for suffix in ["time", "latency", "rate", "duration", "hours", "minutes"]):
        return MetricDirection.LOWER_IS_BETTER

    # Conservative default
    logger.warning(f"Unknown metric direction for '{metric_name}', defaulting to LOWER_IS_BETTER")
    return MetricDirection.LOWER_IS_BETTER


# ---------------------------------------------------------------------------
# Evaluation Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvaluationResult:
    """The outcome of evaluating a metric reading against an SLA term.

    Attributes:
        sla_term_id: The database ID of the SLATerm that was evaluated.
        reading_timestamp: When the metric was observed.
        actual_value: The observed value from the vendor API.
        target_value: The contractual threshold.
        breach_detected: True if the SLA was violated.
        severity: Calculated severity of the breach (or NONE).
        deviation_percentage: How far off target (absolute percentage).
        direction: Whether higher or lower values are better.
        penalty_percentage: The contractual penalty (0.0 if no breach).
    """

    sla_term_id: int
    reading_timestamp: datetime
    actual_value: float
    target_value: float
    breach_detected: bool
    severity: BreachSeverity
    deviation_percentage: float
    direction: MetricDirection
    penalty_percentage: float

    def to_metric_log_dict(self) -> dict:
        """Convert to dict for creating a MetricLog database record."""
        return {
            "sla_term_id": self.sla_term_id,
            "timestamp": self.reading_timestamp,
            "actual_value": self.actual_value,
            "breach_detected": self.breach_detected,
        }


# ---------------------------------------------------------------------------
# Evaluator Engine
# ---------------------------------------------------------------------------

class BreachEvaluator:
    """Evaluates metric readings against SLA targets to detect breaches.

    Usage::

        evaluator = BreachEvaluator()
        result = evaluator.evaluate(reading, sla_term)
        if result.breach_detected:
            print(f"Breach! Deviation: {result.deviation_percentage:.2f}%")
    """

    # Severity thresholds (percentage deviation)
    MINOR_THRESHOLD = 1.0    # < 1% = minor
    MAJOR_THRESHOLD = 5.0    # 1-5% = major
    # > 5% = critical

    def evaluate(
        self,
        reading: MetricReadingSchema,
        sla_term: SLATerm,
    ) -> EvaluationResult:
        """Compare a live reading against an SLA term.

        Parameters
        ----------
        reading : MetricReading
            The observed metric value from a vendor API.
        sla_term : SLATerm
            The contractual obligation (target_value, penalty_percentage).

        Returns
        -------
        EvaluationResult
            Complete evaluation including breach status and severity.
        """
        direction = get_metric_direction(sla_term.metric_name)
        actual = reading.value
        target = sla_term.target_value

        # Determine breach
        breach_detected = self._is_breach(actual, target, direction)

        # Calculate deviation percentage
        deviation = self._calculate_deviation(actual, target, direction)

        # Determine severity
        severity = self._calculate_severity(deviation, breach_detected)

        # Apply penalty only if breached
        penalty = sla_term.penalty_percentage if breach_detected else 0.0

        return EvaluationResult(
            sla_term_id=sla_term.id,
            reading_timestamp=reading.timestamp,
            actual_value=actual,
            target_value=target,
            breach_detected=breach_detected,
            severity=severity,
            deviation_percentage=deviation,
            direction=direction,
            penalty_percentage=penalty,
        )

    def _is_breach(
        self,
        actual: float,
        target: float,
        direction: MetricDirection,
    ) -> bool:
        """Determine if actual value breaches the target threshold."""
        if direction == MetricDirection.HIGHER_IS_BETTER:
            # For uptime/availability: actual must be >= target
            return actual < target
        else:
            # For latency/error_rate: actual must be <= target
            return actual > target

    def _calculate_deviation(
        self,
        actual: float,
        target: float,
        direction: MetricDirection,
    ) -> float:
        """Calculate percentage deviation from target.

        For HIGHER_IS_BETTER: how much below target (as % of target)
        For LOWER_IS_BETTER: how much above target (as % of target)
        """
        if target == 0:
            return 0.0  # Avoid division by zero

        if direction == MetricDirection.HIGHER_IS_BETTER:
            # How much we're below target
            return max(0.0, ((target - actual) / target) * 100)
        else:
            # How much we're above target
            return max(0.0, ((actual - target) / target) * 100)

    def _calculate_severity(
        self,
        deviation_percentage: float,
        breach_detected: bool,
    ) -> BreachSeverity:
        """Classify the severity of a breach based on deviation."""
        if not breach_detected:
            return BreachSeverity.NONE

        if deviation_percentage >= self.MAJOR_THRESHOLD:
            return BreachSeverity.CRITICAL
        elif deviation_percentage >= self.MINOR_THRESHOLD:
            return BreachSeverity.MAJOR
        else:
            return BreachSeverity.MINOR


# ---------------------------------------------------------------------------
# Batch Evaluation
# ---------------------------------------------------------------------------

def evaluate_batch(
    readings: list[MetricReadingSchema],
    sla_terms: list[SLATerm],
) -> list[EvaluationResult]:
    """Evaluate multiple readings against their matching SLA terms.

    Matches readings to SLA terms by metric_name. Unmatched readings are skipped.

    Parameters
    ----------
    readings : list[MetricReading]
        Observations from vendor APIs.
    sla_terms : list[SLATerm]
        SLA obligations from the database.

    Returns
    -------
    list[EvaluationResult]
        One evaluation result for each matched reading.
    """
    evaluator = BreachEvaluator()
    results: list[EvaluationResult] = []

    # Index SLA terms by metric name for fast lookup
    term_index: dict[str, SLATerm] = {t.metric_name: t for t in sla_terms}

    for reading in readings:
        sla_term = term_index.get(reading.metric_name)
        if sla_term is None:
            logger.warning(f"No SLA term found for metric: {reading.metric_name}")
            continue

        result = evaluator.evaluate(reading, sla_term)
        results.append(result)

    return results
