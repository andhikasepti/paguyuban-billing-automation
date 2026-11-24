import pytest

from paguyuban_billing.terbilang import terbilang, terbilang_rupiah


@pytest.mark.parametrize(
    "angka, teks",
    [
        (0, "nol"),
        (11, "sebelas"),
        (15, "lima belas"),
        (100, "seratus"),
        (101, "seratus satu"),
        (250, "dua ratus lima puluh"),
        (1000, "seribu"),
        (1500, "seribu lima ratus"),
        (2025, "dua ribu dua puluh lima"),
        (300_000, "tiga ratus ribu"),
        (1_250_000, "satu juta dua ratus lima puluh ribu"),
        (2_000_000_000, "dua miliar"),
    ],
)
def test_terbilang(angka, teks):
    assert terbilang(angka) == teks


def test_terbilang_rupiah_title_case():
    assert terbilang_rupiah(600_000) == "Enam Ratus Ribu Rupiah"
    assert terbilang_rupiah(1_000_000) == "Satu Juta Rupiah"
    assert terbilang_rupiah(0) == "Nol Rupiah"
