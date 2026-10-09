"""Sin red: verifica mapeo Odoo y semáforo real con objetos simulados."""
from datetime import date
from decimal import Decimal

from src.odoo_integration import build_odoo_snapshot, combine_report, rounded_odoo_tonnes
from src.report import build_daily_summary


def test_live_sample_of_all_three_warehouses():
    # Reproduce el número de operaciones y toneladas del diagnóstico real.
    pickings = []
    moves = []
    products = [
        {"id": 9, "default_code": "10004"},
        {"id": 10, "default_code": "10002"},
    ]
    counts = [("Morales", 3, 13, 12, 7613, 6636),
              ("Morales 2", 36, 3, 3, 1280, 1920),
              ("Bárcenas", 19, 3, 5, 1070, 1770)]
    pid = 1
    for _, operation, eco_n, uno_n, eco_sacks, uno_sacks in counts:
        for product_id, number, sacks in ((10, eco_n, eco_sacks), (9, uno_n, uno_sacks)):
            # Reparto determinista de sacos entre operaciones del mismo producto.
            for i in range(number):
                pickings.append({"id": pid, "picking_type_id": [operation, "Recolectar"]})
                demand = sacks // number + (1 if i < sacks % number else 0)
                moves.append({"picking_id": [pid,"op"], "product_id": [product_id,"p"],
                              "product_uom": [1,"Sacos"], "product_uom_qty": demand, "state": "assigned"})
                pid += 1
    snapshot = build_odoo_snapshot(pickings, moves, products)
    assert snapshot["unique_total"] == 39
    assert snapshot["unique_by_warehouse"] == {"Morales":25, "Morales 2":6, "Bárcenas":8}
    assert snapshot["rows"][("Morales","ECO")]["orders"] == 13
    assert snapshot["rows"][("Morales","UNO")]["orders"] == 12
    assert snapshot["rows"][("Morales","ECO")]["tonnes"] == Decimal("323.5525")
    assert snapshot["rows"][("Bárcenas","UNO")]["tonnes"] == Decimal("75.225")
    assert sum((v["tonnes"] for v in snapshot["rows"].values()),Decimal(0)) == Decimal("862.2825")
    assert rounded_odoo_tonnes(Decimal("862.2825")) == "862"


def test_one_picking_two_products_counts_once_in_warehouse_total():
    pickings=[{"id":1,"picking_type_id":[19,"PICK"]}]
    moves=[
        {"picking_id":[1,"PICK"],"product_id":[9,"ECO"],"product_uom":[4,"Sacos"],"product_uom_qty":40},
        {"picking_id":[1,"PICK"],"product_id":[10,"UNO"],"product_uom":[4,"Sacos"],"product_uom_qty":60},
        {"picking_id":[1,"PICK"],"product_id":[10,"UNO"],"product_uom":[4,"Sacos"],"product_uom_qty":20},
    ]
    products=[{"id":9,"default_code":"10002"},{"id":10,"default_code":"10004"}]
    snapshot=build_odoo_snapshot(pickings,moves,products)
    assert snapshot["unique_total"] == 1
    assert snapshot["rows"][("Bárcenas","UNO")]["orders"] == 1
    assert snapshot["rows"][("Bárcenas","ECO")]["orders"] == 1
    assert snapshot["rows"][("Bárcenas","UNO")]["tonnes"] == Decimal("3.400")


def test_unknown_sku_or_unit_does_not_become_42_5kg():
    pickings=[{"id":42,"picking_type_id":[36,"PICK"]}]
    moves=[{"picking_id":[42,""],"product_id":[22,""],"product_uom":[2,"Toneladas"],"product_uom_qty":12}]
    snapshot=build_odoo_snapshot(pickings,moves,[{"id":22,"default_code":"10004"}])
    assert snapshot["unique_by_warehouse"]["Morales 2"] == 1
    assert not snapshot["rows"]
    assert snapshot["unmapped"]


def test_supabase_zero_rows_still_displays_live_odoo():
    base=build_daily_summary([],date(2026,10,8))
    snap={"rows":{("Morales","UNO"):{"orders":7,"tonnes":Decimal("10.1")}},
          "unique_by_warehouse":{"Morales":7,"Morales 2":0,"Bárcenas":0},
          "unmapped":[],"as_of":"08/10/2026 20:00:00"}
    report=combine_report(base,snap)
    assert len(report["rows"])==1
    assert report["rows"][0]["sacks"] == 0
    assert report["rows"][0]["odoo_orders"] == 7
    assert report["odoo_unique_total"] == 7
    assert rounded_odoo_tonnes(report["odoo_tonnes_total"]) == "10"


def test_error_not_misrepresented_as_zero_orders():
    report=build_daily_summary([{"warehouse":"Bárcenas","product":"UNO","production_date":"2026-10-08","sacks":40}],date(2026,10,8))
    with_error=combine_report(report,None)
    assert with_error["rows"][0]["odoo_orders"] is None
    assert with_error["rows"][0]["odoo_tonnes"] is None
    assert with_error["odoo_unique_total"] is None


def test_selected_warehouse_uses_only_its_unique_operations():
    base=build_daily_summary([],date(2026,10,8),warehouse="Bárcenas")
    snap={"rows":{("Morales","UNO"):{"orders":12,"tonnes":Decimal(9)},
                 ("Bárcenas","ECO"):{"orders":3,"tonnes":Decimal(5)}},
          "unique_by_warehouse":{"Morales":12,"Morales 2":0,"Bárcenas":3},
          "unmapped":[],"as_of":"08/10/2026 20:00:00"}
    report=combine_report(base,snap,warehouse="Bárcenas")
    assert [(r["warehouse"],r["product"]) for r in report["rows"]] == [("Bárcenas","ECO")]
    assert report["odoo_unique_total"] == 3


def test_rounding_done_after_summing_decimal_tonnes():
    a=Decimal("45.475")
    b=Decimal("75.225")
    assert rounded_odoo_tonnes(a) == "45"
    assert rounded_odoo_tonnes(b) == "75"
    assert rounded_odoo_tonnes(a+b) == "121"
