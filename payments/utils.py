import os
import io
import decimal
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def generate_invoice_pdf(invoice):
    """
    Generates a professional PDF for the invoice and saves it in storage.
    Includes promo code discount line items if applied.
    Returns the relative path to the generated PDF.
    """
    filename = f"invoice_{invoice.invoice_number}.pdf"

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0A1128"),
        spaceAfter=15
    )

    right_title_style = ParagraphStyle(
        name="InvoiceRightTitle",
        parent=title_style,
        alignment=TA_RIGHT
    )

    meta_label_style = ParagraphStyle(
        name="MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569")
    )

    meta_val_style = ParagraphStyle(
        name="MetaValue",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )

    table_header_style = ParagraphStyle(
        name="TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )

    right_cell_style = ParagraphStyle(
        name="RightCell",
        parent=table_cell_style,
        alignment=TA_RIGHT
    )

    right_header_style = ParagraphStyle(
        name="RightHeader",
        parent=table_header_style,
        alignment=TA_RIGHT
    )

    story = []

    # Header Section
    header_data = [
        [
            Paragraph("<b>RISE360 INSTITUTE</b><br/><font size=9 color='#64748B'>Master the Enrolled Agent Exam</font>", meta_val_style),
            Paragraph("<b>INVOICE</b>", right_title_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # Metadata
    meta_data = [
        [
            Paragraph("<b>BILLED TO:</b>", meta_label_style),
            Paragraph("<b>INVOICE DETAILS:</b>", meta_label_style)
        ],
        [
            Paragraph(
                f"{invoice.user.get_full_name or invoice.user.email}<br/>"
                f"Email: {invoice.user.email}<br/>"
                f"Phone: {getattr(invoice.user, 'phone', None) or 'N/A'}",
                meta_val_style
            ),
            Paragraph(
                f"Invoice No: <b>{invoice.invoice_number}</b><br/>"
                f"Date: {invoice.created_at.strftime('%Y-%m-%d')}<br/>"
                f"Status: <b>{invoice.payment_status.upper()}</b>",
                meta_val_style
            )
        ]
    ]
    meta_table = Table(meta_data, colWidths=[3.5 * inch, 3.5 * inch])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 15),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Line Items Table
    plan_name = invoice.subscription.plan
    duration_str = "Lifetime" if invoice.subscription.lifetime else (
        "30 Days" if plan_name == "Monthly" else "365 Days"
    )

    orig_val = invoice.original_amount if invoice.original_amount else (invoice.amount + invoice.discount_amount)
    disc_val = invoice.discount_amount or decimal.Decimal("0.00")
    promo_label = f" ({invoice.promo_code_str})" if invoice.promo_code_str else ""

    items_data = [
        [
            Paragraph("Description", table_header_style),
            Paragraph("Duration", table_header_style),
            Paragraph("Amount (INR)", right_header_style)
        ],
        [
            Paragraph(f"MCQ Subscription - {plan_name} Plan", table_cell_style),
            Paragraph(duration_str, table_cell_style),
            Paragraph(f"INR {orig_val}", right_cell_style)
        ],
    ]

    if disc_val > 0:
        items_data.append([
            Paragraph("", table_cell_style),
            Paragraph(f"<b>Promo Discount{promo_label}</b>", right_cell_style),
            Paragraph(f"- INR {disc_val}", right_cell_style)
        ])

    items_data.extend([
        [
            Paragraph("", table_cell_style),
            Paragraph("<b>Tax (GST 0%)</b>", right_cell_style),
            Paragraph(f"INR {invoice.gst}", right_cell_style)
        ],
        [
            Paragraph("", table_cell_style),
            Paragraph("<b>Total Paid</b>", right_cell_style),
            Paragraph(f"<b>INR {invoice.total}</b>", right_cell_style)
        ]
    ])

    items_table = Table(items_data, colWidths=[3.5 * inch, 1.5 * inch, 2.0 * inch])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A1128")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, 1), 0.5, colors.HexColor("#cbd5e1")),
        ("LINEBELOW", (1, 2), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 30))

    footer_style = ParagraphStyle(
        name="InvoiceFooter",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.HexColor("#64748B")
    )
    story.append(Paragraph("Thank you for choosing RISE360 Institute! This is a system-generated invoice.", footer_style))

    doc.build(story)

    relative_path = f"invoices/{filename}"
    pdf_buffer.seek(0)
    default_storage.save(relative_path, ContentFile(pdf_buffer.getvalue()))

    invoice.pdf_path = relative_path
    invoice.save(update_fields=["pdf_path"])
    return relative_path
