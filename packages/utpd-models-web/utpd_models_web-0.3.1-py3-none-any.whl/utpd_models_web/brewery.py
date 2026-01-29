"""Web-scraper brewery details."""

from __future__ import annotations

from functools import total_ordering

from pydantic.dataclasses import dataclass

from utpd_models_web.injector import eq_by, hash_by, lt_by


@total_ordering
@dataclass(frozen=True)
class WebBreweryDetails:
    """A brewery web page."""

    brewery_id: int
    name: str
    brewery_url: str
    style: str
    description: str
    num_beers: int
    rating: float | None
    address: str

    __eq__ = eq_by("brewery_id")
    __lt__ = lt_by("brewery_id")
    __hash__ = hash_by("brewery_id")  # pyright: ignore[reportAssignmentType]
