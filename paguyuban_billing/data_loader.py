"""Membaca data Excel dan mengubahnya menjadi objek InvoiceData / ReceiptData."""

from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from .formatting import format_tanggal, parse_rupiah, tanggal_hari_ini
from .invoice import InvoiceData
from .receipt import ReceiptData
from .terbilang import terbilang_rupiah

INVOICE_REQUIRED = ["No Tagihan", "Blok", "Nama Pemilik", "Jangka Pembayaran"]
RECEIPT_REQUIRED = ["No Pembayaran", "Blok", "Nama Pemilik", "Nominal"]
INVOICE_NOTE_COLUMNS = ["Catatan", "Keterangan", "Detail", "Catatan Tambahan", "Deskripsi Tagihan"]


class DataError(ValueError):
    """Data sumber tidak sesuai format yang diharapkan."""


def direct_download_url(url: str) -> str:
    """Pastikan link Dropbox berupa direct download (dl=1)."""
    if "dropbox.com" not in url:
        return url
    if "dl=0" in url:
        return url.replace("dl=0", "dl=1")
    if "dl=1" not in url:
        return url + ("&dl=1" if "?" in url else "?dl=1")
    return url


def read_sheet(settings, sheet_name: str, header: int = 0) -> pd.DataFrame:
    """Baca satu sheet dari file lokal, atau dari DATA_URL bila diisi."""
    source = direct_download_url(settings.data.excel_url) if settings.data.excel_url else settings.data.excel_path
    if not settings.data.excel_url and not settings.data.excel_path.exists():
        raise FileNotFoundError(f"File data tidak ditemukan: {settings.data.excel_path}")
    try:
        return pd.read_excel(source, sheet_name=sheet_name, header=header)
    except ValueError as exc:  # sheet tidak ada
        raise DataError(f"Sheet '{sheet_name}' tidak ditemukan atau tidak bisa dibaca: {exc}") from exc


def _check_columns(df: pd.DataFrame, required: Iterable[str], sheet: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataError(
            f"Sheet '{sheet}' tidak punya kolom wajib: {missing}. Kolom yang ada: {list(df.columns)}"
        )


def _text(row: pd.Series, column: str, default: str = "") -> str:
    if column not in row.index or pd.isna(row[column]):
        return default
    return str(row[column]).strip()


def _number(row: pd.Series, column: str) -> float | None:
    if column not in row.index or pd.isna(row[column]):
        return None
    value = row[column]
    return float(parse_rupiah(value)) if isinstance(value, str) else float(value)


def load_invoices(settings) -> List[InvoiceData]:
    sheet = settings.data.invoice_sheet
    df = read_sheet(settings, sheet)
    _check_columns(df, INVOICE_REQUIRED, sheet)
    df = df.dropna(subset=["No Tagihan", "Nama Pemilik"])

    invoices: List[InvoiceData] = []
    for _, row in df.iterrows():
        blok = _text(row, "Blok")
        iuran = _number(row, "Iuran") or 0.0
        jumlah = int(_number(row, "Jumlah Bulan") or 1)
        # Total memakai nilai sel; jika kosong (mis. rumus belum dihitung) hitung ulang.
        total = _number(row, "Total")
        if total is None:
            total = iuran * jumlah
        catatan = next((_text(row, c) for c in INVOICE_NOTE_COLUMNS if _text(row, c)), "")

        invoices.append(
            InvoiceData(
                no_tagihan=_text(row, "No Tagihan"),
                nama=_text(row, "Nama Pemilik"),
                blok=blok,
                alamat=f"{settings.organization.address_prefix} {blok}",
                periode=_text(row, "Jangka Pembayaran", settings.billing.period),
                total=total,
                iuran_per_bulan=iuran,
                jumlah_bulan=jumlah,
                catatan=catatan,
            )
        )
    return invoices


def load_receipts(settings) -> List[ReceiptData]:
    sheet = settings.data.receipt_sheet
    df = read_sheet(settings, sheet)
    _check_columns(df, RECEIPT_REQUIRED, sheet)
    df = df.dropna(subset=["No Pembayaran", "Nominal", "Nama Pemilik"])

    receipts: List[ReceiptData] = []
    for _, row in df.iterrows():
        blok = _text(row, "Blok")
        alamat_dasar = _text(row, "Alamat Pemilik")
        alamat = f"{alamat_dasar} {blok}".strip() if alamat_dasar else f"{settings.organization.address_prefix} {blok}"
        nominal = _number(row, "Nominal") or 0.0

        receipts.append(
            ReceiptData(
                no_kwitansi=_text(row, "No Pembayaran"),
                tanggal=format_tanggal(row.get("Tanggal Pembayaran"), fallback=tanggal_hari_ini()),
                nama=_text(row, "Nama Pemilik"),
                alamat=alamat,
                nominal=nominal,
                # Terbilang dihitung otomatis bila kolomnya kosong.
                terbilang=_text(row, "Terbilang") or terbilang_rupiah(nominal),
                jenis_bayar=_text(row, "Jenis Pembayaran", settings.billing.default_payment_type),
                periode=_text(row, "Jangka Pembayaran", settings.billing.period),
                catatan_khusus=_text(row, "Catatan Khusus"),
                blok=blok,
            )
        )
    return receipts
