"""Tests for beer structs."""

from __future__ import annotations

from datetime import datetime

import pytest
from utpd_models_web.beer import WebBeerDetails
from utpd_models_web.checkin import WebActivityBeer


@pytest.fixture
def beer1() -> WebBeerDetails:
    """Fake beer object."""
    return WebBeerDetails(
        beer_id=123,
        beer_name="Test Beer",
        beer_description="A test beer.",
        beer_label_url="https://example.com/beer/123.jpg",
        brewery_name="Test Brewery",
        brewery_url="test-brewery",
        style="IPA",
        url="https://example.com/beer/123",
        num_ratings=100,
        global_rating=4.5,
    )


@pytest.fixture
def beer2() -> WebBeerDetails:
    """Fake beer object with same beer ID."""
    return WebBeerDetails(
        beer_id=123,
        beer_name="Another Test Beer",
        beer_description="Another test beer.",
        beer_label_url="https://example.com/beer/123b.jpg",
        brewery_name="Test Brewery2",
        brewery_url="test-brewery2",
        style="DIPA",
        url="https://example.com/beer/123b",
        num_ratings=200,
        global_rating=4.7,
    )


@pytest.fixture
def beer3() -> WebBeerDetails:
    """Totally different beer object."""
    return WebBeerDetails(
        beer_id=456,
        beer_name="Another Beer",
        beer_description="A different beer.",
        beer_label_url="https://example.com/beer/456.jpg",
        brewery_name="Another Brewery",
        brewery_url="another-brewery",
        style="Stout",
        url="https://example.com/beer/456",
        num_ratings=50,
        global_rating=4.0,
    )


@pytest.mark.parametrize(
    "b1_name, b2_name, expected",
    [
        ("beer1", "beer1", True),
        ("beer1", "beer2", True),
        ("beer1", "beer3", False),
        ("beer2", "beer3", False),
        ("beer3", "beer3", True),
    ],
)
def test_beer_eq(
    b1_name: str, b2_name: str, expected: bool, request: pytest.FixtureRequest
) -> None:
    """Test equality of two beer objects."""
    b1: WebBeerDetails = request.getfixturevalue(b1_name)
    b2: WebBeerDetails = request.getfixturevalue(b2_name)

    result = b1 == b2

    assert result is expected


@pytest.mark.parametrize(
    "b1_name, b2_name, expected",
    [
        ("beer1", "beer1", False),
        ("beer1", "beer2", False),
        ("beer3", "beer1", True),
        ("beer2", "beer3", False),
        ("beer3", "beer3", False),
    ],
)
def test_beer_gt(
    b1_name: str, b2_name: str, expected: bool, request: pytest.FixtureRequest
) -> None:
    """Test equality of two beer objects."""
    b1: WebBeerDetails = request.getfixturevalue(b1_name)
    b2: WebBeerDetails = request.getfixturevalue(b2_name)

    result = b1 > b2

    assert result is expected


def test_activity_gt() -> None:
    """Test equality of two beer objects."""
    b1 = WebActivityBeer(
        checkin_id=123,
        checkin=datetime.fromisoformat("2023-10-01T12:00:00Z"),
        user_name="Test User",
        beer_name="Test Beer",
        beer_id=123,
        beer_label_url="https://example.com/beer/123.jpg",
        brewery_id=456,
        brewery_name="Test Brewery",
        brewery_url="test-brewery",
    )
    b2 = WebActivityBeer(
        checkin_id=124,
        checkin=datetime.fromisoformat("2023-10-01T12:00:00Z"),
        user_name="Test User",
        beer_name="Test Beer",
        beer_id=123,
        beer_label_url="https://example.com/beer/123.jpg",
        brewery_id=456,
        brewery_name="Test Brewery",
        brewery_url="test-brewery",
    )

    result = b2 > b1

    assert result
