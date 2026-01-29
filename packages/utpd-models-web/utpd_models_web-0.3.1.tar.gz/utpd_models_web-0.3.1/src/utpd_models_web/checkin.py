"""Web-scraper checkin details."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003    # pydantic
from functools import total_ordering

from pydantic.dataclasses import dataclass

from utpd_models_web.injector import eq_by, hash_by, lt_by


@total_ordering
@dataclass(frozen=True)
class WebActivityBeer:
    """A checkin from a user or venue activity feed."""

    checkin_id: int
    checkin: datetime
    user_name: str
    beer_name: str
    beer_id: int
    beer_label_url: str
    brewery_id: int | None
    brewery_name: str
    brewery_url: str
    location: str | None = None
    location_id: int | None = None
    purchased_at: str | None = None
    purchased_id: int | None = None
    comment: str | None = None
    serving: str | None = None
    user_rating: float | None = None
    friends: list[str] | None = None

    def __str__(self) -> str:
        """Create a summary description of a beer.

        Returns:
            str: beer description
        """
        summary = (
            f"{self.checkin.astimezone().strftime('%a %H:%M')}: {self.user_name} - "
            f"{self.beer_name} by {self.brewery_name}"
        )
        if self.location:
            summary += f" at {self.location}"
        if self.serving:
            summary += f" ({self.serving})"
        if self.user_rating:
            summary += f", user rating {self.user_rating}"
        if self.friends:
            friends = ", ".join(self.friends)
            summary += f" with {friends}"
        return summary

    __eq__ = eq_by("checkin_id")
    __lt__ = lt_by("checkin_id")
    __hash__ = hash_by("checkin_id")  # pyright: ignore[reportAssignmentType]
