from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def money(value: str | int | float) -> Decimal:
    """Parse a monetary value safely and round it to two decimal places."""
    try:
        amount = Decimal(str(value).strip() or "0")
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid monetary amount.")

    if not amount.is_finite() or amount < 0:
        raise ValueError("Amounts must be zero or greater.")

    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total(quantity: str, unit_price: str) -> tuple[Decimal, Decimal, Decimal]:
    try:
        qty = Decimal(str(quantity).strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid quantity.")

    if not qty.is_finite() or qty <= 0:
        raise ValueError("Quantity must be greater than zero.")

    price = money(unit_price)
    line_total = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return qty, price, line_total
