"""Reglas del semáforo expresado en TON, incluidos productos PL."""
from datetime import date, timedelta
from decimal import Decimal
import pytest
from src.report import age_band, build_daily_summary, day_bounds_utc, rounded_tonnes

@pytest.mark.parametrize('days,band',[(0,'verde'),(10,'verde'),(11,'amarillo'),(15,'amarillo'),(16,'naranja'),(20,'naranja'),(21,'rojo'),(45,'rojo'),(-1,'inconsistente')])
def test_age_band(days,band):
    d=date(2026,10,8)
    assert age_band(d-timedelta(days=days),d)==band


def test_mixed_products_and_tonnages():
    d=date(2026,10,8)
    rows=[{'warehouse':'Morales','product':'UNO','production_date':'2026-10-02','tonnes':'1.7000'},
          {'warehouse':'Morales','product':'UNO PL','production_date':'2026-09-21','tonnes':'59.5000'},
          {'warehouse':'Morales 2','product':'ECO','production_date':'2026-09-14','tonnes':'2.2500'}]
    report=build_daily_summary(rows,d)
    assert report['tonnes']==Decimal('63.4500')
    assert report['totals']['verde']==Decimal('1.7000')
    assert report['totals']['naranja']==Decimal('59.5000')
    assert report['totals']['rojo']==Decimal('2.2500')
    assert [x['product'] for x in report['rows']]==['ECO','UNO','UNO PL'] or set(x['product'] for x in report['rows'])=={'ECO','UNO','UNO PL'}


def test_day_bounds_guatemala():
    assert day_bounds_utc(date(2026,10,8))==('2026-10-08T06:00:00+00:00','2026-10-09T06:00:00+00:00')


def test_round_at_end():
    assert rounded_tonnes(Decimal('1.7')+Decimal('1.7'))==3
    assert rounded_tonnes(Decimal('59.5'))==60
