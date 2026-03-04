"""
Unit tests for historical sales notes importer parser/dedupe behavior.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCRIPT_PATH = ROOT / "scripts" / "import_sales_notes_historic.py"

spec = importlib.util.spec_from_file_location("import_sales_notes_historic", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load importer script at {SCRIPT_PATH}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TestHistoricalImporterParser:
    def test_parse_ocr_txt_normal_0(self):
        note, issues = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/0.txt")
        assert note is not None
        assert note.note_number_int == 158
        assert note.note_number == "00000158"
        assert note.client_name == "ASADOR 9"
        assert math.isclose(note.total, 732.0, rel_tol=0, abs_tol=0.01)
        assert len(note.items) >= 1
        assert not [issue for issue in issues if issue.severity in {"skip", "error"}]

    def test_parse_ocr_txt_normal_114(self):
        note, issues = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/114.txt")
        assert note is not None
        assert note.note_number_int == 273
        assert note.note_number == "00000273"
        assert note.client_name == "DESERT BREW TAP"
        assert math.isclose(note.total, 22560.0, rel_tol=0, abs_tol=0.01)
        assert len(note.items) >= 1
        assert not [issue for issue in issues if issue.severity in {"skip", "error"}]

    def test_parse_ocr_txt_noisy_102_103_are_skipped(self):
        note_102, issues_102 = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/102.txt")
        note_103, issues_103 = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/103.txt")

        assert note_102 is None
        assert note_103 is None
        assert any(issue.severity == "skip" for issue in issues_102)
        assert any(issue.severity == "skip" for issue in issues_103)

    def test_parse_noise_files_13_88_are_skipped(self):
        note_13, issues_13 = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/13.txt")
        note_88, issues_88 = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/88.txt")

        assert note_13 is None
        assert note_88 is None
        assert any(issue.reason in {"missing_note_number", "missing_total"} for issue in issues_13)
        assert any(issue.reason in {"missing_note_number", "missing_total"} for issue in issues_88)

    def test_parse_gestion_pdf_taxed_and_bonus(self):
        pdftotext_bin = module.find_pdftotext()
        note_157, issues_157 = module.parse_gestion_pdf(
            ROOT / "docs/Notas de venta/notas_gestion_Cervecera/Pedido-00000157.pdf",
            pdftotext_bin=pdftotext_bin,
        )
        note_101, issues_101 = module.parse_gestion_pdf(
            ROOT / "docs/Notas de venta/notas_gestion_Cervecera/Pedido_00000101.pdf",
            pdftotext_bin=pdftotext_bin,
        )

        assert note_157 is not None
        assert note_157.note_number_int == 157
        assert note_157.include_taxes is True
        assert math.isclose(note_157.iva_total, 243.20, rel_tol=0, abs_tol=0.01)
        assert math.isclose(note_157.total, 1763.20, rel_tol=0, abs_tol=0.01)
        assert not [issue for issue in issues_157 if issue.severity in {"skip", "error"}]

        assert note_101 is not None
        assert note_101.note_number_int == 101
        assert math.isclose(note_101.total, 0.0, rel_tol=0, abs_tol=0.01)
        assert not [issue for issue in issues_101 if issue.severity in {"skip", "error"}]

    def test_dedupe_conflict_163_keeps_dup(self):
        note_a, _ = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/4.txt")
        note_b, _ = module.parse_ocr_txt(ROOT / "docs/Notas de venta/notas/6.txt")
        assert note_a is not None
        assert note_b is not None

        issues: list[module.ImportIssue] = []
        deduped, duplicate_rows, conflict_rows = module.deduplicate_notes([note_a, note_b], issues)

        note_numbers = sorted(note.note_number for note in deduped)
        assert "00000163" in note_numbers
        assert "00000163-DUP1" in note_numbers
        assert any(row["type"] == "conflict_kept" for row in duplicate_rows)
        assert len(conflict_rows) == 1

    def test_dedupe_identical_33_collapses(self):
        pdftotext_bin = module.find_pdftotext()
        note_a, _ = module.parse_gestion_pdf(
            ROOT / "docs/Notas de venta/notas_gestion_Cervecera/Pedido_00000033.pdf",
            pdftotext_bin=pdftotext_bin,
        )
        note_b, _ = module.parse_gestion_pdf(
            ROOT / "docs/Notas de venta/notas_gestion_Cervecera/Pedido-00000033.pdf",
            pdftotext_bin=pdftotext_bin,
        )
        assert note_a is not None
        assert note_b is not None

        issues: list[module.ImportIssue] = []
        deduped, duplicate_rows, conflict_rows = module.deduplicate_notes([note_a, note_b], issues)

        assert len(deduped) == 1
        assert deduped[0].note_number == "00000033"
        assert any(row["type"] == "identical_collapsed" for row in duplicate_rows)
        assert conflict_rows == []

    def test_client_alias_for_db_tap(self):
        assert module.canonicalize_client_name("DB TAP") == "DESERT BREW TAP"
        assert (
            module.canonicalize_client_name(
                "Desert Brew Tap - Desert Brew Tap                     DIRECCION: Guadalupe Victoria 120"
            )
            == "DESERT BREW TAP"
        )
