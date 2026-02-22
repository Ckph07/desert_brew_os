"""
Note Renderer - PDF and PNG generation for sales notes.

Purpose: Generate professional sales notes matching the Desert Brew Co. format.
Uses ReportLab for PDF and Pillow for PNG conversion.

Format matches the real business notes:
- Header: Desert Brew Co. logo area, PEDIDO number, date
- Issuer: Razón social, RFC, Dirección, Teléfono
- Client: CLIENT name, FORMA DE PAGO
- Table: Cantidad | Descripción | P.U. | Precio
- Footer: Total liters, Subtotal, I.E.P.S, I.V.A, TOTAL
"""
import io
from decimal import Decimal
from datetime import datetime


class NoteRenderer:
    """Render sales notes as PDF/PNG matching Desert Brew Co. format."""

    @staticmethod
    def render_pdf(note, items: list, logo_path: str | None = None) -> bytes:
        """
        Generate PDF of sales note using ReportLab.

        Args:
            note: SalesNote model instance
            items: List of SalesNoteItem model instances
            logo_path: Optional path to logo image

        Returns:
            PDF file as bytes
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=2 * mm,
            fontName='Helvetica-Bold',
        )
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica',
        )
        bold_style = ParagraphStyle(
            'BoldStyle',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
        )
        red_bold_style = ParagraphStyle(
            'RedBold',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#CC0000'),
        )

        # --- HEADER ---
        note_date = note.created_at.strftime("%d/%m/%y") if note.created_at else datetime.utcnow().strftime("%d/%m/%y")

        header_data = [
            [
                Paragraph("Cervecería<br/><b>DESERT BREW CO.</b><br/><i>Saltillo, Coahuila</i>", header_style),
                "",
                Paragraph(f"<b>PEDIDO:</b>", bold_style),
                Paragraph(f"<font color='#CC0000'><b>{note.note_number}</b></font>", red_bold_style),
            ],
            [
                "",
                "",
                Paragraph("<b>FECHA:</b>", bold_style),
                Paragraph(f"<font color='#CC0000'><b>{note_date}</b></font>", red_bold_style),
            ],
        ]
        header_table = Table(header_data, colWidths=[55 * mm, 30 * mm, 30 * mm, 45 * mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('SPAN', (0, 0), (0, 1)),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 8 * mm))

        # --- ISSUER INFO ---
        issuer_data = [
            [
                Paragraph(f"Razón social: {note.issuer_name}", header_style),
                Paragraph(f"Dirección: {note.issuer_address}", header_style),
            ],
            [
                Paragraph(f"RFC:{note.issuer_rfc}", header_style),
                Paragraph(f"Teléfono: {note.issuer_phone}", header_style),
            ],
        ]
        issuer_table = Table(issuer_data, colWidths=[85 * mm, 85 * mm])
        issuer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(issuer_table)
        elements.append(Spacer(1, 5 * mm))

        # --- CLIENT INFO ---
        client_name = note.client_name or "—"
        payment = note.payment_method or "—"
        elements.append(Paragraph(f"<b>CLIENTE:  {client_name}</b>", bold_style))
        elements.append(Paragraph(f" FORMA DE PAGO: {payment.upper()}", header_style))
        elements.append(Spacer(1, 6 * mm))

        # --- ITEMS TABLE ---
        item_header = [
            Paragraph("<b>Cantidad</b>", bold_style),
            Paragraph("<b>Descripción</b>", bold_style),
            Paragraph("<b>P.U.</b>", bold_style),
            Paragraph("<b>Precio</b>", bold_style),
        ]

        table_data = [item_header]
        for item in items:
            qty = float(item.quantity)
            qty_str = f"{int(qty)}" if qty == int(qty) else f"{qty:.2f}"
            unit_price_str = f"$ {float(item.unit_price):>10,.2f}"
            line_str = f"$ {float(item.subtotal):>10,.2f}"

            table_data.append([
                Paragraph(qty_str, header_style),
                Paragraph(f"{item.product_name}", header_style),
                Paragraph(unit_price_str, header_style),
                Paragraph(line_str, header_style),
            ])

        items_table = Table(table_data, colWidths=[20 * mm, 80 * mm, 30 * mm, 35 * mm])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            # Grid
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#CC0000')),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            # Row lines
            ('LINEBELOW', (0, 1), (-1, -2), 0.25, colors.HexColor('#dddddd')),
            # Alignment
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 6 * mm))

        # --- TOTALS ---
        total_liters = float(note.total_liters or 0)
        liters_str = f"{int(total_liters)}  L" if total_liters == int(total_liters) else f"{total_liters:.1f}  L"

        subtotal_str = f"${float(note.subtotal):,.2f}"
        ieps_str = f"${float(note.ieps_total):,.2f}" if note.include_taxes and float(note.ieps_total) > 0 else ""
        iva_str = f"${float(note.iva_total):,.2f}" if note.include_taxes and float(note.iva_total) > 0 else ""
        total_str = f"$ {float(note.total):>10,.2f}"

        totals_data = [
            [Paragraph(f"<b>{liters_str}</b>", bold_style), "", Paragraph("<b>Subtotal</b>", bold_style), Paragraph(subtotal_str, header_style)],
            ["", "", Paragraph("<b>I.E.P.S</b>", bold_style), Paragraph(ieps_str, header_style)],
            ["", "", Paragraph("<b>I.V.A</b>", bold_style), Paragraph(iva_str, header_style)],
            ["", "", "", ""],
            ["", "", Paragraph("<b>TOTAL</b>", bold_style), Paragraph(f"<b>{total_str}</b>", bold_style)],
        ]

        totals_table = Table(totals_data, colWidths=[25 * mm, 75 * mm, 30 * mm, 35 * mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
            ('LINEABOVE', (2, 4), (3, 4), 1, colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(totals_table)

        # Build PDF
        doc.build(elements)
        return buffer.getvalue()

    @staticmethod
    def render_png(note, items: list, dpi: int = 150) -> bytes:
        """
        Render sales note as PNG by converting PDF to image.

        Uses Pillow to draw a simplified version of the note.
        """
        from PIL import Image, ImageDraw, ImageFont

        # Page dimensions at given DPI
        w = int(8.5 * dpi)
        h = int(11 * dpi)
        img = Image.new('RGB', (w, h), 'white')
        draw = ImageDraw.Draw(img)

        # Fonts (use default since custom fonts may not be available)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=int(dpi * 0.1))
            font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=int(dpi * 0.1))
            font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=int(dpi * 0.15))
        except (OSError, IOError):
            font = ImageFont.load_default()
            font_bold = font
            font_title = font

        margin = int(dpi * 0.75)
        y = margin

        # Red color for accents
        red = (204, 0, 0)
        black = (0, 0, 0)
        gray = (100, 100, 100)

        # --- HEADER ---
        draw.text((margin, y), "Cervecería", fill=gray, font=font)
        y += int(dpi * 0.12)
        draw.text((margin, y), "DESERT BREW CO.", fill=black, font=font_title)

        # PEDIDO number (right side)
        note_date = note.created_at.strftime("%d/%m/%y") if note.created_at else ""
        draw.text((w - margin - int(dpi * 2), margin), f"PEDIDO:     {note.note_number}", fill=red, font=font_bold)
        draw.text((w - margin - int(dpi * 2), margin + int(dpi * 0.15)), f"FECHA:       {note_date}", fill=red, font=font_bold)

        y += int(dpi * 0.3)

        # --- ISSUER ---
        draw.text((margin, y), f"Razón social: {note.issuer_name}", fill=black, font=font)
        draw.text((w // 2, y), f"Dirección: {note.issuer_address}", fill=black, font=font)
        y += int(dpi * 0.12)
        draw.text((margin, y), f"RFC:{note.issuer_rfc}", fill=black, font=font)
        draw.text((w // 2, y), f"Teléfono: {note.issuer_phone}", fill=black, font=font)
        y += int(dpi * 0.2)

        # --- CLIENT ---
        client_name = note.client_name or "—"
        draw.text((margin, y), f"CLIENTE:  {client_name}", fill=black, font=font_bold)
        y += int(dpi * 0.12)
        draw.text((margin, y), f" FORMA DE PAGO: {(note.payment_method or '').upper()}", fill=black, font=font)
        y += int(dpi * 0.2)

        # --- TABLE HEADER ---
        col_x = [margin, margin + int(dpi * 0.6), w // 2 + int(dpi * 0.5), w - margin - int(dpi * 1)]
        draw.line([(margin, y), (w - margin, y)], fill=red, width=2)
        y += int(dpi * 0.05)
        draw.text((col_x[0], y), "Cantidad", fill=black, font=font_bold)
        draw.text((col_x[1], y), "Descripción", fill=black, font=font_bold)
        draw.text((col_x[2], y), "P.U.", fill=black, font=font_bold)
        draw.text((col_x[3], y), "Precio", fill=black, font=font_bold)
        y += int(dpi * 0.15)
        draw.line([(margin, y), (w - margin, y)], fill=red, width=1)
        y += int(dpi * 0.05)

        # --- TABLE ITEMS ---
        for item in items:
            qty = float(item.quantity)
            qty_str = f"{int(qty)}" if qty == int(qty) else f"{qty:.2f}"
            draw.text((col_x[0], y), qty_str, fill=black, font=font)
            draw.text((col_x[1], y), item.product_name, fill=black, font=font)
            draw.text((col_x[2], y), f"$ {float(item.unit_price):,.2f}", fill=black, font=font)
            draw.text((col_x[3], y), f"$ {float(item.subtotal):,.2f}", fill=black, font=font)
            y += int(dpi * 0.15)

        y += int(dpi * 0.15)

        # --- TOTALS ---
        total_liters = float(note.total_liters or 0)
        liters_str = f"{int(total_liters)}  L" if total_liters == int(total_liters) else f"{total_liters:.1f}  L"
        draw.text((margin, y), liters_str, fill=black, font=font_bold)

        right_col = w - margin - int(dpi * 1.8)
        draw.text((right_col, y), "Subtotal", fill=black, font=font_bold)
        draw.text((right_col + int(dpi * 0.8), y), f"${float(note.subtotal):,.2f}", fill=black, font=font)
        y += int(dpi * 0.13)

        draw.text((right_col, y), "I.E.P.S", fill=black, font=font_bold)
        if note.include_taxes and float(note.ieps_total or 0) > 0:
            draw.text((right_col + int(dpi * 0.8), y), f"${float(note.ieps_total):,.2f}", fill=black, font=font)
        y += int(dpi * 0.13)

        draw.text((right_col, y), "I.V.A", fill=black, font=font_bold)
        if note.include_taxes and float(note.iva_total or 0) > 0:
            draw.text((right_col + int(dpi * 0.8), y), f"${float(note.iva_total):,.2f}", fill=black, font=font)
        y += int(dpi * 0.2)

        draw.line([(right_col, y), (w - margin, y)], fill=black, width=1)
        y += int(dpi * 0.05)
        draw.text((right_col, y), "TOTAL", fill=black, font=font_bold)
        draw.text((right_col + int(dpi * 0.8), y), f"$ {float(note.total):,.2f}", fill=black, font=font_bold)

        # Save PNG
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
