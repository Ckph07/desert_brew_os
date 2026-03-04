#!/usr/bin/env python3
"""Extract Brewers Association 2025 style metrics from official PDF.

Output schema keeps numeric min/max when available and preserves non-numeric
guideline values (for example: "Varies with style", "May vary widely") as raw.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "data" / "2025_BA_Beer_Style_Guidelines.pdf"
LAYOUT_TXT_PATH = Path("/tmp/ba_2025_layout.txt")
OUT_PATH = ROOT / "data" / "ba_beer_styles_2025.json"

# Fixed split point for two-column pages after pdftotext -layout.
COLUMN_CUT = 56


@dataclass
class HeadingMatch:
    page_index: int
    line_index: int
    matched_heading: str
    score: float


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.upper()
    value = re.sub(r"[^A-Z0-9]+", " ", value).strip()
    return value


def run_pdftotext() -> None:
    cmd = [
        "pdftotext",
        "-layout",
        str(PDF_PATH),
        str(LAYOUT_TXT_PATH),
    ]
    subprocess.run(cmd, check=True)


def parse_toc_styles(layout_text: str) -> list[tuple[str, int]]:
    start = layout_text.find("Table of Contents")
    end = layout_text.find("ALE STYLES", start)
    if start == -1 or end == -1:
        raise RuntimeError("Could not find Table of Contents/ALE STYLES markers.")

    segment = layout_text[start:end]
    styles: list[tuple[str, int]] = []
    for raw in segment.splitlines():
        match = re.match(
            r"^(\s{3,})([A-Za-z0-9].*?)\s+\.{3,}\s+(\d+)\s*$",
            raw.rstrip(),
        )
        if not match:
            continue
        name = match.group(2).strip()
        page = int(match.group(3))
        if name.endswith("Styles"):
            continue
        styles.append((name, page))

    if not styles:
        raise RuntimeError("No styles found in TOC parse.")
    return styles


def reconstruct_pages(layout_text: str) -> list[list[str]]:
    pages: list[list[str]] = []
    for page in layout_text.split("\f"):
        lines = page.splitlines()
        left: list[str] = []
        right: list[str] = []
        for line in lines:
            if len(line) <= COLUMN_CUT:
                left.append(line.rstrip())
                right.append("")
            else:
                left.append(line[:COLUMN_CUT].rstrip())
                right.append(line[COLUMN_CUT:].rstrip())
        pages.append(left + [""] + right)
    return pages


def infer_toc_offset(pages: list[list[str]]) -> int:
    # In BA 2025 PDF, style page 1 maps to a later PDF page because intro exists.
    first_style_page = None
    for page_index, lines in enumerate(pages):
        if any(line.strip() == "Ordinary Bitter" for line in lines):
            first_style_page = page_index
            break
    if first_style_page is None:
        raise RuntimeError("Could not infer offset from 'Ordinary Bitter'.")
    return first_style_page - 1


def find_heading_in_page(lines: list[str], style_name: str) -> Optional[tuple[int, str, float]]:
    target = normalize(style_name)

    # 1-line exact heading
    for i, line in enumerate(lines):
        if normalize(line) == target:
            return i, line.strip(), 100.0

    # 2-3 lines wrapped exact heading
    for i in range(len(lines)):
        for size in (2, 3):
            if i + size > len(lines):
                continue
            combined = " ".join(part.strip() for part in lines[i : i + size] if part.strip())
            if combined and normalize(combined) == target:
                return i, combined, 95.0

    # Relaxed fallback on first token groups
    tokens = target.split()
    for prefix_size in (5, 4, 3, 2):
        if len(tokens) < prefix_size:
            continue
        key = " ".join(tokens[:prefix_size])
        for i, line in enumerate(lines):
            normalized_line = normalize(line)
            if key in normalized_line:
                # Penalize short/loose fallback.
                return i, line.strip(), 65.0 + prefix_size

    return None


def pick_heading_match(
    pages: list[list[str]],
    toc_page: int,
    style_name: str,
    offset: int,
) -> HeadingMatch:
    expected_pdf_page = toc_page + offset
    best: Optional[HeadingMatch] = None

    for page_index in range(max(0, expected_pdf_page - 1), min(len(pages), expected_pdf_page + 2)):
        found = find_heading_in_page(pages[page_index], style_name)
        if not found:
            continue
        line_index, heading, score = found
        distance = abs(page_index - expected_pdf_page)
        adjusted_score = score - distance * 8
        candidate = HeadingMatch(
            page_index=page_index,
            line_index=line_index,
            matched_heading=heading,
            score=adjusted_score,
        )
        if best is None or candidate.score > best.score:
            best = candidate

    if best is None:
        # This should not happen with current PDF, but keep a safe fallback.
        best = HeadingMatch(
            page_index=max(0, min(len(pages) - 1, expected_pdf_page)),
            line_index=0,
            matched_heading="",
            score=0.0,
        )

    return best


def parse_numeric_token(token: str) -> tuple[Optional[float], bool]:
    value = token.strip()
    plus = value.endswith("+")
    base = value[:-1] if plus else value
    try:
        return float(base), plus
    except ValueError:
        return None, plus


def parse_range(raw: str) -> dict[str, object]:
    text = raw.strip()
    numeric_text = text.replace("%", "")
    # Numeric range or plus-range.
    match = re.search(r"([0-9.]+\+?)\s*-\s*([0-9.]+\+?)", numeric_text)
    if match:
        min_val, _ = parse_numeric_token(match.group(1))
        max_val, _ = parse_numeric_token(match.group(2))
        raw_clean = f"{match.group(1)}-{match.group(2)}"
        return {"min": min_val, "max": max_val, "raw": raw_clean, "mode": "numeric"}

    # Single plus value (for example 40+).
    match = re.search(r"\b([0-9.]+\+)\b", numeric_text)
    if match:
        min_val, _ = parse_numeric_token(match.group(1))
        return {"min": min_val, "max": None, "raw": match.group(1), "mode": "numeric_plus"}

    lowered = text.lower()
    if "varies" in lowered:
        if "varies with porter style" in lowered:
            raw_clean = "Varies with porter style"
        elif "varies with style" in lowered:
            raw_clean = "Varies with style"
        elif "may vary widely" in lowered:
            raw_clean = "May vary widely"
        elif "varies widely" in lowered:
            raw_clean = "Varies widely"
        else:
            raw_clean = "Varies"
        return {"min": None, "max": None, "raw": raw_clean, "mode": "varies"}
    if "may vary" in lowered:
        return {"min": None, "max": None, "raw": "May vary widely", "mode": "varies"}

    return {"min": None, "max": None, "raw": text, "mode": "unknown"}


def extract_style_metrics(
    pages: list[list[str]],
    page_index: int,
    heading_index: int,
) -> dict[str, dict[str, object]]:
    # Prefer the first OG line *after* style heading, allowing page spillover.
    forward_lines: list[str] = []
    forward_lines.extend(pages[page_index][heading_index:])
    if page_index + 1 < len(pages):
        forward_lines.extend(pages[page_index + 1])
    if page_index + 2 < len(pages):
        forward_lines.extend(pages[page_index + 2])
    forward_lines = forward_lines[:280]

    og_forward = next(
        (idx for idx, line in enumerate(forward_lines) if "Original Gravity (°Plato)" in line),
        None,
    )

    blob = None
    if og_forward is not None:
        metric_window = forward_lines[og_forward : min(len(forward_lines), og_forward + 8)]
        blob = re.sub(r"\s+", " ", " ".join(metric_window)).strip()
    else:
        # Fallback to recent OG before heading on same page.
        backward_start = max(0, heading_index - 100)
        backward_window = pages[page_index][backward_start : heading_index + 20]
        og_backward = [
            idx
            for idx, line in enumerate(backward_window)
            if "Original Gravity (°Plato)" in line
        ]
        if og_backward:
            last = og_backward[-1]
            metric_window = backward_window[last : min(len(backward_window), last + 8)]
            blob = re.sub(r"\s+", " ", " ".join(metric_window)).strip()

    if not blob:
        return {
            "og": {"min": None, "max": None, "raw": None, "mode": "missing"},
            "fg": {"min": None, "max": None, "raw": None, "mode": "missing"},
            "abv": {"min": None, "max": None, "raw": None, "mode": "missing"},
            "ibu": {"min": None, "max": None, "raw": None, "mode": "missing"},
            "srm": {"min": None, "max": None, "raw": None, "mode": "missing"},
        }

    def capture(pattern: str) -> Optional[str]:
        match = re.search(pattern, blob)
        return match.group(1).strip() if match else None

    og_raw = capture(r"Original Gravity \(°Plato\)\s*([^•]+)")
    fg_raw = capture(r"Apparent Extract/Final Gravity \(°Plato\)\s*([^•]+)")
    ibu_raw = capture(r"Hop Bitterness \(IBU\)\s*([^•]+)")
    srm_raw = capture(r"Color SRM \(EBC\)\s*([^•]+)")

    # For ABV, prefer value inside parenthesis after "Alcohol by Weight (Volume)".
    abv_raw = None
    abv_match = re.search(
        r"Alcohol by Weight \(Volume\)\s*[0-9.]+%?\s*-?\s*[0-9.]+%?\s*\(([^)]+)\)",
        blob,
    )
    if abv_match:
        abv_raw = abv_match.group(1).strip()
    else:
        abv_raw = capture(r"Alcohol by Weight \(Volume\)\s*([^•]+)")

    return {
        "og": parse_range(og_raw) if og_raw else {"min": None, "max": None, "raw": None, "mode": "missing"},
        "fg": parse_range(fg_raw) if fg_raw else {"min": None, "max": None, "raw": None, "mode": "missing"},
        "abv": parse_range(abv_raw) if abv_raw else {"min": None, "max": None, "raw": None, "mode": "missing"},
        "ibu": parse_range(ibu_raw) if ibu_raw else {"min": None, "max": None, "raw": None, "mode": "missing"},
        "srm": parse_range(srm_raw) if srm_raw else {"min": None, "max": None, "raw": None, "mode": "missing"},
    }


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"PDF not found: {PDF_PATH}")

    run_pdftotext()
    layout_text = LAYOUT_TXT_PATH.read_text(errors="ignore")

    styles_toc = parse_toc_styles(layout_text)
    pages = reconstruct_pages(layout_text)
    offset = infer_toc_offset(pages)

    extracted_styles: list[dict[str, object]] = []
    for index, (name, toc_page) in enumerate(styles_toc, start=1):
        heading = pick_heading_match(pages, toc_page, name, offset)
        metrics = extract_style_metrics(pages, heading.page_index, heading.line_index)

        extracted_styles.append(
            {
                "id": f"BA-2025-{index:03d}",
                "name": name,
                "toc_page": toc_page,
                "og_min": metrics["og"]["min"],
                "og_max": metrics["og"]["max"],
                "fg_min": metrics["fg"]["min"],
                "fg_max": metrics["fg"]["max"],
                "abv_min": metrics["abv"]["min"],
                "abv_max": metrics["abv"]["max"],
                "ibu_min": metrics["ibu"]["min"],
                "ibu_max": metrics["ibu"]["max"],
                "srm_min": metrics["srm"]["min"],
                "srm_max": metrics["srm"]["max"],
                "raw": {
                    "og": metrics["og"]["raw"],
                    "fg": metrics["fg"]["raw"],
                    "abv": metrics["abv"]["raw"],
                    "ibu": metrics["ibu"]["raw"],
                    "srm": metrics["srm"]["raw"],
                },
                "modes": {
                    "og": metrics["og"]["mode"],
                    "fg": metrics["fg"]["mode"],
                    "abv": metrics["abv"]["mode"],
                    "ibu": metrics["ibu"]["mode"],
                    "srm": metrics["srm"]["mode"],
                },
                "extraction": {
                    "matched_pdf_page_index": heading.page_index,
                    "matched_heading": heading.matched_heading,
                    "match_score": round(heading.score, 2),
                },
            }
        )

    numeric_og = sum(1 for row in extracted_styles if row["og_min"] is not None)
    varies_og = sum(1 for row in extracted_styles if row["modes"]["og"] == "varies")

    payload = {
        "metadata": {
            "source": "Brewers Association Beer Style Guidelines",
            "year": 2025,
            "version": "Updated 5/30/2025",
            "source_pdf": str(PDF_PATH.relative_to(ROOT)),
            "extracted_from": "pdftotext -layout",
            "parser": "extract_ba_styles_2025.py",
            "total_styles": len(extracted_styles),
            "numeric_og_styles": numeric_og,
            "varies_og_styles": varies_og,
            "notes": "Styles with non-numeric ranges keep raw text and null min/max.",
        },
        "styles": extracted_styles,
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT_PATH}")
    print(f"Styles: {len(extracted_styles)} | numeric OG: {numeric_og} | varies OG: {varies_og}")


if __name__ == "__main__":
    main()
