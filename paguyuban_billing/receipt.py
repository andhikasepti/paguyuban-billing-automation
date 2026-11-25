"""Pembuatan Tanda Terima Pembayaran / Kwitansi (PDF, A5 landscape)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, landscape
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .formatting import esc, format_rupiah
from .layout import RECEIPT_THEME, derive, header_block, kv_table, make_styles, signature_block


@dataclass
class ReceiptData:
    no_kwitansi: str
    tanggal: str
    nama: str
    alamat: str
    nominal: float
    terbilang: str
    jenis_bayar: str
    periode: str
    catatan_khusus: str = ""
    blok: str = ""


def build_receipt(data: ReceiptData, settings, output_path: Path) -> Path:
    """Buat satu PDF kwitansi dan kembalikan path-nya."""
    theme = RECEIPT_THEME
    st = make_styles(theme, scale=1.08)
    org = settings.organization

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A5),
        rightMargin=25, leftMargin=25, topMargin=20, bottomMargin=20,
        title=f"Kwitansi {data.no_kwitansi}",
        author=org.name,
    )
    story = []

    # --- 1. Header -----------------------------------------------------------
    right = [
        Paragraph("TANDA TERIMA PEMBAYARAN", derive(st["title"], "title_big", fontSize=13.5, leading=16)),
        Paragraph(f"No. {esc(data.no_kwitansi)}", st["subtitle"]),
    ]
    story.append(header_block(settings, st, logo_box=(105, 52), left_width=320, right_flowables=right))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(theme.accent), spaceBefore=0, spaceAfter=8))

    # --- 2. Rincian ----------------------------------------------------------
    story.append(
        kv_table(
            [
                ("Telah Terima Dari Bpk/Ibu", Paragraph(f"<b>{esc(data.nama)}</b>", st["value_bold"])),
                ("Alamat / Unit", Paragraph(esc(data.alamat), st["value"])),
                ("Untuk Pembayaran", Paragraph(f"{esc(data.jenis_bayar)} — <b>Bulan {esc(data.periode)}</b>", st["value"])),
            ],
            st, col_widths=[130, 10, 410], pad=2,
        )
    )
    story.append(Spacer(1, 8))

    # --- 3. Kotak nominal ----------------------------------------------------
    green = colors.HexColor("#16A34A")
    box = Table(
        [
            [
                Paragraph("JUMLAH PEMBAYARAN", st["label"]),
                Paragraph("STATUS", derive(st["label"], "lbl_status", alignment=2)),
            ],
            [
                Paragraph(format_rupiah(data.nominal), st["amount"]),
                Paragraph("<b>LUNAS</b>", derive(st["value_bold"], "status_val", fontSize=11, alignment=2, textColor=green)),
            ],
            [Paragraph(f"<i>Terbilang: {esc(data.terbilang)}</i>", st["terbilang"]), Paragraph("", st["terbilang"])],
        ],
        colWidths=[400, 150],
    )
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(theme.box_bg)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(theme.box_border)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(theme.box_divider)),
            ]
        )
    )
    story.append(box)
    story.append(Spacer(1, 8))

    # --- 4. Catatan + tanda tangan -------------------------------------------
    notes = [
        Paragraph("<b>Catatan Tambahan:</b>", st["note"]),
        Paragraph(f"• Tanda terima ini merupakan bukti pembayaran resmi dari {esc(org.short_name)}.", st["note"]),
    ]
    if data.catatan_khusus:
        notes.append(Paragraph(f"• <b>{esc(data.catatan_khusus)}</b>", st["note"]))

    note_table = Table([[notes]], colWidths=[370])
    note_table.setStyle(
        TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)])
    )

    footer = Table([[note_table, signature_block(settings, st, data.tanggal, sig_box=(70, 38), col_width=180)]], colWidths=[370, 180])
    footer.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(footer)

    doc.build(story)
    return Path(output_path)
