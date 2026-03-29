"""
LiveSLA — Pydantic Schemas (API / Validation Layer)
=====================================================

These schemas serve two purposes:

1. **Input validation** — Ensure data entering the system (from API
   requests or from the AI extraction agent) is well-formed before it
   touches the database.
2. **Response serialisation** — Provide a clean, typed JSON contract for
   any future FastAPI endpoints.

Every ORM model has a corresponding Create schema (write) and a Read
schema (read, includes ``id`` and ``created_at``).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Contract ────────────────────────────────────────────────────────────────


class ContractCreate(BaseModel):
    """Payload required to create a new Contract record."""

    client_name: str = Field(..., min_length=1, max_length=255, examples=["Acme Corp"])
    vendor_name: str = Field(..., min_length=1, max_length=255, examples=["CloudHost Inc"])
    contract_value: float = Field(..., ge=0, examples=[500_000.00])
    active: bool = Field(default=True)


class ContractRead(ContractCreate):
    """Contract record as returned from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ── SLA Term ────────────────────────────────────────────────────────────────


class SLATermCreate(BaseModel):
    """Payload required to create an SLA Term (used by the AI agent)."""

    contract_id: int = Field(..., ge=1)
    metric_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        examples=["uptime"],
        description="Machine-readable metric identifier.",
    )
    target_value: float = Field(
        ...,
        examples=[99.9],
        description="Contractual threshold (e.g. 99.9 for 99.9 % uptime).",
    )
    penalty_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        examples=[5.0],
        description="Penalty as a % of contract value on breach.",
    )
    description: str | None = Field(
        default=None,
        examples=["Vendor guarantees 99.9% monthly uptime."],
    )


class SLATermRead(SLATermCreate):
    """SLA Term record as returned from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class SLATermExtracted(BaseModel):
    """Lightweight schema the AI agent returns (no contract_id yet).

    The extraction agent doesn't know the contract_id at parse time;
    that gets assigned after the contract is persisted.
    """

    metric_name: str = Field(..., min_length=1, max_length=128)
    target_value: float
    penalty_percentage: float = Field(..., ge=0, le=100)
    description: str | None = None


# ── Metric Log ──────────────────────────────────────────────────────────────


class MetricLogCreate(BaseModel):
    """Payload to record a new metric observation."""

    sla_term_id: int = Field(..., ge=1)
    actual_value: float
    breach_detected: bool = False


class MetricLogRead(MetricLogCreate):
    """Metric log entry as returned from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime


# ── Metric Reading (from Vendor APIs) ───────────────────────────────────────


class MetricReading(BaseModel):
    """A single observation from a vendor monitoring API.

    This is the input to the breach evaluator — it represents a live
    metric reading before it's compared against an SLA target.
    """

    timestamp: datetime
    metric_name: str = Field(..., description="Maps to SLATerm.metric_name")
    value: float = Field(..., description="The observed numeric value")
    unit: str | None = Field(default=None, examples=["percent", "ms", "count"])
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Vendor-specific context (host, region, query used, etc.)",
    )
