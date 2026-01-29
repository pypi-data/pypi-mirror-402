"""Untapdd scraping constants."""

from __future__ import annotations

import os
from typing import Final

UNTAPPD_BASE_URL: Final = (
    os.getenv("UNTAPPD_BASE_URL", "https://untappd.com/").rstrip("/") + "/"
)


# ----- Number of entries to expect on a page -----

UNTAPPD_BEER_HISTORY_SIZE: Final = 25
UNTAPPD_BREWERY_HISTORY_SIZE: Final = 20
UNTAPPD_VENUE_ACTIVITY_SIZE: Final = 20
UNTAPPD_VENUE_HISTORY_SIZE: Final = 25
