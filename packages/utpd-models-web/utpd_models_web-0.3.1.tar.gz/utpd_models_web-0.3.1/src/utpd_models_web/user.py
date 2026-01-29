"""Web-scraper user details."""

from __future__ import annotations

from dataclasses import field
from datetime import datetime  # noqa: TC003    # Pydantic
from functools import total_ordering

from pydantic.dataclasses import dataclass

from utpd_models_web.injector import eq_by, hash_by, lt_by


@total_ordering
@dataclass(frozen=True)
class WebUserDetails:
    """A user's details from the user's web page."""

    user_id: str
    name: str
    location: str
    url: str
    total_beers: int
    total_uniques: int
    total_badges: int
    total_friends: int

    recent_beers: list[int] = field(default_factory=list)
    recent_venues: list[int] = field(default_factory=list)

    __eq__ = eq_by("user_id")
    __lt__ = lt_by("user_id")
    __hash__ = hash_by("user_id")  # pyright: ignore[reportAssignmentType]


@dataclass(frozen=True)
class WebUserListSummary:
    """Summary information for a user's list."""

    list_id: str
    username: str
    name: str
    description: str
    num_items: int
    updated: datetime | None
    url: str
    is_wishlist: bool

    __eq__ = eq_by("list_id")
    __lt__ = lt_by("list_id")
    __hash__ = hash_by("list_id")  # pyright: ignore[reportAssignmentType]
