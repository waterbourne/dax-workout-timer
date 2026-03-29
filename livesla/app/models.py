"""
LiveSLA — SQLAlchemy ORM Models
================================

Defines the three core tables for the MVP:

* **Contract**   – Represents a signed enterprise agreement between a
                   client and a vendor.
* **SLATerm**    – A single measurable SLA obligation extracted from a
                   contract (e.g. "99.9 % uptime, 5 % penalty").
* **MetricLog**  – A timestamped observation of a live metric, recording
                   whether it breached the SLA target.

Relationships
-------------
Contract  1 ──▶ ∞  SLATerm   (cascade delete)
SLATerm   1 ──▶ ∞  MetricLog (cascade delete)
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contract(Base):
    """An enterprise contract between a client and a vendor.

    Attributes:
        id:              Auto-incrementing primary key.
        client_name:     The customer / buyer organisation.
        vendor_name:     The service provider bound by SLAs.
        contract_value:  Total monetary value of the contract (USD).
        active:          Whether the contract is currently in force.
        created_at:      UTC timestamp of record creation.
        sla_terms:       One-to-many collection of extracted SLA terms.
    """

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contract_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # --- relationships -------------------------------------------------------
    sla_terms: Mapped[list["SLATerm"]] = relationship(
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Contract(id={self.id}, client={self.client_name!r}, "
            f"vendor={self.vendor_name!r}, active={self.active})>"
        )


class SLATerm(Base):
    """A single SLA metric obligation tied to a contract.

    Attributes:
        id:                  Auto-incrementing primary key.
        contract_id:         FK → contracts.id.
        metric_name:         What is being measured (e.g. "uptime",
                             "response_time_ms", "error_rate").
        target_value:        The contractual threshold.  For "uptime" this
                             might be 99.9 (meaning 99.9 %).
        penalty_percentage:  The financial penalty as a percentage of
                             contract value if the SLA is breached.
        description:         Optional free-text context extracted from
                             the legal clause.
        created_at:          UTC timestamp of record creation.
        contract:            Back-reference to the parent Contract.
        metric_logs:         One-to-many collection of observed readings.
    """

    __tablename__ = "sla_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    penalty_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # --- relationships -------------------------------------------------------
    contract: Mapped["Contract"] = relationship(back_populates="sla_terms")
    metric_logs: Mapped[list["MetricLog"]] = relationship(
        back_populates="sla_term",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<SLATerm(id={self.id}, metric={self.metric_name!r}, "
            f"target={self.target_value}, penalty={self.penalty_percentage}%)>"
        )


class MetricLog(Base):
    """A point-in-time observation of a live metric for an SLA term.

    Attributes:
        id:               Auto-incrementing primary key.
        sla_term_id:      FK → sla_terms.id.
        timestamp:        When the metric was sampled (UTC).
        actual_value:     The observed value from the operational API.
        breach_detected:  True if actual_value violated the SLA target.
        sla_term:         Back-reference to the parent SLATerm.
    """

    __tablename__ = "metric_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sla_term_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sla_terms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    breach_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- relationships -------------------------------------------------------
    sla_term: Mapped["SLATerm"] = relationship(back_populates="metric_logs")

    def __repr__(self) -> str:
        status = "BREACH" if self.breach_detected else "OK"
        return (
            f"<MetricLog(id={self.id}, value={self.actual_value}, "
            f"status={status}, ts={self.timestamp.isoformat()})>"
        )
