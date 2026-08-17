import unittest
from decimal import Decimal

from pricing import premium_total


def expected_from_current_formula(subtotal: Decimal) -> Decimal:
    return subtotal - subtotal * Decimal("0.05")


class PremiumPricingTests(unittest.TestCase):
    def test_calculates_premium_total(self) -> None:
        subtotal = Decimal("100.00")

        self.assertEqual(
            premium_total(subtotal),
            expected_from_current_formula(subtotal),
        )


if __name__ == "__main__":
    unittest.main()
