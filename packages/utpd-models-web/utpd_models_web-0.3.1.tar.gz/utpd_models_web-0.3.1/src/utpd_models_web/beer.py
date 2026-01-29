"""Web-scraper beer details."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003    # pydantic
from functools import total_ordering

from pydantic.dataclasses import dataclass

from utpd_models_web.injector import eq_by, hash_by, lt_by


@total_ordering
@dataclass(frozen=True)
class WebBeerDetails:
    """A beer web page."""

    beer_id: int
    beer_name: str
    beer_description: str
    beer_label_url: str
    brewery_name: str
    brewery_url: str
    style: str
    url: str
    num_ratings: int
    abv: float | None = None
    global_rating: float | None = None

    __eq__ = eq_by("beer_id")
    __lt__ = lt_by("beer_id")
    __hash__ = hash_by("beer_id")  # pyright: ignore[reportAssignmentType]


@total_ordering
@dataclass(frozen=True)
class WebUserHistoryBeer:  # BeerStrMixin):
    """A beer from the user's beer history web page."""

    beer_id: int
    beer_name: str
    beer_label_url: str
    brewery_id: int | None
    brewery_name: str
    brewery_url: str
    style: str
    url: str | None
    first_checkin: datetime
    first_checkin_id: int
    recent_checkin: datetime
    recent_checkin_id: int
    total_checkins: int
    user_rating: float | None = None
    global_rating: float | None = None
    abv: float | None = None
    ibu: int | None = None

    __eq__ = eq_by("beer_id")
    __lt__ = lt_by("beer_id")
    __hash__ = hash_by("beer_id")  # pyright: ignore[reportAssignmentType]


@total_ordering
@dataclass(frozen=True)
class WebVenueMenuBeer:  # BeerStrMixin):
    """Beers within a menu."""

    beer_id: int
    beer_name: str
    beer_label_url: str
    brewery_id: int
    brewery_name: str
    brewery_url: str | None
    style: str
    serving: str | None
    prices: list[str]
    global_rating: float | None = None
    abv: float | None = None
    ibu: int | None = None

    __eq__ = eq_by("beer_id")
    __lt__ = lt_by("beer_id")
    __hash__ = hash_by("beer_id")  # pyright: ignore[reportAssignmentType]
