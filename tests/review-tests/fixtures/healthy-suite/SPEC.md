# Username normalization contract

`normalize_username(raw)` accepts only strings and returns their canonical account key.

- Trim leading and trailing whitespace.
- Apply Unicode-aware case folding.
- Reject an empty normalized value.
- Accept at most twelve normalized characters; reject thirteen or more.
- Reject non-string input with `TypeError`.

No persistence, uniqueness, locale-specific, or performance behavior belongs to this function.
