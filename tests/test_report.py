"""Semáforo diario: límites, agregación, unidades y horario Guatemala."""
from datetime import date
from decimal import Decimal

import pytest

from src.report import age_band, build_daily_summary, configured_weights, day_bounds_utc


@pytest.mark.parametrize("days,expected", [
    (0,"verde"),(10,"verde"),(11,"amarillo"),(15,"amarillo"),
    (16,"naranja"),(20,"naranja"),(21,"rojo"),(31,"rojo"),(-1,"inconsistente"),
])
def test_bands(days, expected):
    from datetime import timedelta
    base = date(2026,10,8)
    assert age_band(base-timedelta(days=days),base) == expected


def sample(**changes):
    row = {
        "created_at":"2026-10-08T15:00:00Z",
        "warehouse":"Morales", "product":"UNO", "production_date":"2026-09-27",
        "sacks":40, "employee_name":"Oscar Ovidio Molina Montesinos", "is_support":False,
    }
    row.update(changes)
    return row


def test_totals_and_groups_sacks():
    records = [sample(), sample(product="ECO",sacks=80,production_date="2026-10-01"),
               sample(warehouse="Bárcenas",product="UNO",sacks=120,production_date="2026-09-12")]
    result=build_daily_summary(records, date(2026,10,8))
    assert result["unit"] == "sacos"
    assert result["count"] == 3 and result["sacks"] == 240
    assert result["totals"]["total"] == 240
    assert result["totals"]["verde"] == 80
    assert result["totals"]["amarillo"] == 40
    assert result["totals"]["rojo"] == 120
    assert len(result["rows"]) == 3
    assert result["weights_missing"] == ("UNO", "ECO")


def test_tonnes_only_with_confirmed_weights():
    weights=configured_weights({"UNO":42.5,"ECO":50})
    result=build_daily_summary([sample(),sample(product="ECO",sacks=20)],date(2026,10,8),weights_kg=weights)
    assert result["unit"]=="tn"
    assert result["totals"]["total"] == Decimal("2.70")
    assert result["totals"]["amarillo"] == Decimal("2.70")


def test_warehouse_filter_and_invalid_date_excluded():
    records=[sample(),sample(warehouse="Bárcenas"),sample(production_date="2026-10-09")]
    result=build_daily_summary(records,date(2026,10,8),warehouse="Morales")
    assert result["sacks"]==40
    assert result["count"]==1
    assert len(result["anomalous"])==1


def test_weights_validation():
    with pytest.raises(ValueError):
        configured_weights({"UNO":-42.5})
    with pytest.raises(ValueError):
        configured_weights({"GU":"no-numero"})
    with pytest.raises(ValueError):
        configured_weights({"ABC":42})


def test_guatemala_day_window_not_utc_midnight():
    start,end=day_bounds_utc(date(2026,10,8))
    assert start == "2026-10-08T06:00:00+00:00"
    assert end == "2026-10-09T06:00:00+00:00"


def test_pl_products_appear_separately_in_supervisor_summary():
    records = [
        sample(product="UNO", sacks=40),
        sample(product="UNO PL", sacks=80),
        sample(product="ECO PL", sacks=120),
        sample(product="GU PL", sacks=20),
    ]
    result = build_daily_summary(records, date(2026, 10, 8))
    by_product = {row["product"]: row for row in result["rows"]}
    assert set(by_product) == {"UNO", "UNO PL", "ECO PL", "GU PL"}
    assert by_product["UNO"]["sacks"] == 40
    assert by_product["UNO PL"]["sacks"] == 80
    assert by_product["ECO PL"]["sacks"] == 120
    assert by_product["GU PL"]["sacks"] == 20
    assert result["sacks"] == 260
    assert result["weights_missing"] == ("UNO", "ECO PL", "UNO PL", "GU PL")
