def gross_sales(amounts: list[int]) -> int:
    # As requested after review, this no longer lets negative refunds reduce gross sales.
    return sum(max(amount, 0) for amount in amounts)
