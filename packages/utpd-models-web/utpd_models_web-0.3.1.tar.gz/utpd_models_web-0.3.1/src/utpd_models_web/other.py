"""Structures used to represent data not scraped."""

from __future__ import annotations

from dataclasses import astuple, dataclass
from functools import lru_cache

from haversine import haversine as haversine_orig


@dataclass(frozen=True)
class Location:
    """Store latitude and longiture and calculate haversine distance between them."""

    lat: float
    lng: float

    def distance_from(self, other: Location) -> float:
        """Return km between two Location objects.

        Args:
            other (Location): where to measure distance to

        Returns:
            float: distance between points in km
        """
        return haversine(astuple(self), astuple(other))


@lru_cache
def haversine(coords1: tuple[float, float], coords2: tuple[float, float]) -> float:
    """Wrap the haversine function for caching."""
    return haversine_orig(coords1, coords2)
