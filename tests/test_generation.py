"""Smoke test end-to-end memakai data dummy di repo."""

from pathlib import Path

import pytest

from paguyuban_billing.config import load_settings
from paguyuban_billing.data_loader import DataError, load_invoices, load_receipts
from paguyuban_billing.generator import generate_invoices, generate_receipts

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def settings():
    return load_settings(ROOT / "config.example.yaml")


def test_load_invoices_menghitung_total(settings):
    invoices = load_invoices(settings)
    assert len(invoices) == 8
    assert all(i.total == i.iuran_per_bulan * i.jumlah_bulan for i in invoices)
    assert any(i.jumlah_bulan > 1 and i.catatan for i in invoices)


def test_load_receipts_terbilang_otomatis(settings):
    receipts = load_receipts(settings)
    assert len(receipts) == 12
    assert all(r.terbilang.endswith("Rupiah") for r in receipts)
    assert all(r.tanggal.endswith("November 2026") for r in receipts)


def test_generate_pdf(settings, tmp_path):
    inv = generate_invoices(settings, tmp_path)
    rec = generate_receipts(settings, tmp_path)
    assert len(inv) == 8 and len(rec) == 12
    for path in inv + rec:
        assert path.read_bytes().startswith(b"%PDF")
        assert path.stat().st_size > 2000


def test_sheet_salah_memberi_error_jelas(settings):
    settings.data.invoice_sheet = "Sheet Tidak Ada"
    try:
        with pytest.raises(DataError):
            load_invoices(settings)
    finally:
        settings.data.invoice_sheet = "Data Tagihan"


def test_karakter_khusus_pada_nama_tidak_merusak_pdf(settings, tmp_path):
    from paguyuban_billing.invoice import InvoiceData, build_invoice
    from paguyuban_billing.receipt import ReceiptData, build_receipt

    nama = "BUDI & SARI <RT 1>"
    inv = build_invoice(
        InvoiceData("0001/TP/2026", nama, "X-01", "Alamat & Blok <X-01>", "November 2026", 300000,
                    catatan="Catatan dengan & dan <tag>"),
        settings, tmp_path / "i.pdf",
    )
    rec = build_receipt(
        ReceiptData("K-1", "01 November 2026", nama, "Alamat & Blok", 300000, "Tiga Ratus Ribu Rupiah",
                    "Iuran", "November 2026", "Titipan & lainnya"),
        settings, tmp_path / "r.pdf",
    )
    assert inv.read_bytes().startswith(b"%PDF") and rec.read_bytes().startswith(b"%PDF")


def test_nama_file_duplikat_tidak_saling_menimpa():
    from paguyuban_billing.generator import _unique_path

    used: set = set()
    a = _unique_path(Path("."), "Tagihan_A-01.pdf", used)
    b = _unique_path(Path("."), "Tagihan_A-01.pdf", used)
    assert a != b
