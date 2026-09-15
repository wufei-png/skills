def active_accounts(accounts: list[dict[str, bool]]) -> int:
    # This loops over every account and adds one to the result when it is active.
    return sum(1 for account in accounts if account["active"])
