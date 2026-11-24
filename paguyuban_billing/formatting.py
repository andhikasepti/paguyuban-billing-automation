"""Helper format: rupiah, tanggal Indonesia, nama file aman, escape XML."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any
from xml.sax.saxutils import escape

import pandas as pd

BULAN = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def format_rupiah(nilai: float) -> str:
    """600000 -> 'Rp 600.000,-'"""
    return f"Rp {nilai:,.0f}".replace(",", ".") + ",-"


def format_tanggal(nilai: Any, fallback: str = "") -> str:
    """Ubah nilai sel Excel (datetime/teks) menjadi '16 November 2026'.

    Sel tanggal di Excel dibaca pandas sebagai Timestamp; jika langsung di-str()
    hasilnya '2026-11-16 00:00:00', maka perlu diformat ulang.
    """
    if nilai is None or (not isinstance(nilai, str) and pd.isna(nilai)):
        return fallback
    if isinstance(nilai, (dt.datetime, dt.date, pd.Timestamp)):
        return f"{nilai.day:02d} {BULAN[nilai.month]} {nilai.year}"
    teks = str(nilai).strip()
    return teks or fallback


def tanggal_hari_ini() -> str:
    return format_tanggal(dt.date.today())


def parse_rupiah(nilai: Any) -> int:
    """Ubah 'Rp 1.250.000,00', 300000.0, atau '300000' menjadi integer.

    Angka numerik dipakai apa adanya. Pembersihan berbasis regex `[^\\d]` pada
    300000.0 akan menghasilkan 3000000 (titik desimal terhapus) sehingga
    nilai numerik sengaja ditangani terpisah.
    """
    if nilai is None or (not isinstance(nilai, str) and pd.isna(nilai)):
        return 0
    if isinstance(nilai, (int, float)):
        return int(round(nilai))
    teks = re.sub(r"(?i)rp", "", str(nilai)).replace(" ", "").strip()
    teks = re.sub(r",\d{1,2}$", "", teks)  # buang desimal gaya Indonesia (,00)
    digit = re.sub(r"[^\d]", "", teks)
    return int(digit) if digit else 0


def aman_untuk_nama_file(teks: str) -> str:
    """Hapus karakter yang tidak aman untuk nama file."""
    teks = re.sub(r"[\\/:*?\"<>|]+", "-", str(teks)).strip()
    return re.sub(r"\s+", "_", teks)


def esc(teks: Any) -> str:
    """Escape karakter XML (&, <, >) agar aman dipakai di Paragraph ReportLab."""
    return escape(str(teks))
