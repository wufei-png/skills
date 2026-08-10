from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    role: str


@dataclass(frozen=True)
class Document:
    owner_id: str


def can_delete(user: User, document: Document) -> bool:
    return user.role == "admin" or user.id == document.owner_id
