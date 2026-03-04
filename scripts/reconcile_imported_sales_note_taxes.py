#!/usr/bin/env python3
"""Reconcile tax fields for historically imported sales notes.

Use when OCR import produced IEPS/IVA amounts on notes that were not invoiced.
The script only targets notes imported by `import_sales_notes_historic.py`.

Rules:
- Candidate if taxes exist but `total == subtotal` (within tolerance).
- Candidate if taxes exist but `subtotal + ieps + iva` differs from `total`.

Dry-run is default. Use --apply to persist changes.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DEFAULT_DB_URL = (
    os.getenv("DATABASE_URL")
    or "postgresql://desertbrew:desertbrew123@localhost:5432/desertbrew_sales"
)
DEFAULT_REPORT_DIR = Path("data/imports")
DEFAULT_TOLERANCE = 0.01
DEFAULT_MATH_TOLERANCE = 1.0


@dataclass
class ReconcileCandidate:
    note_id: int
    note_number: str
    subtotal: float
    ieps_total: float
    iva_total: float
    total: float
    reason: str
    math_delta: float


def _round2(value: Any) -> float:
    return round(float(value or 0.0), 2)


def load_candidates(
    db_url: str,
    equality_tolerance: float,
    math_tolerance: float,
) -> list[ReconcileCandidate]:
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    id,
                    note_number,
                    subtotal,
                    ieps_total,
                    iva_total,
                    total
                FROM sales_notes
                WHERE notes LIKE '%"import":"historic_sales_notes"%'
                ORDER BY id
                """
            )
        ).mappings().all()

    candidates: list[ReconcileCandidate] = []
    for row in rows:
        subtotal = _round2(row["subtotal"])
        ieps_total = _round2(row["ieps_total"])
        iva_total = _round2(row["iva_total"])
        total = _round2(row["total"])

        if abs(ieps_total) < equality_tolerance and abs(iva_total) < equality_tolerance:
            continue

        reason = ""
        if abs(total - subtotal) <= equality_tolerance:
            reason = "total_equals_subtotal_with_taxes"
        else:
            expected_total = round(subtotal + ieps_total + iva_total, 2)
            delta = round(expected_total - total, 2)
            if abs(delta) > math_tolerance:
                reason = "inconsistent_tax_math"

        if not reason:
            continue

        math_delta = round((subtotal + ieps_total + iva_total) - total, 2)
        candidates.append(
            ReconcileCandidate(
                note_id=int(row["id"]),
                note_number=str(row["note_number"]),
                subtotal=subtotal,
                ieps_total=ieps_total,
                iva_total=iva_total,
                total=total,
                reason=reason,
                math_delta=math_delta,
            )
        )

    return candidates


def apply_reconciliation(db_url: str, candidates: list[ReconcileCandidate]) -> tuple[int, int]:
    if not candidates:
        return 0, 0

    note_ids = [candidate.note_id for candidate in candidates]
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        note_result = conn.execute(
            text(
                """
                UPDATE sales_notes
                SET
                    include_taxes = FALSE,
                    include_ieps = FALSE,
                    include_iva = FALSE,
                    ieps_total = 0,
                    iva_total = 0,
                    total = subtotal,
                    updated_at = NOW()
                WHERE id = ANY(:note_ids)
                """
            ),
            {"note_ids": note_ids},
        )
        item_result = conn.execute(
            text(
                """
                UPDATE sales_note_items
                SET
                    ieps_amount = 0,
                    iva_amount = 0,
                    line_total = subtotal
                WHERE sales_note_id = ANY(:note_ids)
                """
            ),
            {"note_ids": note_ids},
        )
    return int(note_result.rowcount or 0), int(item_result.rowcount or 0)


def write_reports(
    report_dir: Path,
    dry_run: bool,
    db_url: str,
    candidates: list[ReconcileCandidate],
    updated_notes: int,
    updated_items: int,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
        "db_url": db_url,
        "candidates": len(candidates),
        "updated_notes": updated_notes,
        "updated_items": updated_items,
        "reasons": {
            "total_equals_subtotal_with_taxes": sum(
                1 for candidate in candidates if candidate.reason == "total_equals_subtotal_with_taxes"
            ),
            "inconsistent_tax_math": sum(
                1 for candidate in candidates if candidate.reason == "inconsistent_tax_math"
            ),
        },
    }

    mode = "dry_run" if dry_run else "applied"
    (report_dir / f"sales_notes_tax_reconciliation_{mode}.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    csv_path = report_dir / f"sales_notes_tax_reconciliation_{mode}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "note_id",
                "note_number",
                "subtotal",
                "ieps_total",
                "iva_total",
                "total",
                "math_delta",
                "reason",
            ],
        )
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(asdict(candidate))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile tax fields on historically imported sales notes."
    )
    parser.add_argument(
        "--db-url",
        default=DEFAULT_DB_URL,
        help="PostgreSQL URL for desertbrew_sales.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="Directory for reconciliation reports.",
    )
    parser.add_argument(
        "--equality-tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
        help="Tolerance to compare total vs subtotal.",
    )
    parser.add_argument(
        "--math-tolerance",
        type=float,
        default=DEFAULT_MATH_TOLERANCE,
        help="Tolerance for tax arithmetic mismatch.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes. Default is dry-run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        candidates = load_candidates(
            db_url=args.db_url,
            equality_tolerance=args.equality_tolerance,
            math_tolerance=args.math_tolerance,
        )

        updated_notes = 0
        updated_items = 0
        if args.apply:
            updated_notes, updated_items = apply_reconciliation(args.db_url, candidates)

        write_reports(
            report_dir=args.report_dir,
            dry_run=not args.apply,
            db_url=args.db_url,
            candidates=candidates,
            updated_notes=updated_notes,
            updated_items=updated_items,
        )

        print(
            json.dumps(
                {
                    "dry_run": not args.apply,
                    "candidates": len(candidates),
                    "updated_notes": updated_notes,
                    "updated_items": updated_items,
                    "report_dir": str(args.report_dir),
                },
                ensure_ascii=True,
            )
        )
        return 0
    except SQLAlchemyError as exc:
        print(
            json.dumps(
                {
                    "error": "db_connection_failed",
                    "db_url": args.db_url,
                    "detail": str(exc),
                },
                ensure_ascii=True,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
