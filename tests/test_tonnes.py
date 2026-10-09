from datetime import date, timedelta
from decimal import Decimal
import pytest
from src.config import WAREHOUSE_SUPERVISORS, PRODUCTS
from src.domain import validate_tonnes_entry
from src.report import build_daily_summary, record_tonnes, rounded_tonnes, day_bounds_utc, age_band
from src.odoo_integration import combine_report

DAY = date(2026,10,8)


def row(**kwargs):
    data = {"warehouse":"Morales 2", "product":"UNO", "production_date":"2026-10-01",
            "tonnes":"1.7000", "employee_name":"Edwin Ramírez", "created_at":"2026-10-08T12:00:00+00:00"}
    data.update(kwargs)
    return data


def test_historical_migration_math_and_precision():
    assert record_tonnes(row(tonnes=None,sacks=1400)) == Decimal('59.5000')
    assert record_tonnes(row(tonnes='59.5000', sacks=1400)) == Decimal('59.5000')
    assert record_tonnes(row(tonnes='2.3456')) == Decimal('2.3456')
    assert rounded_tonnes(Decimal('1.7')) == 2
    assert rounded_tonnes(Decimal('0.0425')) == 0  # UI redondea, base conserva precisión


def test_summary_by_ton_and_bands():
    data = [row(),row(tonnes='0.3000', production_date='2026-09-23'),
            row(product='ECO PL',tonnes='10.1250',production_date='2026-09-18'),
            row(warehouse='Morales',tonnes='2.0000',production_date='2026-09-15')]
    r=build_daily_summary(data,DAY)
    assert r['tonnes']==Decimal('14.1250')
    assert r['totals']['verde']==Decimal('1.7000')
    assert r['totals']['naranja']==Decimal('10.1250')
    assert r['totals']['amarillo']==Decimal('0.3000')
    assert r['totals']['rojo']==Decimal('2.0000')
    assert len(r['rows'])==3


def test_invalid_record_excluded():
    r=build_daily_summary([row(),row(tonnes='NaN'),row(production_date='2026-10-09')],DAY)
    assert r['count']==1 and len(r['anomalous'])==2


def test_supervisor_names_match_home_warehouses():
    assert WAREHOUSE_SUPERVISORS=={
        'Edwin Ramírez':'Morales 2',
        'Jefrie Anthony Sandoval Estrada':'Morales',
        'Pedro Chajón':'Bárcenas'
    }
    assert len(PRODUCTS)==7


def entry(**updates):
    vals=dict(employee='Edwin Ramírez',home_warehouse='Morales 2',active_warehouse='Morales 2',
              support=False,product='UNO PL',tonnes=Decimal('59.5000'),production=DAY,reference=DAY)
    vals.update(updates)
    return vals


def test_valid_tonnes_entry_and_manager():
    assert validate_tonnes_entry(**entry())==Decimal('59.5000')
    data=entry(employee='Rudy Anavisca',home_warehouse='Morales',active_warehouse='Morales',manager=True)
    assert validate_tonnes_entry(**data)==Decimal('59.5000')


@pytest.mark.parametrize('updates',[
    {'tonnes':Decimal('0')},{'tonnes':Decimal('-1')},{'tonnes':Decimal('NaN')},
    {'tonnes':Decimal('1.00001')},{'product':'XYZ'}, {'employee':'Pedro Chajón'},
    {'production':DAY + timedelta(days=1)},
    {'active_warehouse':'Morales','support':False},
    {'employee':'Jefrie Anthony Sandoval Estrada','manager':True},
])
def test_invalid_tonnes_entry(updates):
    with pytest.raises(ValueError):
        validate_tonnes_entry(**entry(**updates))


def test_odoo_row_can_exist_without_supabase_capture():
    base=build_daily_summary([],DAY)
    snapshot={"rows":{('Morales','UNO'):{'orders':3,'tonnes':Decimal('3.4')}},
              'unique_by_warehouse':{'Morales':3,'Morales 2':0,'Bárcenas':0},
              'unmapped':[], 'as_of':'08/10/2026 18:00:00'}
    summary=combine_report(base,snapshot)
    assert summary['rows'][0]['tonnes']==0
    assert summary['rows'][0]['odoo_orders']==3
    assert summary['odoo_unique_total']==3


def test_local_day():
    assert day_bounds_utc(DAY)==('2026-10-08T06:00:00+00:00','2026-10-09T06:00:00+00:00')
    assert age_band(DAY - timedelta(days=21),DAY)=='rojo'
