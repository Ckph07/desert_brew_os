#!/usr/bin/env python3
"""Import historical sales notes from OCR/TXT/PDF sources into desertbrew_sales.

Design goals:
- Reproducible dry-run/apply workflow.
- Priority-aware source merge:
  gestion_pdf > ocr_txt > ocr_pdf_page.
- Conflict handling:
  identical duplicates collapse, conflicting duplicates kept with -DUPn.
- Direct PostgreSQL inserts preserving historical note numbers and timestamps.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection


SOURCE_PRIORITY: dict[str, int] = {
    "gestion_pdf": 0,
    "ocr_txt": 1,
    "ocr_pdf_page": 2,
}

DEFAULT_DB_URL = (
    os.getenv("DATABASE_URL")
    or "postgresql://desertbrew:desertbrew123@localhost:5432/desertbrew_sales"
)

DEFAULT_NOTES_ROOT = Path("docs/Notas de venta")
DEFAULT_REPORT_DIR = Path("data/imports")

DEFAULT_ISSUER = {
    "issuer_name": "Cesar Krisabd Padilla Hernandez",
    "issuer_rfc": "PAHC980207LA1",
    "issuer_address": "SERPENTIS 178",
    "issuer_phone": "8443823737",
}

MONEY_RE = re.compile(
    r"(?P<sign>-?)\s*\$?\s*(?P<num>[0-9]{1,3}(?:,[0-9]{3})*(?:\.\d{2})|[0-9]+\.\d{2})"
)
DATE_RE = re.compile(r"\b([0-3]?\d/[01]?\d/\d{2,4})\b")
NOTE_NUMBER_MAX = 9999


@dataclass
class StagedItem:
    product_name: str
    unit_measure: str
    quantity: float
    unit_price: float
    discount_pct: float = 0.0
    subtotal: float = 0.0
    ieps_amount: float = 0.0
    iva_amount: float = 0.0
    line_total: float = 0.0

    def finalize(self) -> None:
        self.quantity = round(float(self.quantity), 2)
        self.unit_price = round(float(self.unit_price), 2)
        self.discount_pct = round(float(self.discount_pct), 2)
        if self.subtotal == 0 and self.quantity != 0:
            self.subtotal = round(self.quantity * self.unit_price, 2)
        self.subtotal = round(float(self.subtotal), 2)
        self.ieps_amount = round(float(self.ieps_amount), 2)
        self.iva_amount = round(float(self.iva_amount), 2)
        if self.line_total == 0:
            self.line_total = round(self.subtotal + self.ieps_amount + self.iva_amount, 2)
        self.line_total = round(float(self.line_total), 2)


@dataclass
class StagedNote:
    source: str
    source_ref: str
    source_priority: int
    source_confidence: float
    note_number_int: int
    note_number: str
    created_at: datetime
    client_raw: str
    client_name: str
    payment_method: str
    channel: str = "B2B"
    include_taxes: bool = False
    include_ieps: bool = False
    include_iva: bool = False
    subtotal: float = 0.0
    ieps_total: float = 0.0
    iva_total: float = 0.0
    total: float = 0.0
    items: list[StagedItem] = field(default_factory=list)
    parse_flags: list[str] = field(default_factory=list)
    duplicate_suffix: Optional[str] = None
    assigned_id: Optional[int] = None
    client_id: Optional[int] = None
    conflict_rank: int = 0

    def canonical_fingerprint(self) -> str:
        items_fingerprint = [
            {
                "name": normalize_token(item.product_name),
                "qty": round(item.quantity, 2),
                "line_total": round(item.line_total, 2),
            }
            for item in self.items
        ]
        payload = {
            "date": self.created_at.strftime("%Y-%m-%d"),
            "client": normalize_token(self.client_name),
            "total": round(self.total, 2),
            "subtotal": round(self.subtotal, 2),
            "ieps": round(self.ieps_total, 2),
            "iva": round(self.iva_total, 2),
            "payment_method": self.payment_method,
            "items": items_fingerprint,
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=True)


@dataclass
class ImportIssue:
    severity: str
    source: str
    source_ref: str
    reason: str
    note_number: Optional[str] = None
    details: str = ""


@dataclass
class ImportReport:
    dry_run: bool
    notes_root: str
    db_url: str
    source_counts: dict[str, int] = field(default_factory=dict)
    parsed_notes: int = 0
    resolved_notes: int = 0
    planned_notes: int = 0
    inserted_notes: int = 0
    planned_clients: int = 0
    inserted_clients: int = 0
    planned_items: int = 0
    inserted_items: int = 0
    skipped_existing_notes: int = 0
    issues: list[ImportIssue] = field(default_factory=list)
    duplicate_rows: list[dict[str, Any]] = field(default_factory=list)
    conflict_rows: list[dict[str, Any]] = field(default_factory=list)
    planned_note_rows: list[dict[str, Any]] = field(default_factory=list)
    applied_note_rows: list[dict[str, Any]] = field(default_factory=list)
    created_client_rows: list[dict[str, Any]] = field(default_factory=list)
    validations: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def skipped_rows(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for issue in self.issues:
            if issue.severity in {"skip", "error"}:
                out.append(
                    {
                        "severity": issue.severity,
                        "source": issue.source,
                        "source_ref": issue.source_ref,
                        "note_number": issue.note_number or "",
                        "reason": issue.reason,
                        "details": issue.details,
                    }
                )
        return out


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clamp_text(value: str, max_len: int) -> str:
    value = value or ""
    value = normalize_whitespace(value)
    if len(value) <= max_len:
        return value
    return value[: max_len - 3].rstrip() + "..."


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_token(value: str) -> str:
    value = strip_accents(value or "")
    value = value.upper()
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    return normalize_whitespace(value)


def parse_money_token(raw: str) -> Optional[float]:
    match = MONEY_RE.search(raw)
    if not match:
        return None
    sign = -1 if match.group("sign") == "-" else 1
    number = float(match.group("num").replace(",", ""))
    return round(sign * number, 2)


def all_money_values(raw: str) -> list[float]:
    values: list[float] = []
    for match in MONEY_RE.finditer(raw):
        sign = -1 if match.group("sign") == "-" else 1
        number = float(match.group("num").replace(",", ""))
        values.append(round(sign * number, 2))
    return values


def parse_date_token(raw: str) -> Optional[datetime]:
    raw = raw.strip()
    match = DATE_RE.search(raw)
    if not match:
        return None
    token = match.group(1)
    try:
        day_s, month_s, year_s = token.split("/")
        day = int(day_s)
        month = int(month_s)
        year = int(year_s)
        if year < 100:
            year += 2000
        return datetime(year, month, day)
    except Exception:
        return None


def find_pdftotext() -> str:
    binary = os.getenv("PDFTOTEXT_BIN", "pdftotext")
    try:
        subprocess.run([binary, "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext not found; install poppler and ensure pdftotext is in PATH") from exc
    return binary


def read_pdf_layout_text(pdf_path: Path, pdftotext_bin: str) -> str:
    result = subprocess.run(
        [pdftotext_bin, "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"pdftotext failed for {pdf_path}: {stderr}")
    return result.stdout


def canonical_note_number(note_number_int: int) -> str:
    return f"{note_number_int:08d}"


def quality_flags_score(flags: Iterable[str]) -> float:
    penalty_map = {
        "inferred_total": 0.08,
        "inferred_subtotal": 0.06,
        "fallback_items": 0.15,
        "missing_payment_method": 0.03,
        "inferred_client_name": 0.06,
        "ocr_noise": 0.08,
    }
    penalty = 0.0
    for flag in flags:
        penalty += penalty_map.get(flag, 0.0)
    return penalty


def clean_client_raw(raw: str) -> str:
    value = raw.strip()
    if not value:
        return value
    value = re.split(r"\s{2,}", value)[0]
    value = re.split(r"\bDIRECCION\b|\bDIRECCIÓN\b|\bENTREGA\b", value, flags=re.IGNORECASE)[0]
    value = value.replace(":", " ")
    value = normalize_whitespace(value)
    return clamp_text(value, 200)


def smart_title(value: str) -> str:
    if not value:
        return value
    words = value.split()
    out: list[str] = []
    for word in words:
        if len(word) <= 3 and word.isupper():
            out.append(word)
            continue
        out.append(word.capitalize())
    return " ".join(out)


def canonicalize_client_name(raw: str) -> str:
    cleaned = clean_client_raw(raw)
    norm = normalize_token(cleaned)
    if not norm:
        return ""

    alias_rules: list[tuple[set[str], str]] = [
        ({"DESERT", "BREW", "TAP"}, "DESERT BREW TAP"),
        ({"DB", "TAP"}, "DESERT BREW TAP"),
        ({"DINOQUESADILLAS"}, "DINOQUESADILLAS"),
        ({"ASADOR", "9"}, "ASADOR 9"),
        ({"CASA", "TIYAHUI"}, "CASA TIYAHUI"),
        ({"TEC", "MILENIO"}, "TEC MILENIO"),
        ({"GRANDES", "BODEGAS"}, "GRANDES BODEGAS"),
        ({"BEER", "GARDEN"}, "BEER GARDEN"),
        ({"JURASSIC", "FOOD", "ADVENTURE"}, "JURASSIC FOOD & ADVENTURE"),
        ({"JURASSIC"}, "JURASSIC FOOD & ADVENTURE"),
        ({"DUBLIN"}, "DUBLIN"),
        ({"SEDENA"}, "SEDENA"),
        ({"TREINTATREINTA"}, "TREINTATREINTA"),
        ({"CERDO", "BABEL"}, "CERDO DE BABEL"),
        ({"ESTACION", "COYOACAN"}, "ESTACION COYOACAN"),
        ({"ESTACION", "COYOACAN"}, "ESTACION COYOACAN"),
        ({"U", "A", "A", "A", "N"}, "UAAAN"),
    ]

    tokens = set(norm.split())
    for required, canonical in alias_rules:
        if required.issubset(tokens):
            return clamp_text(canonical, 200)

    if norm.startswith("FORMA DE PAGO"):
        return ""

    return clamp_text(smart_title(norm), 200)


def normalize_payment_method(raw_text: str) -> str:
    upper = normalize_token(raw_text)
    if "EFECTIVO" in upper:
        return "EFECTIVO"
    if "TARJETA" in upper:
        return "TARJETA"
    if "CREDITO" in upper:
        return "CREDITO"
    if "TRANSFER" in upper:
        return "TRANSFERENCIA"
    return "TRANSFERENCIA"


def detect_payment_method(lines: list[str]) -> tuple[str, bool]:
    for line in lines:
        if "FORMA" in normalize_token(line) and "PAGO" in normalize_token(line):
            method = normalize_payment_method(line)
            return method, False
    return "TRANSFERENCIA", True


def extract_client_line(lines: list[str]) -> Optional[str]:
    for idx, line in enumerate(lines):
        if "CLIENTE" not in normalize_token(line):
            continue
        match = re.search(r"CLIENTE\s*:?\s*(.*)$", line, flags=re.IGNORECASE)
        if match:
            inline = clean_client_raw(match.group(1))
            if inline:
                return inline
        for jdx in range(idx + 1, min(idx + 5, len(lines))):
            candidate = clean_client_raw(lines[jdx])
            candidate_norm = normalize_token(candidate)
            if not candidate:
                continue
            if any(token in candidate_norm for token in ("DIRECCION", "TELEFONO", "CANTIDAD", "DESCRIPCION")):
                continue
            return candidate
    return None


def extract_note_number(lines: list[str]) -> Optional[int]:
    direct_candidates: list[str] = []
    sliding_candidates: list[int] = []
    for idx, line in enumerate(lines):
        norm = normalize_token(line)
        if "PEDIDO" not in norm and "NUMERO" not in norm:
            continue
        window_lines = lines[idx : idx + 10]
        filtered_window_lines: list[str] = []
        for window_line in window_lines:
            wn = normalize_token(window_line)
            if any(token in wn for token in ("RFC", "TELEFONO", "CLIENTE", "DIRECCION", "RAZON SOCIAL")):
                continue
            filtered_window_lines.append(window_line)
            for token in re.findall(r"\d{5,8}", window_line):
                direct_candidates.append(token)

        digits_joined = "".join(re.findall(r"\d", " ".join(filtered_window_lines[:5])))
        if len(digits_joined) >= 8:
            for start in range(0, len(digits_joined) - 7):
                chunk = digits_joined[start : start + 8]
                value = int(chunk)
                if 1 <= value <= NOTE_NUMBER_MAX:
                    sliding_candidates.append(value)

    if direct_candidates:
        plausible = [int(token) for token in direct_candidates if 1 <= int(token) <= NOTE_NUMBER_MAX]
        if plausible:
            return plausible[0]

        # OCR sometimes injects a leading digit in front of a zero-padded folio.
        # Example: "60000306" should become 306.
        for token in direct_candidates:
            match = re.search(r"0{3,}(\d{1,4})$", token)
            if not match:
                continue
            candidate = int(match.group(1))
            if 1 <= candidate <= NOTE_NUMBER_MAX:
                return candidate

    candidates: list[int] = []
    candidates.extend(sliding_candidates)
    if not candidates:
        global_candidates = [
            int(token)
            for token in re.findall(r"\b\d{8}\b", " ".join(lines))
            if 1 <= int(token) <= NOTE_NUMBER_MAX
        ]
        candidates.extend(global_candidates)
    if not candidates:
        return None

    ranked: list[tuple[int, int]] = []
    for value in candidates:
        # Prefer realistic order numbers first.
        plausibility = 0
        if 1 <= value <= NOTE_NUMBER_MAX:
            plausibility += 4
        if 100 <= value <= 2000:
            plausibility += 1
        ranked.append((plausibility, value))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def extract_note_date(lines: list[str]) -> Optional[datetime]:
    for idx, line in enumerate(lines):
        norm = normalize_token(line)
        if "FECHA" in norm:
            for jdx in range(idx, min(idx + 6, len(lines))):
                parsed = parse_date_token(lines[jdx])
                if parsed:
                    return parsed
    for line in lines:
        parsed = parse_date_token(line)
        if parsed:
            return parsed
    return None


def find_money_near(lines: list[str], idx: int) -> Optional[float]:
    for jdx in range(idx, min(idx + 4, len(lines))):
        values = all_money_values(lines[jdx])
        if values:
            return values[-1]
    return None


def parse_totals_from_lines(lines: list[str]) -> tuple[float, float, float, float, list[str]]:
    subtotal: Optional[float] = None
    ieps: float = 0.0
    iva: float = 0.0
    total_candidates: list[float] = []
    flags: list[str] = []

    for idx, line in enumerate(lines):
        norm = normalize_token(line)
        compact = re.sub(r"[^A-Z]", "", strip_accents(line).upper())
        if not norm:
            continue

        if "SUBTOTAL" in compact:
            money = find_money_near(lines, idx)
            if money is not None:
                subtotal = money
        elif compact in {"IEPS", "IEPSS"} or "IEPS" in compact:
            money = find_money_near(lines, idx)
            if money is not None:
                ieps = money
        elif compact in {"IVA", "IVAIMPUESTOS"} or compact.startswith("IVA"):
            money = find_money_near(lines, idx)
            if money is not None:
                iva = money
        elif "TOTAL" in compact and "SUBTOTAL" not in compact and "TOTALENVASES" not in compact:
            money = find_money_near(lines, idx)
            if money is not None:
                total_candidates.append(money)

        if "IVA:" in line.upper():
            value = parse_money_token(line)
            if value is not None:
                iva = value
        if "IEPS" in line.upper() and "$" in line:
            # Handles "Impuestos: IEPS: $0.00"
            values = all_money_values(line)
            if values:
                ieps = values[-1]

    total: Optional[float] = total_candidates[-1] if total_candidates else None

    all_values: list[float] = []
    for line in lines:
        all_values.extend(all_money_values(line))
    positive_values = [value for value in all_values if value >= 0]

    if total is None and positive_values:
        total = max(positive_values)
        flags.append("inferred_total")
    if subtotal is None:
        if total is not None:
            subtotal = round(total - ieps - iva, 2)
            flags.append("inferred_subtotal")
        elif positive_values:
            subtotal = max(positive_values)
            flags.append("inferred_subtotal")
    if total is None and subtotal is not None:
        total = round(subtotal + ieps + iva, 2)
        flags.append("inferred_total")

    return (
        round(float(subtotal or 0), 2),
        round(float(ieps or 0), 2),
        round(float(iva or 0), 2),
        round(float(total or 0), 2),
        flags,
    )


def detect_unit_measure(description: str) -> str:
    norm = normalize_token(description)
    if "LITRO" in norm or re.search(r"\b\d+\s*L\b", norm):
        return "LITROS"
    if "BARRIL" in norm or "KEYKEG" in norm:
        return "KEGS"
    return "UNITS"


def extract_unit_price(description: str) -> Optional[float]:
    match = re.search(r"P\.?\s*U(?:NIT)?\.?\s*\$?\s*([0-9][0-9,]*\.?[0-9]*)", description, flags=re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).replace(",", "")
    if raw.count(".") == 0:
        return round(float(raw), 2)
    return round(float(raw), 2)


def clean_item_description(description: str) -> str:
    description = normalize_whitespace(description)
    description = re.sub(
        r"\bP\.?\s*U(?:NIT)?\.?\s*\$?\s*[0-9][0-9,]*\.?[0-9]*\b",
        "",
        description,
        flags=re.IGNORECASE,
    )
    description = description.replace("  ", " ").strip(" -")
    return clamp_text(normalize_whitespace(description), 200)


def build_item(
    quantity: float,
    description: str,
    line_total: Optional[float],
    unit_price: Optional[float],
) -> StagedItem:
    quantity = float(quantity or 0)
    if quantity == 0:
        quantity = 1.0
    if unit_price is None and line_total is not None:
        unit_price = line_total / quantity
    if unit_price is None:
        unit_price = 0.0

    if line_total is None:
        line_total = quantity * unit_price

    item = StagedItem(
        product_name=clamp_text(clean_item_description(description) or "Concepto historico", 200),
        unit_measure=detect_unit_measure(description),
        quantity=quantity,
        unit_price=unit_price,
        subtotal=line_total,
        line_total=line_total,
    )
    item.finalize()
    return item


def extract_table_region(lines: list[str]) -> list[str]:
    start = None
    end = None
    for idx, line in enumerate(lines):
        norm = normalize_token(line)
        if start is None and ("CANTIDAD" in norm or "DESCRIPCION" in norm):
            start = idx + 1
            continue
        if start is not None:
            compact = re.sub(r"[^A-Z]", "", strip_accents(line).upper())
            if "SUBTOTAL" in compact or compact.startswith("TOTAL") or "IEPS" in compact or "IVA" in compact:
                end = idx
                break
    if start is None:
        return []
    if end is None:
        end = len(lines)
    return [line for line in lines[start:end] if normalize_whitespace(line)]


def parse_items_row_based(table_lines: list[str]) -> list[StagedItem]:
    items: list[StagedItem] = []
    idx = 0

    while idx < len(table_lines):
        line = normalize_whitespace(table_lines[idx])
        if not line:
            idx += 1
            continue

        # Discounts/bonifications often come without quantity.
        if "BONIFIC" in normalize_token(line) or "DESCUENTO" in normalize_token(line):
            amount = parse_money_token(line)
            consumed = 1
            if amount is None and idx + 1 < len(table_lines):
                amount = parse_money_token(table_lines[idx + 1])
                if amount is not None:
                    consumed = 2
            if amount is not None:
                amount = -abs(amount)
                item = build_item(1.0, "Bonificacion", amount, amount)
                items.append(item)
                idx += consumed
                continue

        # Pattern: "<qty> <desc> <line_total>"
        full_match = re.match(
            r"^\s*(-?\d+(?:\.\d+)?)\s+(.+?)\s+(-?\$?\s*[0-9][0-9,]*\.\d{2})\s*$",
            line,
            flags=re.IGNORECASE,
        )
        if full_match:
            qty = float(full_match.group(1))
            desc = full_match.group(2)
            line_total = parse_money_token(full_match.group(3))
            unit_price = extract_unit_price(desc)
            items.append(build_item(qty, desc, line_total, unit_price))
            idx += 1
            continue

        # Pattern: "<qty> <desc>" followed by price lines.
        qty_desc_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s+(.+)$", line)
        if qty_desc_match:
            qty = float(qty_desc_match.group(1))
            desc_parts = [qty_desc_match.group(2)]
            line_total = parse_money_token(line)
            consumed = 1
            for jdx in range(idx + 1, min(idx + 5, len(table_lines))):
                candidate = normalize_whitespace(table_lines[jdx])
                if not candidate:
                    continue
                if re.match(r"^\s*-?\d+(?:\.\d+)?\s+.+$", candidate):
                    break
                candidate_money = parse_money_token(candidate)
                if candidate_money is not None and line_total is None:
                    line_total = candidate_money
                    consumed = jdx - idx + 1
                    break
                if candidate_money is None:
                    desc_parts.append(candidate)
                    consumed = jdx - idx + 1
            desc = " ".join(desc_parts)
            unit_price = extract_unit_price(desc)
            items.append(build_item(qty, desc, line_total, unit_price))
            idx += consumed
            continue

        # Pattern: price-only line can belong to previous item.
        price_only = re.match(r"^\s*-?\$?\s*[0-9][0-9,]*\.\d{2}\s*$", line)
        if price_only and items and items[-1].line_total == items[-1].subtotal:
            amount = parse_money_token(line)
            if amount is not None and items[-1].line_total == 0:
                items[-1].line_total = amount
                items[-1].subtotal = amount
                items[-1].finalize()
            idx += 1
            continue

        # Append trailing description chunks to last item when OCR wrapped lines.
        if items and parse_money_token(line) is None:
            joined = f"{items[-1].product_name} {line}"
            items[-1].product_name = clean_item_description(joined)
            items[-1].unit_measure = detect_unit_measure(items[-1].product_name)
            idx += 1
            continue

        idx += 1

    # Remove obvious accidental empty concepts.
    out: list[StagedItem] = []
    for item in items:
        if normalize_token(item.product_name) in {"PRECIO", "DESCRIPCION", "CANTIDAD"}:
            continue
        out.append(item)
    return out


def parse_items_columnar(table_lines: list[str], total: float) -> list[StagedItem]:
    qty_values: list[float] = []
    desc_values: list[str] = []
    line_prices: list[float] = []
    unit_prices: list[float] = []

    for raw in table_lines:
        line = normalize_whitespace(raw)
        if not line:
            continue
        norm = normalize_token(line)
        if norm in {"CANTIDAD", "DESCRIPCION", "PRECIO"}:
            continue

        qty_match = re.match(r"^(-?\d+(?:\.\d+)?)\s*(?:U|UNITS?|L|LTS?)?$", line, flags=re.IGNORECASE)
        if qty_match:
            qty_values.append(float(qty_match.group(1)))
            continue

        money_values = all_money_values(line)
        if money_values and re.match(r"^\s*-?\$?\s*[0-9][0-9,]*\.\d{2}\s*$", line):
            line_prices.append(money_values[-1])
            continue

        extracted_unit = extract_unit_price(line)
        if extracted_unit is not None:
            unit_prices.append(extracted_unit)

        has_letters = bool(re.search(r"[A-Za-z]", line))
        if has_letters:
            desc_values.append(line)

    count = max(len(qty_values), len(desc_values), len(line_prices), len(unit_prices))
    if count == 0:
        return []

    items: list[StagedItem] = []
    for idx in range(count):
        qty = qty_values[idx] if idx < len(qty_values) else 1.0
        desc = desc_values[idx] if idx < len(desc_values) else "Concepto historico"
        line_total = line_prices[idx] if idx < len(line_prices) else None
        unit_price = unit_prices[idx] if idx < len(unit_prices) else None
        items.append(build_item(qty, desc, line_total, unit_price))

    # If OCR gave impossible table, keep one fallback with reliable total.
    if not items and total != 0:
        return [build_item(1.0, "Importe historico (sin detalle OCR)", total, total)]
    return items


def parse_items(lines: list[str], total: float) -> tuple[list[StagedItem], bool]:
    table_lines = extract_table_region(lines)
    if not table_lines:
        if total != 0:
            return [build_item(1.0, "Importe historico (sin detalle OCR)", total, total)], True
        return [], True

    items = parse_items_row_based(table_lines)
    if items:
        return items, False
    columnar = parse_items_columnar(table_lines, total=total)
    if columnar:
        return columnar, False
    if total != 0:
        return [build_item(1.0, "Importe historico (sin detalle OCR)", total, total)], True
    return [], True


def distribute_header_taxes(note: StagedNote) -> None:
    if not note.items:
        return
    total_subtotal = sum(max(item.subtotal, 0) for item in note.items)
    if total_subtotal <= 0:
        return

    if note.ieps_total > 0 and sum(abs(item.ieps_amount) for item in note.items) == 0:
        distributed = 0.0
        for item in note.items[:-1]:
            ratio = item.subtotal / total_subtotal
            item.ieps_amount = round(note.ieps_total * ratio, 2)
            distributed += item.ieps_amount
        note.items[-1].ieps_amount = round(note.ieps_total - distributed, 2)

    if note.iva_total > 0 and sum(abs(item.iva_amount) for item in note.items) == 0:
        distributed = 0.0
        for item in note.items[:-1]:
            ratio = item.subtotal / total_subtotal
            item.iva_amount = round(note.iva_total * ratio, 2)
            distributed += item.iva_amount
        note.items[-1].iva_amount = round(note.iva_total - distributed, 2)

    for item in note.items:
        item.line_total = round(item.subtotal + item.ieps_amount + item.iva_amount, 2)
        item.finalize()


def normalize_note_financials(note: StagedNote) -> None:
    for item in note.items:
        item.finalize()

    if not note.items:
        note.items = [build_item(1.0, "Importe historico (sin detalle OCR)", note.total, note.total)]
        note.parse_flags.append("fallback_items")

    if note.subtotal == 0 and "inferred_subtotal" in note.parse_flags:
        note.subtotal = round(sum(item.subtotal for item in note.items), 2)
    if note.total == 0 and "inferred_total" in note.parse_flags:
        note.total = round(note.subtotal + note.ieps_total + note.iva_total, 2)

    distribute_header_taxes(note)

    # Keep header totals authoritative; adjust last line if OCR rounding differs.
    lines_total = round(sum(item.line_total for item in note.items), 2)
    target_total = round(note.total, 2)
    delta = round(target_total - lines_total, 2)
    if note.items and abs(delta) >= 0.01:
        note.items[-1].line_total = round(note.items[-1].line_total + delta, 2)
        note.items[-1].subtotal = round(
            note.items[-1].line_total - note.items[-1].ieps_amount - note.items[-1].iva_amount,
            2,
        )
        note.items[-1].unit_price = round(note.items[-1].subtotal / max(note.items[-1].quantity, 1), 2)
        note.items[-1].finalize()

    note.subtotal = round(note.subtotal, 2)
    note.ieps_total = round(note.ieps_total, 2)
    note.iva_total = round(note.iva_total, 2)
    note.total = round(note.total, 2)
    note.include_ieps = abs(note.ieps_total) > 0.0
    note.include_iva = abs(note.iva_total) > 0.0
    note.include_taxes = note.include_ieps or note.include_iva


def parse_text_like_note(
    content: str,
    source: str,
    source_ref: str,
    base_confidence: float,
) -> tuple[Optional[StagedNote], list[ImportIssue]]:
    issues: list[ImportIssue] = []
    lines = [line.rstrip() for line in content.splitlines() if line.strip()]
    if not lines:
        issues.append(
            ImportIssue(
                severity="skip",
                source=source,
                source_ref=source_ref,
                reason="empty_document",
                details="No usable lines in source file/page.",
            )
        )
        return None, issues

    note_number_int = extract_note_number(lines)
    date = extract_note_date(lines)
    client_raw = extract_client_line(lines) or ""
    client_name = canonicalize_client_name(client_raw)
    payment_method, payment_missing = detect_payment_method(lines)
    subtotal, ieps_total, iva_total, total, total_flags = parse_totals_from_lines(lines)
    items, fallback_items = parse_items(lines, total=total)

    parse_flags: list[str] = list(total_flags)
    if payment_missing:
        parse_flags.append("missing_payment_method")
    if fallback_items:
        parse_flags.append("fallback_items")
    if len(lines) < 4:
        parse_flags.append("ocr_noise")
    if not client_name:
        parse_flags.append("inferred_client_name")

    if note_number_int is None:
        issues.append(
            ImportIssue(
                severity="skip",
                source=source,
                source_ref=source_ref,
                reason="missing_note_number",
                details="Could not parse note number from document.",
            )
        )
        return None, issues

    if date is None:
        issues.append(
            ImportIssue(
                severity="skip",
                source=source,
                source_ref=source_ref,
                reason="missing_date",
                note_number=canonical_note_number(note_number_int),
                details="Could not parse date from document.",
            )
        )
        return None, issues

    if not client_name:
        issues.append(
            ImportIssue(
                severity="skip",
                source=source,
                source_ref=source_ref,
                reason="missing_client",
                note_number=canonical_note_number(note_number_int),
                details="Could not parse client from document.",
            )
        )
        return None, issues

    inferred_totals = ("inferred_total" in parse_flags) or ("inferred_subtotal" in parse_flags)
    if total == 0 and subtotal == 0 and items and inferred_totals:
        subtotal = round(sum(item.subtotal for item in items), 2)
        total = round(sum(item.line_total for item in items), 2)
        parse_flags.append("inferred_subtotal")
        parse_flags.append("inferred_total")

    if total <= 0 and subtotal <= 0 and not items:
        issues.append(
            ImportIssue(
                severity="skip",
                source=source,
                source_ref=source_ref,
                reason="missing_total",
                note_number=canonical_note_number(note_number_int),
                details="Could not parse a reliable total amount.",
            )
        )
        return None, issues

    note = StagedNote(
        source=source,
        source_ref=source_ref,
        source_priority=SOURCE_PRIORITY[source],
        source_confidence=max(0.0, round(base_confidence - quality_flags_score(parse_flags), 3)),
        note_number_int=note_number_int,
        note_number=canonical_note_number(note_number_int),
        created_at=date,
        client_raw=client_raw or client_name,
        client_name=client_name,
        payment_method=payment_method,
        include_taxes=(abs(ieps_total) > 0) or (abs(iva_total) > 0),
        include_ieps=abs(ieps_total) > 0,
        include_iva=abs(iva_total) > 0,
        subtotal=subtotal,
        ieps_total=ieps_total,
        iva_total=iva_total,
        total=total,
        items=items,
        parse_flags=parse_flags,
    )
    normalize_note_financials(note)
    return note, issues


def parse_gestion_pdf(path: Path, pdftotext_bin: str) -> tuple[Optional[StagedNote], list[ImportIssue]]:
    content = read_pdf_layout_text(path, pdftotext_bin)
    note, issues = parse_text_like_note(
        content=content,
        source="gestion_pdf",
        source_ref=str(path),
        base_confidence=0.96,
    )
    return note, issues


def parse_ocr_txt(path: Path) -> tuple[Optional[StagedNote], list[ImportIssue]]:
    content = path.read_text(errors="ignore")
    return parse_text_like_note(
        content=content,
        source="ocr_txt",
        source_ref=str(path),
        base_confidence=0.90,
    )


def parse_ocr_pdf_pages(pdf_path: Path, pdftotext_bin: str) -> tuple[list[StagedNote], list[ImportIssue]]:
    issues: list[ImportIssue] = []
    notes: list[StagedNote] = []
    content = read_pdf_layout_text(pdf_path, pdftotext_bin)
    pages = content.split("\f")

    for idx, page in enumerate(pages, start=1):
        if not page.strip():
            continue
        note, page_issues = parse_text_like_note(
            content=page,
            source="ocr_pdf_page",
            source_ref=f"{pdf_path}#page={idx}",
            base_confidence=0.75,
        )
        if note:
            notes.append(note)
        issues.extend(page_issues)
    return notes, issues


def scan_sources(notes_root: Path) -> tuple[list[StagedNote], list[ImportIssue], dict[str, int]]:
    pdftotext_bin = find_pdftotext()
    issues: list[ImportIssue] = []
    notes: list[StagedNote] = []
    source_counts: dict[str, int] = Counter()

    gestion_dir = notes_root / "notas_gestion_Cervecera"
    if gestion_dir.exists():
        for pdf_path in sorted(gestion_dir.glob("*.pdf")):
            note, note_issues = parse_gestion_pdf(pdf_path, pdftotext_bin=pdftotext_bin)
            if note:
                notes.append(note)
                source_counts["gestion_pdf"] += 1
            issues.extend(note_issues)
    else:
        issues.append(
            ImportIssue(
                severity="error",
                source="gestion_pdf",
                source_ref=str(gestion_dir),
                reason="missing_source_directory",
                details="Directory not found.",
            )
        )

    txt_dir = notes_root / "notas"
    if txt_dir.exists():
        for txt_path in sorted(txt_dir.glob("*.txt"), key=lambda p: (len(p.stem), p.stem)):
            note, note_issues = parse_ocr_txt(txt_path)
            if note:
                notes.append(note)
                source_counts["ocr_txt"] += 1
            issues.extend(note_issues)
    else:
        issues.append(
            ImportIssue(
                severity="error",
                source="ocr_txt",
                source_ref=str(txt_dir),
                reason="missing_source_directory",
                details="Directory not found.",
            )
        )

    ocr_pdf = notes_root / "Notas de venta__OCR.pdf"
    if ocr_pdf.exists():
        pdf_notes, pdf_issues = parse_ocr_pdf_pages(ocr_pdf, pdftotext_bin=pdftotext_bin)
        notes.extend(pdf_notes)
        source_counts["ocr_pdf_page"] = len(pdf_notes)
        issues.extend(pdf_issues)
    else:
        issues.append(
            ImportIssue(
                severity="error",
                source="ocr_pdf_page",
                source_ref=str(ocr_pdf),
                reason="missing_source_file",
                details="OCR PDF not found.",
            )
        )

    return notes, issues, dict(source_counts)


def deduplicate_notes(notes: list[StagedNote], issues: list[ImportIssue]) -> tuple[list[StagedNote], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[int, list[StagedNote]] = defaultdict(list)
    for note in notes:
        grouped[note.note_number_int].append(note)

    deduped: list[StagedNote] = []
    duplicate_rows: list[dict[str, Any]] = []
    conflict_rows: list[dict[str, Any]] = []

    for note_number_int in sorted(grouped.keys()):
        group = grouped[note_number_int]
        group.sort(
            key=lambda note: (
                note.source_priority,
                -note.source_confidence,
                note.source_ref,
            )
        )
        canonical = group[0]
        canonical.note_number = canonical_note_number(note_number_int)
        deduped.append(canonical)

        canonical_fingerprint = canonical.canonical_fingerprint()
        conflict_index = 0
        for candidate in group[1:]:
            same_client = normalize_token(candidate.client_name) == normalize_token(canonical.client_name)
            same_date = candidate.created_at.date() == canonical.created_at.date()
            same_total = abs(candidate.total - canonical.total) <= 0.01
            same = same_client and same_date and same_total
            if not same:
                same = candidate.canonical_fingerprint() == canonical_fingerprint
            if same:
                duplicate_rows.append(
                    {
                        "note_number": canonical_note_number(note_number_int),
                        "type": "identical_collapsed",
                        "kept_source": canonical.source,
                        "kept_ref": canonical.source_ref,
                        "discarded_source": candidate.source,
                        "discarded_ref": candidate.source_ref,
                    }
                )
                issues.append(
                    ImportIssue(
                        severity="info",
                        source=candidate.source,
                        source_ref=candidate.source_ref,
                        reason="duplicate_identical_collapsed",
                        note_number=canonical_note_number(note_number_int),
                        details=f"Kept canonical source {canonical.source}:{canonical.source_ref}.",
                    )
                )
                continue

            conflict_index += 1
            candidate.conflict_rank = conflict_index
            candidate.duplicate_suffix = f"DUP{conflict_index}"
            candidate.note_number = f"{canonical_note_number(note_number_int)}-{candidate.duplicate_suffix}"
            deduped.append(candidate)

            row = {
                "note_number": canonical_note_number(note_number_int),
                "conflict_note_number": candidate.note_number,
                "primary_source": canonical.source,
                "primary_ref": canonical.source_ref,
                "conflict_source": candidate.source,
                "conflict_ref": candidate.source_ref,
                "reason": "same_note_number_different_payload",
            }
            duplicate_rows.append(
                {
                    **row,
                    "type": "conflict_kept",
                    "kept_source": candidate.source,
                    "kept_ref": candidate.source_ref,
                    "discarded_source": "",
                    "discarded_ref": "",
                }
            )
            conflict_rows.append(row)
            issues.append(
                ImportIssue(
                    severity="warning",
                    source=candidate.source,
                    source_ref=candidate.source_ref,
                    reason="duplicate_conflict_kept",
                    note_number=candidate.note_number,
                    details=(
                        f"Preserved conflict against canonical {canonical.note_number}. "
                        f"Stored as {candidate.note_number}."
                    ),
                )
            )

    deduped.sort(key=lambda note: (note.note_number_int, note.conflict_rank, note.source_priority, note.source_ref))
    return deduped, duplicate_rows, conflict_rows


def metadata_note(note: StagedNote) -> str:
    payload = {
        "import": "historic_sales_notes",
        "source": note.source,
        "ref": note.source_ref,
        "confidence": round(note.source_confidence, 3),
        "flags": note.parse_flags,
    }
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    if len(raw) > 480:
        raw = raw[:477] + "..."
    return raw


def next_client_code(existing_codes: list[str]) -> int:
    max_code = 0
    for code in existing_codes:
        match = re.match(r"CLI-(\d+)$", code or "")
        if not match:
            continue
        max_code = max(max_code, int(match.group(1)))
    return max_code + 1


def load_existing_clients(conn: Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute(text("SELECT id, business_name, client_code FROM clients")).mappings().all()
    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        normalized = normalize_token(row["business_name"] or "")
        if not normalized:
            continue
        mapping[normalized] = {"id": int(row["id"]), "business_name": row["business_name"], "client_code": row["client_code"]}
    return mapping


def resolve_clients(
    conn: Connection,
    notes: list[StagedNote],
    apply: bool,
    report: ImportReport,
) -> None:
    client_map = load_existing_clients(conn)
    existing_codes = [row["client_code"] for row in client_map.values()]
    next_code = next_client_code(existing_codes)
    max_client_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM clients")).scalar_one()
    predicted_client_id = int(max_client_id)

    unique_names = sorted({note.client_name for note in notes if note.client_name})
    for name in unique_names:
        normalized = normalize_token(name)
        if normalized in client_map:
            continue

        client_code = f"CLI-{next_code:04d}"
        next_code += 1

        if apply:
            result = conn.execute(
                text(
                    """
                    INSERT INTO clients (
                        client_code, business_name, client_type, pricing_tier,
                        current_balance, current_kegs, is_active, created_at, updated_at
                    ) VALUES (
                        :client_code, :business_name, 'B2B', 'RETAIL',
                        0, 0, true, :created_at, :updated_at
                    )
                    RETURNING id
                    """
                ),
                {
                    "client_code": client_code,
                    "business_name": name,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            client_id = int(result.scalar_one())
            report.inserted_clients += 1
        else:
            predicted_client_id += 1
            client_id = predicted_client_id

        client_map[normalized] = {"id": client_id, "business_name": name, "client_code": client_code}
        report.planned_clients += 1
        report.created_client_rows.append(
            {
                "client_id": client_id,
                "client_code": client_code,
                "business_name": name,
                "applied": apply,
            }
        )

    for note in notes:
        normalized = normalize_token(note.client_name)
        if normalized in client_map:
            note.client_id = int(client_map[normalized]["id"])
        else:
            # Should not happen after resolve, but keep safe.
            note.client_id = None


def load_existing_note_state(conn: Connection) -> tuple[set[str], set[int], int]:
    rows = conn.execute(text("SELECT id, note_number FROM sales_notes")).mappings().all()
    note_numbers = {row["note_number"] for row in rows}
    note_ids = {int(row["id"]) for row in rows}
    max_id = max(note_ids) if note_ids else 0
    return note_numbers, note_ids, max_id


def assign_note_ids(notes: list[StagedNote], used_ids: set[int], starting_max_id: int) -> int:
    max_id = int(starting_max_id)

    # First pass: reserve canonical numeric ids whenever possible.
    canonical_max = max_id
    for note in notes:
        if note.duplicate_suffix is not None:
            continue
        if note.note_number_int in used_ids:
            continue
        note.assigned_id = note.note_number_int
        used_ids.add(note.assigned_id)
        canonical_max = max(canonical_max, note.assigned_id)

    # Second pass: assign synthetic ids only to duplicates/collisions,
    # starting above the highest reserved canonical id.
    max_id = canonical_max
    for note in notes:
        if note.assigned_id is not None:
            continue

        while True:
            max_id += 1
            if max_id not in used_ids:
                note.assigned_id = max_id
                used_ids.add(max_id)
                break
    return max_id


def calculate_total_liters(items: list[StagedItem]) -> float:
    liters = 0.0
    for item in items:
        if item.unit_measure.upper() in {"LITROS", "L"}:
            liters += item.quantity
    return round(liters, 2)


def insert_sales_note(conn: Connection, note: StagedNote) -> None:
    conn.execute(
        text(
            """
            INSERT INTO sales_notes (
                id, note_number, client_id, client_name,
                issuer_name, issuer_rfc, issuer_address, issuer_phone,
                include_taxes, include_ieps, include_iva,
                subtotal, ieps_total, iva_total, total, total_liters,
                channel, payment_method, payment_status, status, notes, created_by,
                confirmed_at, cancelled_at, created_at, updated_at, paid_at
            ) VALUES (
                :id, :note_number, :client_id, :client_name,
                :issuer_name, :issuer_rfc, :issuer_address, :issuer_phone,
                :include_taxes, :include_ieps, :include_iva,
                :subtotal, :ieps_total, :iva_total, :total, :total_liters,
                :channel, :payment_method, 'PENDING', 'CONFIRMED', :notes, 'historic_import',
                :confirmed_at, NULL, :created_at, :updated_at, NULL
            )
            """
        ),
        {
            "id": note.assigned_id,
            "note_number": note.note_number,
            "client_id": note.client_id,
            "client_name": note.client_name,
            "issuer_name": DEFAULT_ISSUER["issuer_name"],
            "issuer_rfc": DEFAULT_ISSUER["issuer_rfc"],
            "issuer_address": DEFAULT_ISSUER["issuer_address"],
            "issuer_phone": DEFAULT_ISSUER["issuer_phone"],
            "include_taxes": note.include_taxes,
            "include_ieps": note.include_ieps,
            "include_iva": note.include_iva,
            "subtotal": note.subtotal,
            "ieps_total": note.ieps_total,
            "iva_total": note.iva_total,
            "total": note.total,
            "total_liters": calculate_total_liters(note.items),
            "channel": note.channel,
            "payment_method": note.payment_method,
            "notes": metadata_note(note),
            "confirmed_at": note.created_at,
            "created_at": note.created_at,
            "updated_at": note.created_at,
        },
    )

    for item in note.items:
        conn.execute(
            text(
                """
                INSERT INTO sales_note_items (
                    sales_note_id, product_id, sku, product_name, unit_measure,
                    quantity, unit_price, discount_pct, subtotal, ieps_amount, iva_amount, line_total
                ) VALUES (
                    :sales_note_id, NULL, NULL, :product_name, :unit_measure,
                    :quantity, :unit_price, :discount_pct, :subtotal, :ieps_amount, :iva_amount, :line_total
                )
                """
            ),
            {
                "sales_note_id": note.assigned_id,
                "product_name": item.product_name,
                "unit_measure": item.unit_measure,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount_pct": item.discount_pct,
                "subtotal": item.subtotal,
                "ieps_amount": item.ieps_amount,
                "iva_amount": item.iva_amount,
                "line_total": item.line_total,
            },
        )


def sync_sequences(conn: Connection) -> None:
    if conn.dialect.name != "postgresql":
        return
    conn.execute(
        text(
            """
            SELECT setval(pg_get_serial_sequence('clients', 'id'),
                          GREATEST((SELECT COALESCE(MAX(id), 1) FROM clients), 1),
                          true)
            """
        )
    )
    conn.execute(
        text(
            """
            SELECT setval(pg_get_serial_sequence('sales_notes', 'id'),
                          GREATEST((SELECT COALESCE(MAX(id), 1) FROM sales_notes), 1),
                          true)
            """
        )
    )
    conn.execute(
        text(
            """
            SELECT setval(pg_get_serial_sequence('sales_note_items', 'id'),
                          GREATEST((SELECT COALESCE(MAX(id), 1) FROM sales_note_items), 1),
                          true)
            """
        )
    )


def validate_post_import(conn: Connection) -> dict[str, Any]:
    duplicate_note_numbers = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM (
                SELECT note_number
                FROM sales_notes
                GROUP BY note_number
                HAVING COUNT(*) > 1
            ) t
            """
        )
    ).scalar_one()
    notes_count = int(conn.execute(text("SELECT COUNT(*) FROM sales_notes")).scalar_one())
    items_count = int(conn.execute(text("SELECT COUNT(*) FROM sales_note_items")).scalar_one())
    orphan_items = int(
        conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM sales_note_items i
                LEFT JOIN sales_notes n ON n.id = i.sales_note_id
                WHERE n.id IS NULL
                """
            )
        ).scalar_one()
    )
    max_note_id = int(conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM sales_notes")).scalar_one())
    next_auto = canonical_note_number(max_note_id + 1)
    return {
        "duplicate_note_number_groups": int(duplicate_note_numbers),
        "sales_notes_count": notes_count,
        "sales_note_items_count": items_count,
        "orphan_items": orphan_items,
        "max_note_id": max_note_id,
        "next_autogenerated_note_number": next_auto,
    }


def run_import(notes_root: Path, db_url: str, apply: bool, report_dir: Path) -> ImportReport:
    parsed_notes, issues, source_counts = scan_sources(notes_root)
    fallback_blockers = {
        note.note_number_int
        for note in parsed_notes
        if note.source in {"gestion_pdf", "ocr_txt"}
    }
    filtered_notes: list[StagedNote] = []
    for note in parsed_notes:
        if note.source == "ocr_pdf_page" and note.note_number_int in fallback_blockers:
            issues.append(
                ImportIssue(
                    severity="info",
                    source=note.source,
                    source_ref=note.source_ref,
                    reason="fallback_not_needed",
                    note_number=canonical_note_number(note.note_number_int),
                    details="Dropped OCR page because same note number exists in higher-priority source.",
                )
            )
            continue
        filtered_notes.append(note)

    parsed_notes = filtered_notes
    deduped_notes, duplicate_rows, conflict_rows = deduplicate_notes(parsed_notes, issues)

    report = ImportReport(
        dry_run=not apply,
        notes_root=str(notes_root),
        db_url=db_url,
        source_counts=source_counts,
        parsed_notes=len(parsed_notes),
        resolved_notes=len(deduped_notes),
        duplicate_rows=duplicate_rows,
        conflict_rows=conflict_rows,
        issues=issues,
    )

    engine = create_engine(db_url, pool_pre_ping=True)

    if apply:
        with engine.begin() as conn:
            resolve_clients(conn, deduped_notes, apply=True, report=report)

            existing_note_numbers, used_note_ids, max_id = load_existing_note_state(conn)
            max_id = assign_note_ids(deduped_notes, used_ids=used_note_ids, starting_max_id=max_id)

            for note in deduped_notes:
                if note.note_number in existing_note_numbers:
                    report.skipped_existing_notes += 1
                    report.issues.append(
                        ImportIssue(
                            severity="info",
                            source=note.source,
                            source_ref=note.source_ref,
                            reason="already_exists",
                            note_number=note.note_number,
                            details="Skipped because note_number already exists in DB.",
                        )
                    )
                    continue

                report.planned_notes += 1
                report.planned_items += len(note.items)
                report.planned_note_rows.append(
                    {
                        "note_number": note.note_number,
                        "assigned_id": note.assigned_id,
                        "client_name": note.client_name,
                        "source": note.source,
                        "source_ref": note.source_ref,
                        "total": note.total,
                    }
                )

                insert_sales_note(conn, note)
                existing_note_numbers.add(note.note_number)
                report.inserted_notes += 1
                report.inserted_items += len(note.items)
                report.applied_note_rows.append(
                    {
                        "note_number": note.note_number,
                        "inserted_id": note.assigned_id,
                        "client_name": note.client_name,
                        "source": note.source,
                        "total": note.total,
                    }
                )

            sync_sequences(conn)
            report.validations = validate_post_import(conn)
    else:
        with engine.connect() as conn:
            resolve_clients(conn, deduped_notes, apply=False, report=report)

            existing_note_numbers, used_note_ids, max_id = load_existing_note_state(conn)
            assign_note_ids(deduped_notes, used_ids=used_note_ids, starting_max_id=max_id)

            for note in deduped_notes:
                if note.note_number in existing_note_numbers:
                    report.skipped_existing_notes += 1
                    report.issues.append(
                        ImportIssue(
                            severity="info",
                            source=note.source,
                            source_ref=note.source_ref,
                            reason="already_exists",
                            note_number=note.note_number,
                            details="Would be skipped because note_number already exists in DB.",
                        )
                    )
                    continue
                report.planned_notes += 1
                report.planned_items += len(note.items)
                report.planned_note_rows.append(
                    {
                        "note_number": note.note_number,
                        "assigned_id": note.assigned_id,
                        "client_name": note.client_name,
                        "source": note.source,
                        "source_ref": note.source_ref,
                        "total": note.total,
                    }
                )

            report.validations = validate_post_import(conn)

    write_reports(report=report, report_dir=report_dir)
    return report


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def write_reports(report: ImportReport, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)

    plan_payload = {
        "generated_at": report.generated_at,
        "dry_run": report.dry_run,
        "notes_root": report.notes_root,
        "source_counts": report.source_counts,
        "parsed_notes": report.parsed_notes,
        "resolved_notes": report.resolved_notes,
        "planned_notes": report.planned_notes,
        "planned_items": report.planned_items,
        "planned_clients": report.planned_clients,
        "skipped_existing_notes": report.skipped_existing_notes,
        "planned_rows": report.planned_note_rows,
        "created_clients": report.created_client_rows,
        "issues": [asdict(issue) for issue in report.issues],
    }
    (report_dir / "sales_notes_import_plan.json").write_text(
        json.dumps(plan_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    applied_payload = {
        "generated_at": report.generated_at,
        "dry_run": report.dry_run,
        "inserted_notes": report.inserted_notes,
        "inserted_items": report.inserted_items,
        "inserted_clients": report.inserted_clients,
        "applied_rows": report.applied_note_rows,
        "validations": report.validations,
        "issues": [asdict(issue) for issue in report.issues],
    }
    (report_dir / "sales_notes_import_applied.json").write_text(
        json.dumps(applied_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    write_csv(
        report_dir / "sales_notes_import_duplicates.csv",
        report.duplicate_rows,
        headers=[
            "note_number",
            "type",
            "kept_source",
            "kept_ref",
            "discarded_source",
            "discarded_ref",
            "conflict_note_number",
            "primary_source",
            "primary_ref",
            "conflict_source",
            "conflict_ref",
            "reason",
        ],
    )

    write_csv(
        report_dir / "sales_notes_import_conflicts.csv",
        report.conflict_rows,
        headers=[
            "note_number",
            "conflict_note_number",
            "primary_source",
            "primary_ref",
            "conflict_source",
            "conflict_ref",
            "reason",
        ],
    )

    write_csv(
        report_dir / "sales_notes_import_skipped.csv",
        report.skipped_rows(),
        headers=["severity", "source", "source_ref", "note_number", "reason", "details"],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import historical sales notes from OCR/TXT/PDF sources into desertbrew_sales."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to database. Default is dry-run.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (default).",
    )
    parser.add_argument(
        "--notes-root",
        type=Path,
        default=DEFAULT_NOTES_ROOT,
        help=f"Root directory containing notes sources (default: {DEFAULT_NOTES_ROOT}).",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=DEFAULT_DB_URL,
        help="Database URL for desertbrew_sales.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"Directory for audit reports (default: {DEFAULT_REPORT_DIR}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apply = bool(args.apply)

    report = run_import(
        notes_root=args.notes_root,
        db_url=args.db_url,
        apply=apply,
        report_dir=args.report_dir,
    )

    mode_label = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode_label}] parsed={report.parsed_notes} resolved={report.resolved_notes}")
    print(
        f"[{mode_label}] planned_notes={report.planned_notes} "
        f"planned_items={report.planned_items} planned_clients={report.planned_clients}"
    )
    print(
        f"[{mode_label}] inserted_notes={report.inserted_notes} "
        f"inserted_items={report.inserted_items} inserted_clients={report.inserted_clients}"
    )
    print(f"[{mode_label}] skipped_existing_notes={report.skipped_existing_notes}")
    print(f"[{mode_label}] report_dir={args.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
