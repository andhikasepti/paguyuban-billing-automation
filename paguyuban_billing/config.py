"""Pemuatan konfigurasi dari file YAML.

Semua nilai yang spesifik terhadap satu paguyuban (nama, rekening, ketua,
path data, dsb.) berada di file konfigurasi, bukan di dalam kode.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class Organization:
    name: str
    address: str
    whatsapp: str
    city: str
    chairman_name: str
    chairman_title: str = "Ketua Paguyuban"
    address_prefix: str = "Blok"
    short_name: str = "Paguyuban"


@dataclass
class Bank:
    name: str
    account_number: str
    account_holder: str


@dataclass
class Billing:
    period: str = ""
    invoice_date: str = ""
    due_day: int = 17
    default_payment_type: str = "Iuran"


@dataclass
class Assets:
    logo: Path = Path("assets/logo_placeholder.png")
    signature: Path = Path("assets/signature_placeholder.png")


@dataclass
class DataSource:
    excel_path: Path = Path("data/sample_data.xlsx")
    excel_url: str = ""
    invoice_sheet: str = "Data Tagihan"
    receipt_sheet: str = "Uang Masuk"


@dataclass
class Cleaning:
    source_sheet: str = "Data Input"
    header_row: int = 0
    column_map: Dict[str, str] = field(default_factory=dict)
    target_tab: str = "Data_Looker_Ready"
    google_sheet_url: str = ""


@dataclass
class Settings:
    organization: Organization
    bank: Bank
    billing: Billing
    assets: Assets
    data: DataSource
    cleaning: Cleaning
    output_dir: Path
    base_dir: Path


def _build(cls, values: Dict[str, Any] | None):
    """Bangun dataclass dari dict; kunci yang tidak dikenal memicu error jelas."""
    values = values or {}
    allowed = {f.name for f in fields(cls)}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(
            f"Kunci tidak dikenal pada bagian '{cls.__name__}': {sorted(unknown)}. "
            f"Kunci yang valid: {sorted(allowed)}"
        )
    return cls(**values)


def _resolve(base: Path, value: Path | str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path)


def load_settings(config_path: str | Path) -> Settings:
    """Muat konfigurasi YAML dan selesaikan path relatif terhadap lokasi file."""
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"File konfigurasi tidak ditemukan: {config_path}")

    base = config_path.parent
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    settings = Settings(
        organization=_build(Organization, raw.get("organization")),
        bank=_build(Bank, raw.get("bank")),
        billing=_build(Billing, raw.get("billing")),
        assets=_build(Assets, raw.get("assets")),
        data=_build(DataSource, raw.get("data")),
        cleaning=_build(Cleaning, raw.get("cleaning")),
        output_dir=_resolve(base, (raw.get("output") or {}).get("directory", "output")),
        base_dir=base,
    )

    # YAML 1.1 membaca NO/YES (tanpa kutip) sebagai boolean; kembalikan ke teks.
    settings.cleaning.column_map = {
        {False: "NO", True: "YES"}.get(k, k) if isinstance(k, bool) else k: v
        for k, v in settings.cleaning.column_map.items()
    }

    settings.assets.logo = _resolve(base, settings.assets.logo)
    settings.assets.signature = _resolve(base, settings.assets.signature)
    settings.data.excel_path = _resolve(base, settings.data.excel_path)

    # Nilai sensitif dibaca dari environment variable agar tidak masuk repo.
    settings.data.excel_url = os.getenv("DATA_URL", settings.data.excel_url)
    settings.cleaning.google_sheet_url = os.getenv(
        "GOOGLE_SHEET_URL", settings.cleaning.google_sheet_url
    )
    return settings
