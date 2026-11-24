"""Antarmuka command line.

Contoh:
    python -m paguyuban_billing invoices
    python -m paguyuban_billing receipts --output hasil/
    python -m paguyuban_billing all --config config.yaml
    python -m paguyuban_billing clean            # -> output/data_looker_ready.csv
    python -m paguyuban_billing clean --push-gsheet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_settings
from .data_loader import DataError


def _default_config() -> str:
    return "config.yaml" if Path("config.yaml").exists() else "config.example.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paguyuban_billing",
        description="Generator surat tagihan & kwitansi iuran warga (PDF).",
    )
    parser.add_argument("command", choices=["invoices", "receipts", "all", "clean"], help="aksi yang dijalankan")
    parser.add_argument("-c", "--config", default=_default_config(), help="path file konfigurasi YAML (default: config.yaml, bila tidak ada config.example.yaml)")
    parser.add_argument("-o", "--output", help="folder output (menimpa nilai di konfigurasi)")
    parser.add_argument("--push-gsheet", action="store_true", help="khusus 'clean': kirim hasil ke Google Sheet (butuh GOOGLE_SHEET_URL)")
    return parser


def _run_clean(settings, push: bool, output_dir: Path) -> None:
    from .cleaning import clean_resident_data, read_google_sheet, write_google_sheet
    from .data_loader import read_sheet

    c = settings.cleaning
    if c.google_sheet_url:
        print("Membaca data dari Google Sheet ...")
        raw = read_google_sheet(c.google_sheet_url, c.source_sheet, c.header_row)
    else:
        print("Membaca data dari file Excel lokal ...")
        raw = read_sheet(settings, c.source_sheet, header=c.header_row)

    clean = clean_resident_data(raw, c.column_map)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "data_looker_ready.csv"
    clean.to_csv(target, index=False)
    print(f"{len(clean)} baris valid -> {target}")

    if push:
        if not c.google_sheet_url:
            raise SystemExit("Set environment variable GOOGLE_SHEET_URL untuk memakai --push-gsheet.")
        write_google_sheet(clean, c.google_sheet_url, c.target_tab)
        print(f"Tab '{c.target_tab}' diperbarui. Hubungkan tab ini ke Looker Studio.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(args.config)
        output = Path(args.output) if args.output else settings.output_dir

        from .generator import generate_invoices, generate_receipts

        if args.command in ("invoices", "all"):
            paths = generate_invoices(settings, output)
            print(f"{len(paths)} surat tagihan dibuat di {output / 'tagihan'}")
        if args.command in ("receipts", "all"):
            paths = generate_receipts(settings, output)
            print(f"{len(paths)} kwitansi dibuat di {output / 'kwitansi'}")
        if args.command == "clean":
            _run_clean(settings, args.push_gsheet, output)
    except (FileNotFoundError, DataError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
