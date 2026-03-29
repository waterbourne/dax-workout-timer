"""
LiveSLA — Polling Engine
=========================

Orchestrates the periodic fetching of metrics from vendor APIs,
evaluates them against SLA targets, and records breaches.

Architecture
------------
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   Scheduler  │────▶│   Poller     │────▶│  Evaluator   │
    │  (asyncio)   │     │ (vendor APIs)│     │(breach check)│
    └──────────────┘     └──────────────┘     └──────┬───────┘
                                                      │
                                               ┌──────▼───────┐
                                               │  Database    │
                                               │(MetricLog)   │
                                               └──────────────┘

Usage::

    engine = PollingEngine()
    await engine.start()
    # Runs forever, polling on schedule
    await engine.stop()

Configuration
-------------
    POLL_INTERVAL_SECONDS – How often to poll (default: 60s)
    MAX_RETRIES – Retry failed vendor calls (default: 3)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.evaluator import BreachEvaluator, EvaluationResult, evaluate_batch
from app.models import Contract, MetricLog, SLATerm
from app.schemas import MetricReading
from app.vendor_clients import BaseVendorClient, create_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PollConfig:
    """Configuration for a single metric polling job.

    Links an SLATerm to the vendor query needed to fetch it.
    """

    sla_term_id: int
    metric_name: str
    vendor: str  # "datadog", "cloudwatch", "prometheus"
    query: dict[str, Any]  # Vendor-specific query parameters
    poll_interval_seconds: int = 60


class PollingEngine:
    """Async scheduler that polls vendor APIs and evaluates SLA compliance.

    Parameters
    ----------
    poll_interval : int
        Default seconds between polls (can be overridden per-metric).
    max_retries : int
        How many times to retry failed vendor API calls.
    """

    def __init__(
        self,
        poll_interval: int = 60,
        max_retries: int = 3,
    ) -> None:
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.evaluator = BreachEvaluator()
        self._running = False
        self._task: asyncio.Task | None = None
        self._clients: dict[str, BaseVendorClient] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the polling engine in a background task."""
        if self._running:
            logger.warning("PollingEngine already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("PollingEngine started")

    async def stop(self) -> None:
        """Stop the polling engine gracefully."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # Close all vendor clients
        for client in self._clients.values():
            await client.__aexit__(None, None, None)
        self._clients.clear()

        logger.info("PollingEngine stopped")

    # ------------------------------------------------------------------
    # Main Loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Main polling loop — runs until stopped."""
        while self._running:
            try:
                await self._poll_all()
            except Exception as exc:
                logger.exception("Error in polling loop: %s", exc)

            # Wait for next interval
            await asyncio.sleep(self.poll_interval)

    async def _poll_all(self) -> None:
        """Fetch all active metrics, evaluate, and record results."""
        async with AsyncSessionLocal() as session:
            # Load active SLA terms with their contract info
            active_terms = await self._load_active_terms(session)
            if not active_terms:
                logger.debug("No active SLA terms to poll")
                return

            # Build poll configs (in real usage, these come from config DB)
            configs = self._build_poll_configs(active_terms)

            # Group by vendor for efficient batching
            by_vendor: dict[str, list[PollConfig]] = {}
            for config in configs:
                by_vendor.setdefault(config.vendor, []).append(config)

            # Poll each vendor
            all_readings: list[MetricReading] = []
            for vendor, vendor_configs in by_vendor.items():
                readings = await self._poll_vendor(vendor, vendor_configs)
                all_readings.extend(readings)

            # Evaluate all readings
            results = evaluate_batch(all_readings, active_terms)

            # Record to database
            await self._record_results(session, results)
            await session.commit()

            # Log summary
            breach_count = sum(1 for r in results if r.breach_detected)
            logger.info(
                "Poll cycle complete: %d metrics checked, %d breaches detected",
                len(results),
                breach_count,
            )

    # ------------------------------------------------------------------
    # Vendor Polling
    # ------------------------------------------------------------------

    async def _poll_vendor(
        self,
        vendor: str,
        configs: list[PollConfig],
    ) -> list[MetricReading]:
        """Poll a single vendor for all its configured metrics."""
        readings: list[MetricReading] = []

        # Get or create client
        client = self._clients.get(vendor)
        if client is None:
            try:
                client = create_client(vendor)
                self._clients[vendor] = await client.__aenter__()
            except Exception as exc:
                logger.error("Failed to create %s client: %s", vendor, exc)
                return readings

        # Fetch each metric
        for config in configs:
            for attempt in range(self.max_retries):
                try:
                    reading = await client.fetch_metric(
                        metric_name=config.metric_name,
                        query=config.query,
                    )
                    readings.append(reading)
                    break  # Success
                except Exception as exc:
                    logger.warning(
                        "%s fetch failed (attempt %d/%d): %s",
                        config.metric_name,
                        attempt + 1,
                        self.max_retries,
                        exc,
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        logger.error(
                            "Failed to fetch %s from %s after %d attempts",
                            config.metric_name,
                            vendor,
                            self.max_retries,
                        )

        return readings

    # ------------------------------------------------------------------
    # Database Operations
    # ------------------------------------------------------------------

    async def _load_active_terms(self, session: AsyncSession) -> list[SLATerm]:
        """Load all SLA terms from active contracts."""
        stmt = (
            select(SLATerm)
            .join(Contract)
            .where(Contract.active == True)  # noqa: E712
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _record_results(
        self,
        session: AsyncSession,
        results: list[EvaluationResult],
    ) -> None:
        """Persist evaluation results to the database."""
        for result in results:
            log_entry = MetricLog(
                sla_term_id=result.sla_term_id,
                timestamp=result.reading_timestamp,
                actual_value=result.actual_value,
                breach_detected=result.breach_detected,
            )
            session.add(log_entry)

            if result.breach_detected:
                logger.warning(
                    "SLA BREACH: %s | Actual: %.4f | Target: %.4f | Severity: %s",
                    result.sla_term_id,
                    result.actual_value,
                    result.target_value,
                    result.severity.value,
                )

    # ------------------------------------------------------------------
    # Configuration Builder (Placeholder)
    # ------------------------------------------------------------------

    def _build_poll_configs(self, terms: list[SLATerm]) -> list[PollConfig]:
        """Build polling configs from SLA terms.

        In a production system, this would query a configuration database
        that maps each SLATerm to its vendor-specific query parameters.

        For MVP, we return a placeholder that demonstrates the structure.
        """
        configs: list[PollConfig] = []

        # Example: Hardcoded demo config for testing
        # In production, load from a config table or YAML file
        demo_configs = {
            "uptime": PollConfig(
                sla_term_id=0,  # Will be replaced with actual ID
                metric_name="uptime",
                vendor="prometheus",
                query={"promql": "up{job='api-server'}"},
                poll_interval_seconds=60,
            ),
            "response_time_ms": PollConfig(
                sla_term_id=0,
                metric_name="response_time_ms",
                vendor="prometheus",
                query={"promql": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000"},
                poll_interval_seconds=60,
            ),
        }

        for term in terms:
            if term.metric_name in demo_configs:
                config = demo_configs[term.metric_name]
                # Replace with actual term ID
                configs.append(
                    PollConfig(
                        sla_term_id=term.id,
                        metric_name=term.metric_name,
                        vendor=config.vendor,
                        query=config.query,
                        poll_interval_seconds=config.poll_interval_seconds,
                    )
                )

        return configs


# ---------------------------------------------------------------------------
# One-Shot Poller (for testing / manual runs)
# ---------------------------------------------------------------------------

async def run_single_poll(
    vendor: str,
    metric_name: str,
    query: dict[str, Any],
    sla_term: SLATerm,
) -> EvaluationResult:
    """Fetch a single metric and evaluate it against an SLA term.

    Useful for testing and ad-hoc verification.

    Example::

        result = await run_single_poll(
            vendor="prometheus",
            metric_name="uptime",
            query={"promql": "up{job='api-server'}"},
            sla_term=my_sla_term,
        )
        print(f"Breach: {result.breach_detected}")
    """
    async with create_client(vendor) as client:
        reading = await client.fetch_metric(metric_name, query)

    evaluator = BreachEvaluator()
    return evaluator.evaluate(reading, sla_term)
