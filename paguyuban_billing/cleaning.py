"""Tahap cleaning data warga agar siap dipakai dashboard (mis. Looker Studio).

Fungsi inti `clean_resident_data` murni (tanpa I/O) sehingga mudah diuji.
Integrasi Google Sheets bersifat opsional dan hanya dimuat saat dipakai.
"""

from __future__ import annotations

import urllib.parse
from typing import Dict

import pandas as pd

from .formatting import parse_rupiah


def clean_resident_data(df_raw: pd.DataFrame, column_map: Dict[str, str], key_column: str = "KAVLING") -> pd.DataFrame:
    """Pilih & ganti nama kolom, buang baris kosong, dan standarkan kolom TARIF.

    Args:
        df_raw: data mentah (header sudah benar).
        column_map: {NAMA_BERSIH: "nama kolom sumber"}.
        key_column: kolom (nama bersih) yang wajib terisi; baris tanpa nilai dibuang.
    """
    missing = [src for src in column_map.values() if src not in df_raw.columns]
    if missing:
        raise ValueError(f"Kolom sumber tidak ditemukan: {missing}. Kolom yang ada: {list(df_raw.columns)}")

    df = df_raw[list(column_map.values())].copy()
    df.columns = list(column_map.keys())

    if key_column in df.columns:
        df = df[df[key_column].notna()]
    df = df.reset_index(drop=True)

    if "TARIF" in df.columns:
        df["TARIF"] = df["TARIF"].map(parse_rupiah).astype(int)

    # Kolom numerik yang seluruhnya bilangan bulat (mis. 1.0 akibat sel kosong) -> int.
    for col in df.select_dtypes(include="number").columns:
        if (df[col].dropna() % 1 == 0).all() and not df[col].isna().any():
            df[col] = df[col].astype(int)
    return df


def google_sheet_id(sheet_url: str) -> str:
    return sheet_url.split("/d/")[1].split("/")[0]


def read_google_sheet(sheet_url: str, tab_name: str, header_row: int = 0) -> pd.DataFrame:
    """Baca satu tab Google Sheet (akses 'siapa saja dengan link') lewat ekspor CSV."""
    url = (
        f"https://docs.google.com/spreadsheets/d/{google_sheet_id(sheet_url)}"
        f"/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(tab_name)}"
    )
    return pd.read_csv(url, header=header_row)


def write_google_sheet(df: pd.DataFrame, sheet_url: str, tab_name: str, credentials_file: str | None = None) -> None:
    """Tulis DataFrame ke tab Google Sheet (dibuat bila belum ada). Butuh `requirements-gsheets.txt`.

    Autentikasi memakai service account: berikan path file JSON lewat argumen
    atau environment variable GOOGLE_APPLICATION_CREDENTIALS. File JSON itu
    tidak boleh pernah di-commit.
    """
    try:
        import gspread
        from gspread_dataframe import set_with_dataframe
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Instal dulu: pip install -r requirements-gsheets.txt") from exc

    client = gspread.service_account(filename=credentials_file) if credentials_file else gspread.service_account()
    spreadsheet = client.open_by_url(sheet_url)
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=max(len(df) + 50, 1000), cols=max(len(df.columns) + 5, 20))
    set_with_dataframe(worksheet, df, include_index=False, include_column_header=True)
