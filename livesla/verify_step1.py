"""
Step 1 Verification — Create tables, insert sample data, query it back.
=========================================================================

Run:  python verify_step1.py
"""

from datetime import datetime, timezone

from app.database import Base, SessionLocal, engine
from app.models import Contract, MetricLog, SLATerm
from app.schemas import ContractCreate, MetricLogRead, SLATermExtracted, SLATermRead

DIVIDER = "─" * 60


def main() -> None:
    # ── 1. Create all tables ────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("1 │ Creating tables …")
    Base.metadata.create_all(bind=engine)
    print("  ✅ Tables created: contracts, sla_terms, metric_logs")

    with SessionLocal() as session:
        # ── 2. Insert a sample Contract ─────────────────────────────────
        print(f"\n{DIVIDER}")
        print("2 │ Inserting sample Contract …")

        contract_in = ContractCreate(
            client_name="Acme Corp",
            vendor_name="CloudHost Inc",
            contract_value=500_000.00,
            active=True,
        )
        contract = Contract(**contract_in.model_dump())
        session.add(contract)
        session.flush()  # assigns id
        print(f"  ✅ {contract!r}")

        # ── 3. Insert SLA Terms ─────────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("3 │ Inserting SLA Terms …")

        # Simulate what the AI agent would return (no contract_id yet)
        extracted = [
            SLATermExtracted(
                metric_name="uptime",
                target_value=99.9,
                penalty_percentage=5.0,
                description="Vendor guarantees 99.9% monthly server uptime.",
            ),
            SLATermExtracted(
                metric_name="response_time_ms",
                target_value=200.0,
                penalty_percentage=3.0,
                description="API p95 response time must remain below 200 ms.",
            ),
        ]

        for ext in extracted:
            term = SLATerm(contract_id=contract.id, **ext.model_dump())
            session.add(term)
        session.flush()

        for t in contract.sla_terms:
            read = SLATermRead.model_validate(t)
            print(f"  ✅ {read.model_dump_json(indent=2)}")

        # ── 4. Insert Metric Logs ───────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("4 │ Inserting MetricLog entries …")

        uptime_term = contract.sla_terms[0]

        logs_data = [
            (99.95, False),   # above target → OK
            (99.85, True),    # below 99.9  → BREACH
        ]
        for value, breach in logs_data:
            log = MetricLog(
                sla_term_id=uptime_term.id,
                actual_value=value,
                breach_detected=breach,
            )
            session.add(log)
        session.flush()

        for log in uptime_term.metric_logs:
            read = MetricLogRead.model_validate(log)
            print(f"  ✅ {read.model_dump_json(indent=2)}")

        # ── 5. Query back ───────────────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("5 │ Querying relationships …")

        c = session.get(Contract, contract.id)
        assert c is not None
        print(f"  Contract : {c.client_name} ↔ {c.vendor_name}  (${c.contract_value:,.2f})")
        print(f"  SLA Terms: {len(c.sla_terms)}")
        for t in c.sla_terms:
            breaches = sum(1 for m in t.metric_logs if m.breach_detected)
            print(f"    • {t.metric_name}: target={t.target_value}, "
                  f"penalty={t.penalty_percentage}%, "
                  f"logs={len(t.metric_logs)}, breaches={breaches}")

        session.commit()

    print(f"\n{DIVIDER}")
    print("🎉  Step 1 verification complete — all models working.\n")


if __name__ == "__main__":
    main()
