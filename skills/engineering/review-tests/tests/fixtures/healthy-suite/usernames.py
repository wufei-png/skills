def normalize_username(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError("username must be a string")

    normalized = raw.strip().casefold()
    if not normalized:
        raise ValueError("username must not be empty")
    if len(normalized) > 12:
        raise ValueError("username must contain at most 12 characters")
    return normalized
