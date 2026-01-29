"""Web-scraper venue details."""

from __future__ import annotations

from datetime import date  # noqa: TC003   # pydantic
from functools import total_ordering

from pydantic.dataclasses import dataclass

from utpd_models_web.injector import eq_by, hash_by, lt_by
from utpd_models_web.other import Location  # noqa: TC001  # pydantic


@total_ordering
@dataclass(frozen=True)
class WebUserHistoryVenue:
    """User's recent venue."""

    venue_id: int
    name: str
    url: str
    category: str
    address: str
    is_verified: bool
    first_visit: date | None
    last_visit: date
    num_checkins: int
    first_checkin_id: int | None
    last_checkin_id: int

    __eq__ = eq_by("venue_id")
    __lt__ = lt_by("venue_id")
    __hash__ = hash_by("venue_id")  # pyright: ignore[reportAssignmentType]


@dataclass(frozen=True)
class WebVenueDetails:
    """A venue web page."""

    venue_id: int
    name: str
    is_verified: bool
    venue_slug: str
    categories: set[str]
    address: str
    location: Location | None
    url: str

    @property
    def activity_url(self) -> str:
        """Return activity page url for this venue.

        For unverified, it's just the main venue page.
        Otherwise there's a 'more activity' link to follow.

        Returns:
            str: venue's activity page url
        """
        return f"{self.url}/activity" if self.is_verified else self.url

    __eq__ = eq_by("venue_id")
    __lt__ = lt_by("venue_id")
    __hash__ = hash_by("venue_id")  # pyright: ignore[reportAssignmentType]
