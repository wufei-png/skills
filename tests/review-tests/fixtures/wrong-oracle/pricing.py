from decimal import Decimal


def premium_total(subtotal: Decimal) -> Decimal:
    """Return the final price charged to a premium member."""
    return subtotal * Decimal("0.95")
