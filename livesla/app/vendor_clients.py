"""
LiveSLA — Vendor API Client Interfaces
=======================================

Abstract base class and concrete implementations for fetching live metrics
from monitoring systems (Datadog, CloudWatch, Prometheus, etc.)

Architecture
------------
    BaseVendorClient (abstract)
        ├── DatadogClient
        ├── CloudWatchClient
        └── PrometheusClient

Each client implements:
  • fetch_metric(metric_name: str, query_params: dict) -> MetricReading
  • health_check() -> bool
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import aiohttp


@dataclass(frozen=True)
class MetricReading:
    """A single observation from a vendor API.

    Attributes:
        timestamp: When the metric was sampled (UTC).
        metric_name: The identifier that maps to an SLATerm.
        value: The observed numeric value.
        unit: Optional unit (e.g., "percent", "ms", "count").
        metadata: Additional context (host, region, endpoint, etc.).
    """

    timestamp: datetime
    metric_name: str
    value: float
    unit: str | None = None
    metadata: dict[str, Any] | None = None


class BaseVendorClient(ABC):
    """Abstract interface for vendor-specific metric fetchers."""

    def __init__(self, name: str, base_url: str, api_key: str | None = None) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> BaseVendorClient:
        self._session = aiohttp.ClientSession(
            headers=self._default_headers(),
            timeout=aiohttp.ClientTimeout(total=30),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    @abstractmethod
    def _default_headers(self) -> dict[str, str]:
        """Return headers required for every request (auth, content-type, etc.)."""
        ...

    @abstractmethod
    async def fetch_metric(
        self,
        metric_name: str,
        query: dict[str, Any],
    ) -> MetricReading:
        """Fetch a single metric reading from the vendor API.

        Parameters
        ----------
        metric_name : str
            The SLA metric identifier (e.g., "uptime", "response_time_p95").
        query : dict
            Vendor-specific query parameters (host, service, time range, etc.).

        Returns
        -------
        MetricReading
            A validated observation with UTC timestamp.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify API connectivity and credentials."""
        ...

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("Client not entered as async context manager.")
        return self._session


# ---------------------------------------------------------------------------
# Datadog Implementation
# ---------------------------------------------------------------------------

class DatadogClient(BaseVendorClient):
    """Fetch metrics from Datadog monitoring (https://docs.datadoghq.com/api/).

    Environment variables:
        DATADOG_API_KEY  – Required for authentication.
        DATADOG_APP_KEY  – Optional, for access control.
        DATADOG_SITE     – Defaults to "datadoghq.com" (use "datadoghq.eu" for EU).
    """

    def __init__(
        self,
        api_key: str | None = None,
        app_key: str | None = None,
        site: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("DATADOG_API_KEY", "")
        self.app_key = app_key or os.getenv("DATADOG_APP_KEY", "")
        site = site or os.getenv("DATADOG_SITE", "datadoghq.com")
        super().__init__(name="datadog", base_url=f"https://api.{site}", api_key=self.api_key)

    def _default_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self.api_key,
        }
        if self.app_key:
            headers["DD-APPLICATION-KEY"] = self.app_key
        return headers

    async def fetch_metric(
        self,
        metric_name: str,
        query: dict[str, Any],
    ) -> MetricReading:
        """Query Datadog for a single metric point.

        Example query:
            {
                "query": "avg:system.cpu.user{host:web-01}",
                "from": 1704067200,
                "to": 1704067500
            }
        """
        session = self._ensure_session()

        # Datadog query endpoint
        url = f"{self.base_url}/api/v1/query"
        payload = {
            "query": query.get("query"),
            "from": query.get("from"),
            "to": query.get("to"),
        }

        async with session.get(url, params=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()

        # Parse the response — Datadog returns series with pointlist
        series = data.get("series", [])
        if not series:
            raise VendorAPIError(f"No data returned for query: {query.get('query')}")

        # Take the latest point
        points = series[0].get("pointlist", [])
        if not points:
            raise VendorAPIError("Empty pointlist in Datadog response.")

        latest = points[-1]
        ts_ms, value = latest[0], latest[1]

        return MetricReading(
            timestamp=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
            metric_name=metric_name,
            value=float(value),
            unit=series[0].get("unit", None),
            metadata={"scope": series[0].get("scope", ""), "query": query.get("query")},
        )

    async def health_check(self) -> bool:
        """Validate API key by calling the validation endpoint."""
        session = self._ensure_session()
        url = f"{self.base_url}/api/v1/validate"
        async with session.get(url) as resp:
            return resp.status == 200


# ---------------------------------------------------------------------------
# CloudWatch Implementation (AWS)
# ---------------------------------------------------------------------------

class CloudWatchClient(BaseVendorClient):
    """Fetch metrics from AWS CloudWatch.

    Uses boto3 under the hood. Credentials via standard AWS chain:
      • Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
      • ~/.aws/credentials
      • IAM role (if running on EC2/EKS/Lambda)

    Environment variables:
        AWS_REGION – Defaults to "us-east-1".
    """

    def __init__(self, region: str | None = None) -> None:
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        # boto3 is sync — we'll run it in a thread pool
        import boto3

        self._client = boto3.client("cloudwatch", region_name=self.region)
        super().__init__(name="cloudwatch", base_url="", api_key=None)

    def _default_headers(self) -> dict[str, str]:
        return {}  # boto3 handles auth internally

    async def fetch_metric(
        self,
        metric_name: str,
        query: dict[str, Any],
    ) -> MetricReading:
        """Query CloudWatch for a single metric statistic.

        Example query:
            {
                "Namespace": "AWS/EC2",
                "MetricName": "CPUUtilization",
                "Dimensions": [{"Name": "InstanceId", "Value": "i-1234567890"}],
                "Statistics": ["Average"],
                "Period": 60,
                "StartTime": "2024-01-01T00:00:00Z",
                "EndTime": "2024-01-01T00:05:00Z"
            }
        """
        import asyncio

        loop = asyncio.get_event_loop()

        # Run boto3 in thread pool
        response = await loop.run_in_executor(None, self._get_metric_statistics, query)

        datapoints = response.get("Datapoints", [])
        if not datapoints:
            raise VendorAPIError(f"No datapoints returned for {query}")

        # Get the most recent
        latest = max(datapoints, key=lambda d: d["Timestamp"])
        stat_name = query.get("Statistics", ["Average"])[0].lower()
        value = latest.get(stat_name.capitalize(), 0.0)

        return MetricReading(
            timestamp=latest["Timestamp"].replace(tzinfo=timezone.utc),
            metric_name=metric_name,
            value=float(value),
            unit=latest.get("Unit"),
            metadata={
                "namespace": query.get("Namespace"),
                "dimensions": query.get("Dimensions"),
            },
        )

    def _get_metric_statistics(self, query: dict[str, Any]) -> dict:
        """Synchronous boto3 call."""
        return self._client.get_metric_statistics(
            Namespace=query.get("Namespace"),
            MetricName=query.get("MetricName"),
            Dimensions=query.get("Dimensions", []),
            StartTime=query.get("StartTime"),
            EndTime=query.get("EndTime"),
            Period=query.get("Period", 60),
            Statistics=query.get("Statistics", ["Average"]),
        )

    async def health_check(self) -> bool:
        """List metrics to verify connectivity."""
        import asyncio

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._client.list_metrics, {"Limit": 1})
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Prometheus Implementation
# ---------------------------------------------------------------------------

class PrometheusClient(BaseVendorClient):
    """Fetch metrics from Prometheus or compatible APIs (VictoriaMetrics, Thanos).

    Environment variables:
        PROMETHEUS_URL – Base URL of the Prometheus server.
    """

    def __init__(self, base_url: str | None = None) -> None:
        url = base_url or os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        super().__init__(name="prometheus", base_url=url, api_key=None)

    def _default_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    async def fetch_metric(
        self,
        metric_name: str,
        query: dict[str, Any],
    ) -> MetricReading:
        """Query Prometheus instant query API.

        Example query:
            {
                "promql": "up{job=\"api-server\"}",
                "time": "2024-01-01T00:00:00Z"  # optional, defaults to now
            }
        """
        session = self._ensure_session()

        url = f"{self.base_url}/api/v1/query"
        params = {"query": query.get("promql")}
        if "time" in query:
            params["time"] = query["time"]

        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        if data.get("status") != "success":
            raise VendorAPIError(f"Prometheus query failed: {data.get('error')}")

        results = data.get("data", {}).get("result", [])
        if not results:
            raise VendorAPIError(f"No results for PromQL: {query.get('promql')}")

        # Take the first result
        result = results[0]
        value_pair = result.get("value", [])
        if len(value_pair) < 2:
            raise VendorAPIError("Malformed Prometheus value pair.")

        ts_seconds, val = value_pair[0], value_pair[1]

        return MetricReading(
            timestamp=datetime.fromtimestamp(ts_seconds, tz=timezone.utc),
            metric_name=metric_name,
            value=float(val),
            unit=None,  # Prometheus doesn't have units natively
            metadata={
                "metric": result.get("metric", {}),
                "promql": query.get("promql"),
            },
        )

    async def health_check(self) -> bool:
        """Query Prometheus health endpoint."""
        session = self._ensure_session()
        url = f"{self.base_url}/-/healthy"
        try:
            async with session.get(url) as resp:
                return resp.status == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Factory & Errors
# ---------------------------------------------------------------------------

class VendorAPIError(Exception):
    """Raised when a vendor API call fails or returns invalid data."""

    pass


CLIENT_REGISTRY: dict[str, type[BaseVendorClient]] = {
    "datadog": DatadogClient,
    "cloudwatch": CloudWatchClient,
    "prometheus": PrometheusClient,
}


def create_client(vendor: str, **kwargs) -> BaseVendorClient:
    """Factory function to instantiate a vendor client by name.

    Parameters
    ----------
    vendor : str
        One of: "datadog", "cloudwatch", "prometheus".
    **kwargs
        Passed to the client constructor (e.g., api_key, region).

    Raises
    ------
    ValueError
        If the vendor name is not recognized.
    """
    vendor = vendor.lower()
    if vendor not in CLIENT_REGISTRY:
        raise ValueError(f"Unknown vendor: {vendor}. Supported: {list(CLIENT_REGISTRY.keys())}")
    return CLIENT_REGISTRY[vendor](**kwargs)
