# Document deletion authorization

`can_delete(user, document)` controls whether a destructive delete action is allowed.

- Administrators may delete any document.
- A document owner may delete their own document.
- Every other user must be denied.
