import datetime as dt

import pandas as pd
import pytest

from paguyuban_billing.formatting import (
    aman_untuk_nama_file,
    esc,
    format_rupiah,
    format_tanggal,
    parse_rupiah,
)


def test_format_rupiah():
    assert format_rupiah(600_000) == "Rp 600.000,-"
    assert format_rupiah(1_500_000.0) == "Rp 1.500.000,-"


@pytest.mark.parametrize(
    "nilai, hasil",
    [
        (300000, 300000),
        (300000.0, 300000),          # float tidak boleh menjadi 3000000
        ("300000", 300000),
        ("Rp 300.000", 300000),
        ("Rp 1.250.000,00", 1250000),
        ("", 0),
        (None, 0),
        (float("nan"), 0),
    ],
)
def test_parse_rupiah(nilai, hasil):
    assert parse_rupiah(nilai) == hasil


def test_format_tanggal():
    assert format_tanggal(dt.date(2026, 11, 16)) == "16 November 2026"
    assert format_tanggal(pd.Timestamp("2026-01-05")) == "05 Januari 2026"
    assert format_tanggal("17 November 2026") == "17 November 2026"
    assert format_tanggal(None, fallback="-") == "-"
    assert format_tanggal(float("nan"), fallback="-") == "-"


def test_nama_file_aman():
    assert aman_untuk_nama_file("A/01 : Oktober") == "A-01_-_Oktober"


def test_esc_melindungi_xml():
    assert esc("Budi & Sari <RT 1>") == "Budi &amp; Sari &lt;RT 1&gt;"
