"""Konversi angka ke teks bahasa Indonesia ("terbilang") untuk kwitansi."""

from __future__ import annotations

_SATUAN = [
    "", "satu", "dua", "tiga", "empat", "lima",
    "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas",
]

# (batas atas, pembagi, satuan)
_SKALA = [
    (10**6, 10**3, "ribu"),
    (10**9, 10**6, "juta"),
    (10**12, 10**9, "miliar"),
    (10**15, 10**12, "triliun"),
]


def _tulis(n: int) -> str:
    if n < 12:
        return _SATUAN[n]
    if n < 20:
        return f"{_tulis(n - 10)} belas"
    if n < 100:
        sisa = n % 10
        return f"{_tulis(n // 10)} puluh" + (f" {_tulis(sisa)}" if sisa else "")
    if n < 200:
        return "seratus" + (f" {_tulis(n - 100)}" if n > 100 else "")
    if n < 1000:
        sisa = n % 100
        return f"{_tulis(n // 100)} ratus" + (f" {_tulis(sisa)}" if sisa else "")
    if n < 2000:
        return "seribu" + (f" {_tulis(n - 1000)}" if n > 1000 else "")
    for batas, pembagi, satuan in _SKALA:
        if n < batas:
            sisa = n % pembagi
            return f"{_tulis(n // pembagi)} {satuan}" + (f" {_tulis(sisa)}" if sisa else "")
    raise ValueError("Angka terlalu besar untuk dikonversi")


def terbilang(n: int) -> str:
    """Contoh: 600000 -> 'enam ratus ribu'."""
    if n < 0:
        return f"minus {terbilang(-n)}"
    return "nol" if n == 0 else _tulis(n)


def terbilang_rupiah(n: float) -> str:
    """Contoh: 600000 -> 'Enam Ratus Ribu Rupiah' (Title Case, sesuai format kwitansi)."""
    teks = f"{terbilang(int(round(n)))} rupiah"
    return " ".join(kata.capitalize() for kata in teks.split())
