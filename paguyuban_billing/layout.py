"""Komponen layout PDF yang dipakai bersama oleh tagihan dan kwitansi."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from .formatting import esc


@dataclass(frozen=True)
class Theme:
    """Skema warna dokumen."""

    primary: str = "#1E293B"
    secondary: str = "#475569"
    text: str = "#334155"
    muted: str = "#64748B"
    accent: str = "#E11D48"      # garis pemisah
    title: str = "#E11D48"       # warna judul dokumen
    amount: str = "#E11D48"      # warna nominal
    box_bg: str = "#FFF1F2"      # latar kotak nominal
    box_border: str = "#FECDD3"
    box_divider: str = "#FFE4E6"
    panel_bg: str = "#F8FAFC"
    panel_border: str = "#CBD5E1"


INVOICE_THEME = Theme()
RECEIPT_THEME = Theme(
    accent="#D97706",
    title="#1E293B",
    amount="#0284C7",
    box_bg="#F8FAFC",
    box_border="#CBD5E1",
    box_divider="#E2E8F0",
)


def make_styles(theme: Theme, scale: float = 1.0) -> Dict[str, ParagraphStyle]:
    """Buat kumpulan ParagraphStyle. `scale` memperbesar/memperkecil seluruh teks."""
    base = getSampleStyleSheet()["Normal"]

    def ps(name: str, font: str, size: float, color: str, **kw) -> ParagraphStyle:
        return ParagraphStyle(
            name,
            parent=base,
            fontName=font,
            fontSize=size * scale,
            leading=(size + 3) * scale,
            textColor=colors.HexColor(color),
            **kw,
        )

    return {
        "title": ps("title", "Helvetica-Bold", 11.5, theme.title, alignment=2),
        "subtitle": ps("subtitle", "Helvetica-Bold", 8.5, "#0284C7", alignment=2),
        "org": ps("org", "Helvetica-Bold", 9.5, theme.primary),
        "org_sub": ps("org_sub", "Helvetica", 7.5, theme.secondary),
        "label": ps("label", "Helvetica-Bold", 8, theme.secondary),
        "value": ps("value", "Helvetica", 8, theme.text),
        "value_bold": ps("value_bold", "Helvetica-Bold", 8.5, theme.primary),
        "amount": ps("amount", "Helvetica-Bold", 12.5, theme.amount),
        "note": ps("note", "Helvetica", 7.5, theme.muted),
        "closing": ps("closing", "Helvetica-Oblique", 8, theme.secondary),
        "terbilang": ps("terbilang", "Helvetica-Oblique", 8, theme.secondary),
    }


def derive(style: ParagraphStyle, name: str, **overrides) -> ParagraphStyle:
    """Turunan style dengan sebagian atribut diganti (mis. alignment)."""
    return ParagraphStyle(name, parent=style, **overrides)


def fit_image(path: Path, max_w: float, max_h: float):
    """Gambar yang dipaskan ke kotak max_w x max_h dengan menjaga rasio.

    Jika file tidak ada, diganti Spacer agar dokumen tetap bisa dibuat.
    """
    path = Path(path)
    if not path.exists():
        return Spacer(max_w, max_h)
    w, h = ImageReader(str(path)).getSize()
    scale = min(max_w / w, max_h / h)
    return Image(str(path), width=w * scale, height=h * scale)


def kv_table(rows: List[tuple], styles: Dict[str, ParagraphStyle], col_widths, pad=1.5) -> Table:
    """Tabel 'label : nilai' tanpa garis."""
    data = [
        [Paragraph(label, styles["label"]), Paragraph(":", styles["label"]), value]
        for label, value in rows
    ]
    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            ]
        )
    )
    return table


def header_block(settings, styles, logo_box, left_width, right_flowables, col_widths=(320, 230)):
    """Header: logo + identitas organisasi di kiri, judul dokumen di kanan."""
    org = settings.organization
    logo = fit_image(settings.assets.logo, *logo_box)
    org_text = [
        Paragraph(esc(org.name), styles["org"]),
        Spacer(1, 1),
        Paragraph(esc(org.address), styles["org_sub"]),
        Paragraph(f"WhatsApp Admin: {esc(org.whatsapp)}", styles["org_sub"]),
    ]
    left = Table([[logo, org_text]], colWidths=[logo_box[0] + 5, left_width - logo_box[0] - 5])
    left.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    header = Table([[left, right_flowables]], colWidths=list(col_widths))
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return header


def signature_block(settings, styles, date_text: str, sig_box=(50, 32), col_width: float = 180) -> list:
    """Blok kota/tanggal, jabatan, tanda tangan, dan nama ketua (rata tengah)."""
    center = lambda key, name, **kw: derive(styles[key], name, alignment=1, **kw)
    # Image di dalam sel tabel tidak otomatis rata tengah (menempel ke kiri),
    # jadi dibungkus tabel selebar kolom supaya sejajar dengan teks di atas/bawahnya.
    sig_img = Table([[fit_image(settings.assets.signature, *sig_box)]], colWidths=[col_width])
    sig_img.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [
        Paragraph(f"{esc(settings.organization.city)}, {esc(date_text)}", center("value", "sig_date")),
        Spacer(1, 2),
        Paragraph(f"<b>{esc(settings.organization.chairman_title)}</b>", center("value_bold", "sig_role", fontSize=8)),
        Spacer(1, 2),
        sig_img,
        Spacer(1, 2),
        Paragraph(f"<b>{esc(settings.organization.chairman_name)}</b>", center("value_bold", "sig_name")),
    ]
