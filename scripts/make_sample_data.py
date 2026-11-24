"""Buat data dummy (FIKTIF) dan aset placeholder untuk demo.

Menghasilkan:
    data/sample_data.xlsx               -> 4 sheet: Petunjuk, Data Input, Data Tagihan, Uang Masuk
    assets/logo_placeholder.png         -> logo contoh
    assets/signature_placeholder.png    -> tanda tangan contoh (transparan)

Semua nama, blok, dan nominal dikarang. Tidak ada data warga sungguhan.

Jalankan dari root repo:
    python scripts/make_sample_data.py
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = "Arial"

# (blok, nama, luas m2, jenis properti, tarif)
TIPE = {"36": (36, "Tipe 36", 300_000), "45": (45, "Tipe 45", 400_000), "60": (60, "Tipe 60", 500_000)}
RESIDENTS = [
    ("A-01", "AGUS PRASETYO", "36"), ("A-02", "SITI RAHAYU", "36"), ("A-03", "BUDI HARTONO", "45"),
    ("A-04", "DEWI LESTARI", "45"), ("A-05", "RIZKY RAMADHAN", "60"),
    ("B-01", "AYU WULANDARI", "36"), ("B-02", "HENDRA GUNAWAN", "45"), ("B-03", "NUR AINI", "36"),
    ("B-04", "YOGA PRATAMA", "60"), ("B-05", "MAYA KUSUMA", "45"),
    ("C-01", "FAJAR NUGROHO", "36"), ("C-02", "RINA SUSANTI", "45"), ("C-03", "DIMAS SAPUTRA", "60"),
    ("C-04", "PUTRI ANGGRAINI", "36"), ("C-05", "EKO WAHYUDI", "45"),
    ("D-01", "LINA MARLINA", "36"), ("D-02", "TAUFIK HIDAYAT", "60"), ("D-03", "WAHYU SETIAWAN", "45"),
    ("D-04", "CITRA DEWANTI", "36"), ("D-05", "ANDI FIRMANSYAH", "45"),
]
# 12 warga pertama sudah membayar (kwitansi), 8 sisanya belum (tagihan)
PAID, UNPAID = RESIDENTS[:12], RESIDENTS[12:]
# blok -> jumlah bulan tertunggak (default 1) dan catatan
ARREARS = {"D-02": (3, "Termasuk tunggakan bulan September dan Oktober 2026."), "D-04": (2, "Termasuk tunggakan bulan Oktober 2026.")}
PERIODE_BULAN = {1: "November 2026", 2: "Oktober - November 2026", 3: "September - November 2026"}

# --- gaya sel -----------------------------------------------------------------
HEADER_FILL = PatternFill("solid", start_color="1E293B")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
BODY = Font(name=FONT, size=10)
INPUT = Font(name=FONT, size=10, color="0000FF")  # biru = nilai input
BOLD = Font(name=FONT, size=10, bold=True)
THIN = Side(style="thin", color="CBD5E1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
RUPIAH = '#,##0;(#,##0);"-"'


def style_header(ws, row: int, ncols: int) -> None:
    for col in range(1, ncols + 1):
        c = ws.cell(row=row, column=col)
        c.fill, c.font, c.border = HEADER_FILL, HEADER_FONT, BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def put(ws, cell: str, value, font=BODY) -> None:
    ws[cell] = value
    ws[cell].font = font


def set_widths(ws, widths) -> None:
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_row(ws, row: int, values, fonts=None, formats=None) -> None:
    for i, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = (fonts or {}).get(i, BODY)
        c.border = BORDER
        if formats and i in formats:
            c.number_format = formats[i]


# --- sheet --------------------------------------------------------------------
def sheet_petunjuk(wb: Workbook) -> None:
    ws = wb.active
    ws.title = "Petunjuk"
    put(ws, "A1", "DATA DUMMY - Taman Sejahtera Residence (fiktif)", Font(name=FONT, bold=True, size=13))
    lines = [
        "Berkas ini dibuat oleh scripts/make_sample_data.py. Seluruh nama, blok, dan nominal adalah karangan.",
        "",
        "Legenda: teks biru = nilai input yang diisi manual; teks hitam = rumus/hasil hitung.",
        "",
        "Sheet 'Data Input'  : data induk warga. Header ada di baris ke-11 (ada judul di atasnya) -> contoh tahap cleaning.",
        "Sheet 'Data Tagihan': satu baris per surat tagihan. Kolom Total = Iuran x Jumlah Bulan (rumus).",
        "Sheet 'Uang Masuk November 2026': satu baris per kwitansi. Kolom Terbilang boleh dikosongkan, akan dihitung otomatis.",
        "",
        "Contoh baris yang sudah diisi tersedia di tiap sheet; ganti dengan data Anda untuk pemakaian nyata.",
    ]
    for i, text in enumerate(lines, start=3):
        ws.cell(row=i, column=1, value=text).font = BODY
    ws.column_dimensions["A"].width = 120


def sheet_data_input(wb: Workbook) -> None:
    ws = wb.create_sheet("Data Input")
    put(ws, "A1", "DATA INDUK WARGA", Font(name=FONT, bold=True, size=13))
    put(ws, "A2", "Taman Sejahtera Residence (DATA DUMMY)", BODY)
    put(ws, "A3", "Baris judul ini sengaja ada agar header berada di baris ke-11 seperti file asli.", Font(name=FONT, italic=True, size=9, color="64748B"))

    headers = ["NO", "KAVLING", "BLOCK", "NAMA WARGA", "LUAS", "JENIS PROPERTI", "STATUS HUNI", "KONTAK", "TARIF"]
    hdr_row = 11
    for i, h in enumerate(headers, start=1):
        ws.cell(row=hdr_row, column=i, value=h)
    style_header(ws, hdr_row, len(headers))

    for n, (blok, nama, tipe) in enumerate(RESIDENTS, start=1):
        luas, jenis, tarif = TIPE[tipe]
        block, kavling = blok.split("-")
        # Beberapa tarif sengaja berupa teks 'Rp 300.000' agar cleaning terlihat bekerja.
        tarif_value = f"Rp {tarif:,.0f}".replace(",", ".") if n % 4 == 0 else tarif
        status = "Dihuni" if n % 5 else "Disewakan"
        write_row(
            ws, hdr_row + n,
            [n, int(kavling), block, nama, luas, jenis, status, f"0812-0000-{n:04d}", tarif_value],
            fonts={i: INPUT for i in range(1, 10)},
            formats={9: RUPIAH},
        )
    # baris kosong di bawah (hanya nomor) -> harus dibuang oleh cleaning
    for k in range(3):
        r = hdr_row + len(RESIDENTS) + 1 + k
        write_row(ws, r, [len(RESIDENTS) + 1 + k, None, None, None, None, None, None, None, None], fonts={1: INPUT})
    set_widths(ws, [6, 10, 9, 22, 8, 16, 14, 16, 14])
    ws.freeze_panes = ws.cell(row=hdr_row + 1, column=1)


def sheet_tagihan(wb: Workbook) -> None:
    ws = wb.create_sheet("Data Tagihan")
    headers = ["No Tagihan", "Blok", "Nama Pemilik", "Jangka Pembayaran", "Iuran", "Jumlah Bulan", "Total", "Catatan"]
    for i, h in enumerate(headers, start=1):
        ws.cell(row=1, column=i, value=h)
    style_header(ws, 1, len(headers))

    for n, (blok, nama, tipe) in enumerate(UNPAID, start=1):
        iuran = TIPE[tipe][2]
        bulan, catatan = ARREARS.get(blok, (1, None))
        r = n + 1
        write_row(
            ws, r,
            [f"{n:04d}/TP1511/2026", blok, nama, PERIODE_BULAN[bulan], iuran, bulan, f"=E{r}*F{r}", catatan],
            fonts={1: INPUT, 2: INPUT, 3: INPUT, 4: INPUT, 5: INPUT, 6: INPUT, 7: BODY, 8: INPUT},
            formats={5: RUPIAH, 7: RUPIAH},
        )
    set_widths(ws, [18, 8, 22, 26, 13, 13, 14, 52])
    ws.freeze_panes = "A2"


def sheet_uang_masuk(wb: Workbook) -> None:
    ws = wb.create_sheet("Uang Masuk November 2026")
    headers = [
        "No Pembayaran", "Tanggal Pembayaran", "Nama Pemilik", "Alamat Pemilik", "Blok",
        "Nominal", "Terbilang", "Jenis Pembayaran", "Jangka Pembayaran", "Catatan Khusus",
    ]
    for i, h in enumerate(headers, start=1):
        ws.cell(row=1, column=i, value=h)
    style_header(ws, 1, len(headers))

    for n, (blok, nama, tipe) in enumerate(PAID, start=1):
        iuran = TIPE[tipe][2]
        # A-05 membayar dua bulan sekaligus, B-02 dititipkan ke pengurus (contoh catatan khusus)
        multi = blok == "A-05"
        nominal = iuran * 2 if multi else iuran
        catatan = "Pembayaran diterima melalui pengurus blok." if blok == "B-02" else None
        tanggal = dt.date(2026, 11, 1 + n)  # 2 - 13 November 2026
        r = n + 1
        write_row(
            ws, r,
            [f"TSR-{n:04d}/1611/2026", tanggal, nama, None, blok, nominal, None,
             "Iuran", "Oktober - November 2026" if multi else "November 2026", catatan],
            fonts={i: INPUT for i in range(1, 11)},
            formats={2: "dd mmmm yyyy", 6: RUPIAH},
        )
    set_widths(ws, [20, 20, 22, 18, 8, 13, 28, 18, 26, 42])
    ws.freeze_panes = "A2"


# --- aset gambar ---------------------------------------------------------------
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSerif-Bold.ttf" if bold else "DejaVuSans.ttf"
    for base in ("/usr/share/fonts/truetype/dejavu", "/Library/Fonts", "C:/Windows/Fonts"):
        try:
            return ImageFont.truetype(str(Path(base) / name), size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_logo(path: Path) -> None:
    """Logo placeholder 600x300 (rasio 2:1) bergaya lencana."""
    w, h = 600, 300
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, w - 8, h - 8), radius=36, outline="#0F766E", width=10)
    # ikon rumah sederhana
    d.polygon([(70, 150), (140, 85), (210, 150)], fill="#0F766E")
    d.rectangle((88, 150, 192, 220), fill="#14B8A6")
    d.rectangle((126, 175, 154, 220), fill="white")
    d.text((240, 70), "PAGUYUBAN WARGA", font=_font(26), fill="#334155")
    d.text((240, 108), "TAMAN", font=_font(46, True), fill="#0F766E")
    d.text((240, 164), "SEJAHTERA", font=_font(40, True), fill="#0F766E")
    d.text((240, 224), "RESIDENCE", font=_font(26), fill="#334155")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def make_signature(path: Path) -> None:
    """Tanda tangan coretan sintetis (PNG transparan, dipotong rapat ke isinya)."""
    w, h = 600, 360
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    ink = (30, 41, 130, 255)
    pts = []
    for i in range(0, 301):
        t = i / 300
        x = 40 + t * 520
        y = 190 + 120 * math.sin(t * 11) * (1 - 0.5 * t) - 30 * math.sin(t * 3.3)
        pts.append((x, y))
    d.line(pts, fill=ink, width=8, joint="curve")
    d.line([(70, 320), (300, 120), (560, 150)], fill=ink, width=6)  # garis penutup
    img = img.crop(img.getbbox())
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def main() -> None:
    (ROOT / "data").mkdir(exist_ok=True)
    wb = Workbook()
    sheet_petunjuk(wb)
    sheet_data_input(wb)
    sheet_tagihan(wb)
    sheet_uang_masuk(wb)
    target = ROOT / "data" / "sample_data.xlsx"
    wb.save(target)
    make_logo(ROOT / "assets" / "logo_placeholder.png")
    make_signature(ROOT / "assets" / "signature_placeholder.png")
    print(f"OK -> {target.relative_to(ROOT)}, assets/logo_placeholder.png, assets/signature_placeholder.png")


if __name__ == "__main__":
    main()
