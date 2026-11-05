from datetime import date
from decimal import Decimal
from pathlib import Path
import re

from flask import Blueprint, current_app, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

from app.calculations import calculate_total
from app.numbering import peek_next_invoice_number, commit_invoice_number
from app.pdf_generator import generate_invoice_pdf

main = Blueprint("main", __name__)


def format_amount(amount: Decimal, currency: str) -> str:
    symbol = "J$" if currency == "JMD" else "US$"
    return f"{symbol}{amount:,.2f}"


@main.get("/")
def home():
    return render_template("index.html", today=date.today().isoformat())


@main.post("/generate")
def generate():
    try:
        customer_name = request.form.get("customer_name", "").strip()
        issue_date = request.form.get("issue_date", "").strip()
        currency = request.form.get("currency", "JMD").strip().upper()
        payment_status = request.form.get("payment_status", "unpaid").strip().lower()
        notes = request.form.get("notes", "").strip()
        doc_type = request.form.get("doc_type", "invoice").strip().lower()

        if not customer_name or not issue_date:
            raise ValueError("Customer name and issue date are required.")
        if currency not in {"JMD", "USD"}:
            raise ValueError("Choose JMD or USD.")
        if doc_type not in {"invoice", "pro_forma", "quote"}:
            raise ValueError("Choose a valid document type.")
        if payment_status not in {"unpaid", "partially paid", "paid"}:
            raise ValueError("Choose a valid payment status.")

        # Extract multi-item arrays from form submission
        descriptions = request.form.getlist("description[]")
        quantities = request.form.getlist("quantity[]")
        unit_prices = request.form.getlist("unit_price[]")

        if not descriptions or not any(d.strip() for d in descriptions):
            raise ValueError("At least one line item description is required.")

        items = []
        grand_total = Decimal("0.00")
        for desc, qty_str, price_str in zip(descriptions, quantities, unit_prices):
            # Replace newlines with spaces so text stays neatly on one line per item
            desc_clean = " ".join(desc.split())
            if not desc_clean:
                continue

            qty, unit_price, line_total = calculate_total(qty_str, price_str)
            grand_total += line_total

            items.append({
                "description": desc_clean,
                "quantity": f"{qty:g}",
                "unit_price_display": format_amount(unit_price, currency),
                "total_display": format_amount(line_total, currency),
            })
        if not items:
            raise ValueError("Please provide at least one valid line item.")

        # Peek at the next number using the document type sequence
        number = peek_next_invoice_number(current_app.config["DATA_DIR"], doc_type)
        invoice = {
            "number": number,
            "doc_type": doc_type,
            "issue_date": issue_date,
            "customer_name": customer_name,
            "items": items,
            "total_due_display": format_amount(grand_total, currency),
            "currency": currency,
            "payment_status": payment_status,
            "notes": notes,
        }

        filename = secure_filename(f"{number}_{customer_name}.pdf")
        output_path = Path(current_app.config["GENERATED_DIR"]) / filename

        # Generate the PDF first
        generate_invoice_pdf(invoice, output_path)

        # Commit the number only when PDF generation succeeds
        commit_invoice_number(current_app.config["DATA_DIR"], doc_type)

        return send_file(output_path, as_attachment=True, download_name=filename, mimetype="application/pdf")
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("main.home"))
