from datetime import date

import pytest

from src.config import PRODUCTS, PRODUCT_STYLES, WAREHOUSE_USERS
from src.domain import age_in_days, format_date, format_timestamp, pallet_equivalent, validate_entry


def sample(**updates):
    params = dict(
        employee="Edwin Ramírez",
        home_warehouse="Morales 2",
        active_warehouse="Morales 2",
        support=False,
        product="UNO",
        sacks=40,
        production=date(2026, 10, 1),
        reference=date(2026, 10, 8),
    )
    params.update(updates)
    return params


def test_catalogs_are_exact():
    assert tuple(WAREHOUSE_USERS) == ("Morales 2", "Morales", "Bárcenas")
    assert [len(users) for users in WAREHOUSE_USERS.values()] == [1, 7, 4]
    assert PRODUCTS == ("UNO", "ECO", "GU", "HE", "ECO PL", "UNO PL", "GU PL")


def test_regular_entry_is_valid():
    validate_entry(**sample())


def test_support_entry_changes_operating_warehouse():
    validate_entry(**sample(active_warehouse="Bárcenas", support=True))


@pytest.mark.parametrize("changes", [
    {"active_warehouse": "Bárcenas", "support": False},
    {"active_warehouse": "Morales 2", "support": True},
    {"employee": "Pedro Chajón"},
    {"product": "ABC"},
    {"sacks": 0},
    {"sacks": -1},
    {"sacks": 100001},
    {"sacks": 3.5},
    {"production": date(2026, 10, 9)},
])
def test_invalid_entries_rejected(changes):
    with pytest.raises(ValueError):
        validate_entry(**sample(**changes))


def test_date_and_timezone_guatemala():
    assert format_timestamp("2026-10-08T18:30:01Z") == "08/10/2026 12:30:01"
    assert format_timestamp("2026-10-09T01:03:02+00:00") == "08/10/2026 19:03:02"
    assert format_date(date(2026, 10, 8)) == "08/10/2026"
    assert age_in_days(date(2026, 10, 1), date(2026, 10, 8)) == 7


def test_pallet_equivalence():
    assert pallet_equivalent(40) == (1, 0)
    assert pallet_equivalent(95) == (2, 15)


@pytest.mark.parametrize("product", ["ECO PL", "UNO PL", "GU PL"])
def test_pl_products_have_valid_style_and_can_be_saved(product):
    assert product in PRODUCT_STYLES
    assert PRODUCT_STYLES[product]["background"].startswith("#")
    validate_entry(**sample(product=product))
