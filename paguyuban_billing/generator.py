"""Proses batch: baca data, buat semua PDF, laporkan hasilnya."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .data_loader import load_invoices, load_receipts
from .formatting import aman_untuk_nama_file
from .invoice import build_invoice
from .receipt import build_receipt


def _unique_path(folder: Path, name: str, used: set) -> Path:
    """Hindari timpa-menimpa bila dua baris menghasilkan nama file yang sama."""
    stem, suffix = Path(name).stem, Path(name).suffix
    candidate, counter = name, 2
    while candidate in used:
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1
    used.add(candidate)
    return folder / candidate


def generate_invoices(settings, output_dir: Path | None = None) -> List[Path]:
    folder = Path(output_dir or settings.output_dir) / "tagihan"
    folder.mkdir(parents=True, exist_ok=True)
    used: set = set()
    paths = []
    for inv in load_invoices(settings):
        name = f"Tagihan_{aman_untuk_nama_file(inv.blok)}_{aman_untuk_nama_file(inv.periode)}.pdf"
        paths.append(build_invoice(inv, settings, _unique_path(folder, name, used)))
    return paths


def generate_receipts(settings, output_dir: Path | None = None) -> List[Path]:
    folder = Path(output_dir or settings.output_dir) / "kwitansi"
    folder.mkdir(parents=True, exist_ok=True)
    used: set = set()
    paths = []
    for rec in load_receipts(settings):
        name = f"Kwitansi_{aman_untuk_nama_file(rec.blok or rec.no_kwitansi)}_{aman_untuk_nama_file(rec.periode)}.pdf"
        paths.append(build_receipt(rec, settings, _unique_path(folder, name, used)))
    return paths
