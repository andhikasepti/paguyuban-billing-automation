import pandas as pd
import pytest

from paguyuban_billing.cleaning import clean_resident_data

MAP = {"NO": "NO", "KAVLING": "KAVLING", "NAMA_WARGA": "NAMA WARGA", "TARIF": "TARIF"}


def _raw():
    return pd.DataFrame(
        {
            "NO": [1, 2, 3],
            "KAVLING": [1, 2, None],           # baris ke-3 kosong -> dibuang
            "NAMA WARGA": ["A", "B", None],
            "TARIF": ["Rp 300.000", 400000.0, None],
            "KOLOM LAIN": ["x", "y", "z"],     # tidak masuk column_map -> dibuang
        }
    )


def test_cleaning_membuang_baris_kosong_dan_kolom_lain():
    df = clean_resident_data(_raw(), MAP)
    assert list(df.columns) == ["NO", "KAVLING", "NAMA_WARGA", "TARIF"]
    assert len(df) == 2


def test_cleaning_tarif_menjadi_integer():
    df = clean_resident_data(_raw(), MAP)
    assert df["TARIF"].tolist() == [300000, 400000]


def test_cleaning_angka_bulat_bukan_float():
    df = clean_resident_data(_raw(), MAP)
    assert df["KAVLING"].tolist() == [1, 2]
    assert str(df["KAVLING"].dtype).startswith("int")


def test_cleaning_kolom_sumber_hilang_memberi_error_jelas():
    with pytest.raises(ValueError, match="Kolom sumber tidak ditemukan"):
        clean_resident_data(_raw(), {"X": "TIDAK ADA"})
