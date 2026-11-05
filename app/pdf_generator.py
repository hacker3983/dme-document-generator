from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from config import BUSINESS_NAME, BUSINESS_SHORT_NAME, LOGO_PATH


def generate_invoice_pdf(invoice: dict, output_path: Path) -> None:
    """Render a document PDF matching the precise DME reference template layout."""
    doc_type = invoice.get("doc_type", "invoice")
    title_map = {
        "invoice": "Invoice",
        "pro_forma": "Pro Forma Invoice",
        "quote": "Quote"
    }
    doc_title_prefix = title_map.get(doc_type, "Invoice")

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=10 * mm, bottomMargin=18 * mm,
        title=f"{doc_title_prefix} {invoice['number']}",
        author=BUSINESS_NAME,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=colors.black, spaceAfter=2))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#555555")))
    styles.add(ParagraphStyle(name="CenterFooter", parent=styles["Normal"], alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.black))
    
    styles.add(ParagraphStyle(
        name="SectionLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#555555")
    ))
    styles.add(ParagraphStyle(
        name="CustomerName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.black
    ))
    styles.add(ParagraphStyle(
        name="PreparedMain",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.black
    ))
    styles.add(ParagraphStyle(
        name="PreparedSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.black
    ))
    styles.add(ParagraphStyle(
        name="HeaderTitle", 
        parent=styles["Normal"], 
        alignment=TA_RIGHT, 
        fontName="Helvetica-Bold",
        fontSize=19, 
        leading=22
    ))

    story = []
    
    # --- Top Header: Logo on Left, Title & Meta on Right ---
    if LOGO_PATH.exists():
        from reportlab.platypus import Image
        logo = Image(str(LOGO_PATH), width=4.5 * cm, height=2.3 * cm)
        brand_cell = logo
    else:
        brand_cell = Paragraph(f"{BUSINESS_NAME}<br/><font size='9'>{BUSINESS_SHORT_NAME}</font>", styles["Brand"])

    header_title = doc_title_prefix.upper()
    number_label_map = {
        "invoice": "Invoice No.",
        "pro_forma": "Pro Forma No.",
        "quote": "Quote No."
    }
    number_label = number_label_map.get(doc_type, "Invoice No.")

    # Explicitly map short currency codes to the full reference description
    raw_currency = invoice.get('currency', 'JMD')
    if raw_currency in ['JMD', 'Jamaican Dollars (JMD)']:
        currency_display = "Jamaican Dollars (JMD), with USD product references"
    else:
        currency_display = raw_currency

    meta_text = f"""
    <b>{number_label}:</b> {invoice['number']}<br/>
    <b>Issue Date:</b> {invoice['issue_date']}<br/>
    <font color="#666666"><b>Currency:</b> {currency_display}</font>
    """
    
    right_inner_table = Table([
        [Paragraph(header_title, styles["HeaderTitle"])],
        [Spacer(1, 3 * mm)],
        [Paragraph(meta_text, ParagraphStyle("MetaSub", parent=styles["Normal"], fontSize=9, leading=14))]
    ], colWidths=[96 * mm])
    
    right_inner_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    header = Table([[brand_cell, right_inner_table]], colWidths=[78 * mm, 96 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (0, 0), 5 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    
    story.extend([
        header, 
        HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=4, spaceAfter=10, hAlign="CENTER")
    ])

    # --- Bill To / Prepared By Section ---
    prepared_content = Paragraph(f"<b>{BUSINESS_NAME}</b>", styles["PreparedMain"])
    prepared_sub_content = Paragraph(BUSINESS_SHORT_NAME, styles["PreparedSub"])

    details = Table([
        [Paragraph("BILL TO", styles["SectionLabel"]), Paragraph("PREPARED BY", styles["SectionLabel"])],
        [Paragraph(escape(invoice["customer_name"]), styles["CustomerName"]), [prepared_content, prepared_sub_content]],
    ], colWidths=[87 * mm, 87 * mm])
    details.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([details, Spacer(1, 10 * mm)])

    # --- Line Items Table ---
    table_data = [
        ["ITEM / DESCRIPTION", "QTY", "UNIT PRICE", "AMOUNT"]
    ]

    for item in invoice.get("items", []):
        table_data.append([
            Paragraph(escape(item["description"]), styles["Normal"]),
            item["quantity"],
            item["unit_price_display"],
            item["total_display"]
        ])

    item_table = Table(table_data, colWidths=[86 * mm, 18 * mm, 35 * mm, 35 * mm])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D5D5D5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([item_table, Spacer(1, 8 * mm)])

    # --- Total Amount Due Block ---
    total_table = Table([["TOTAL AMOUNT DUE", invoice["total_due_display"]]], colWidths=[120 * mm, 54 * mm])
    total_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    story.extend([total_table, Spacer(1, 8 * mm)])

    # --- Payment Status & Notes Section ---
    story.append(Paragraph(f"<b>Payment status:</b> {invoice['payment_status'].title()}", styles["Normal"]))
    
    if invoice.get("notes"):
        story.extend([
            Spacer(1, 5 * mm), 
            Paragraph("<b>NOTES & TERMS</b>", styles["Normal"]), 
            Spacer(1, 2 * mm),
            Paragraph(escape(invoice["notes"]).replace("\n", "<br/>"), styles["SmallMuted"])
        ])

    # --- Centered Footer ---
    story.extend([
        Spacer(1, 14 * mm), 
        Paragraph("Thank you for choosing Dujohn Mobile Essentials.", styles["CenterFooter"])
    ])
    
    doc.build(story)
