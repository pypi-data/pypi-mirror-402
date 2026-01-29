"""Web-scraper menu details."""

from __future__ import annotations

from functools import total_ordering

from pydantic import Field
from pydantic.dataclasses import dataclass

from utpd_models_web.beer import WebVenueMenuBeer  # noqa: TC001 # pydantic
from utpd_models_web.injector import eq_by, hash_by, lt_by


@total_ordering
@dataclass(frozen=True)
class WebVenueMenu:
    """Verified venue's menu page(s)."""

    menu_id: int
    selection: str
    name: str
    description: str
    beers: set[WebVenueMenuBeer] = Field(default_factory=set)

    @property
    def full_name(self) -> str:
        """Concatenate menu selector with name to ensure a unique name.

        Returns:
            str: full menu name
        """
        return f"{self.selection} / {self.name}"

    __eq__ = eq_by("menu_id")
    __lt__ = lt_by("menu_id")
    __hash__ = hash_by("menu_id")  # pyright: ignore[reportAssignmentType]
