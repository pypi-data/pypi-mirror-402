"""Inject common methods into classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable


def eq_by(field: str) -> Callable[[object, object], bool]:
    """Inject methods into a class to only consider the field for equality."""

    def method(self: object, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return getattr(self, field) == getattr(other, field)

    return method


def lt_by(field: str) -> Callable[[object, object], bool]:
    """Inject methods into a class to only consider the field for ordering."""

    def method(self: object, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return getattr(self, field) < getattr(other, field)

    return method


def hash_by(field: str) -> Callable[[object], int]:
    """Return a __hash__ method that hashes by the given field."""

    def __hash__(self: object) -> int:  # noqa: N807
        return hash(getattr(self, field))

    return __hash__


# class IdEq[T]:
#     """Identity-based equality, ordering, and hashing, based on a single attribute."""

#     def __init__(self, field: str) -> None:
#         """Initialize the IdEq class with the field name."""
#         self.field = field

#     def eq(self, self_: T, other: object) -> bool:
#         """Compare two objects for equality based on the specified field."""
#         if not isinstance(other, type(self_)):
#             return NotImplemented
#         return getattr(self_, self.field) == getattr(other, self.field)

#     def lt(self, self_: T, other: object) -> bool:
#         """Compare two objects for ordering based on the specified field."""
#         if not isinstance(other, type(self_)):
#             return NotImplemented
#         return getattr(self_, self.field) < getattr(other, self.field)

#     def hash(
#         slf,  # pyright: ignore[reportSelfClsParameterName]   # Pylance needs hash to be passed "self"
#         self: T,
#     ) -> int:
#         """Return a hash value based on the specified field."""
#         return hash(getattr(self, slf.field))
