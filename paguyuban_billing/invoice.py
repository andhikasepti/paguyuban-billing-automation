"""Pembuatan Surat Tagihan Pembayaran Iuran (PDF, A5 landscape)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, landscape
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .formatting import esc, format_rupiah
from .layout import INVOICE_THEME, derive, header_block, kv_table, make_styles, signature_block


@dataclass
class InvoiceData:
    no_tagihan: str
    nama: str
    blok: str
    alamat: str
    periode: str
    total: float
    iuran_per_bulan: float = 0.0
    jumlah_bulan: int = 1
    catatan: str = ""


def build_invoice(data: InvoiceData, settings, output_path: Path) -> Path:
    """Buat satu PDF surat tagihan dan kembalikan path-nya."""
    theme = INVOICE_THEME
    st = make_styles(theme)
    bank = settings.bank
    org = settings.organization

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A5),
        rightMargin=20, leftMargin=20, topMargin=12, bottomMargin=12,
        title=f"Tagihan {data.no_tagihan}",
        author=org.name,
    )
    story = []

    # --- 1. Header -----------------------------------------------------------
    meta = kv_table(
        [
            ("<b>No. Tagihan</b>", Paragraph(esc(data.no_tagihan), st["value"])),
            ("<b>Hal</b>", Paragraph("Tagihan Iuran Bulanan", st["value"])),
        ],
        st, col_widths=[60, 10, 160], pad=1,
    )
    right = [Paragraph("TAGIHAN PEMBAYARAN IURAN", st["title"]), Spacer(1, 4), meta]
    story.append(header_block(settings, st, logo_box=(95, 48), left_width=320, right_flowables=right))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor(theme.accent), spaceBefore=0, spaceAfter=8))

    # --- 2. Penerima tagihan -------------------------------------------------
    story.append(
        kv_table(
            [
                ("Kepada Yth. Bapak/Ibu", Paragraph(f"<b>{esc(data.nama)}</b>", st["value_bold"])),
                ("Alamat / Unit", Paragraph(esc(data.alamat), st["value"])),
                ("Periode Tagihan", Paragraph(f"<b>Bulan {esc(data.periode)}</b>", st["value_bold"])),
            ],
            st, col_widths=[110, 10, 430],
        )
    )
    story.append(Spacer(1, 5))

    # --- 3. Kotak total tagihan ----------------------------------------------
    box = Table(
        [
            [
                Paragraph("TOTAL TAGIHAN PEMBAYARAN", derive(st["label"], "lbl_inv", fontSize=7.5, textColor=colors.HexColor(theme.accent))),
                Paragraph(
                    f'STATUS: <font color="{theme.accent}"><b>BELUM DIBAYAR</b></font>',
                    derive(st["label"], "lbl_status", fontSize=7.5, alignment=2),
                ),
            ],
            [
                Paragraph(format_rupiah(data.total), st["amount"]),
                Paragraph(
                    f"<i>Mohon melakukan pembayaran sebelum tanggal {settings.billing.due_day}</i>",
                    derive(st["note"], "due_note", alignment=2, textColor=colors.HexColor(theme.secondary)),
                ),
            ],
        ],
        colWidths=[330, 220],
    )
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(theme.box_bg)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(theme.box_border)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(theme.box_divider)),
            ]
        )
    )
    story.append(box)
    story.append(Spacer(1, 5))

    # --- 4. Informasi transfer bank ------------------------------------------
    bold = st["value_bold"]
    bank_rows = [
        [Paragraph("<b>Metode Pembayaran Transfer Bank:</b>", st["label"]), "", ""],
        [Paragraph("<b>Bank / Rekening</b>", bold), Paragraph(":", st["label"]),
         Paragraph(f"<b>{esc(bank.name)}</b> / <b>{esc(bank.account_number)}</b>", st["value"])],
        [Paragraph("<b>Atas Nama</b>", bold), Paragraph(":", st["label"]),
         Paragraph(esc(bank.account_holder), st["value"])],
        [Paragraph("<b>Konfirmasi Transfer</b>", bold), Paragraph(":", st["label"]),
         Paragraph(f"Kirim bukti transfer ke WhatsApp Admin <b>({esc(org.whatsapp)})</b>", st["value"])],
    ]
    bank_table = Table(bank_rows, colWidths=[110, 15, 425])
    bank_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (2, 0)),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(theme.panel_bg)),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(theme.panel_border)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (0, -1), 6),
                ("RIGHTPADDING", (0, 0), (0, -1), 2),
                ("LEFTPADDING", (1, 0), (1, -1), 0),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("LEFTPADDING", (2, 0), (2, -1), 2),
                ("RIGHTPADDING", (2, 0), (2, -1), 6),
            ]
        )
    )
    story.append(bank_table)
    story.append(Spacer(1, 5))

    # --- 5. Catatan (hanya jika perlu) ---------------------------------------
    multi_month = data.jumlah_bulan > 1
    if multi_month or data.catatan:
        story.append(Paragraph("<b>Catatan:</b>", st["note"]))
        nomor = 1
        if multi_month:
            story.append(Paragraph(f"{nomor}. Besar iuran bulanan {format_rupiah(data.iuran_per_bulan)}", st["note"]))
            nomor += 1
        if data.catatan:
            story.append(Paragraph(f"{nomor}. {esc(data.catatan)}", st["note"]))
        story.append(Spacer(1, 3))

    # --- 6. Penutup & tanda tangan -------------------------------------------
    story.append(
        Paragraph("Demikian surat tagihan ini kami sampaikan. Atas perhatian Bapak/Ibu, terima kasih.", st["closing"])
    )
    story.append(Spacer(1, 4))

    sign = Table([["", signature_block(settings, st, _tanggal_surat(settings), sig_box=(60, 30))]], colWidths=[360, 190])
    sign.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(sign)

    doc.build(story)
    return Path(output_path)


def _tanggal_surat(settings) -> str:
    from .formatting import tanggal_hari_ini

    return settings.billing.invoice_date or tanggal_hari_ini()
