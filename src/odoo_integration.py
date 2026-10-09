"""Consulta Odoo 17 en solo lectura para operaciones PICK actualmente en estado Listo.

No usa fechas: el semáforo de capturas sí se filtra por día, Odoo muestra
el estado operativo actual. No se incluyen clientes ni documentos de origen.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from urllib.parse import urlsplit
import xmlrpc.client
from zoneinfo import ZoneInfo

from src.config import PRODUCTS, TIMEZONE, WAREHOUSE_USERS
from src.report import rounded_tonnes

PICK_TYPES = {"Morales": 3, "Morales 2": 36, "Bárcenas": 19}
SACK_SKUS = {"10002": ("ECO", Decimal("42.5")), "10004": ("UNO", Decimal("42.5"))}
BATCH = 100


class _TimedHttpsTransport(xmlrpc.client.SafeTransport):
    """Limita la espera por petición sin alterar socket.timeout global."""

    def make_connection(self, host):
        connection = super().make_connection(host)
        connection.timeout = 18
        return connection


def _get_id(value):
    if isinstance(value, (list, tuple)):
        return int(value[0]) if value else None
    return int(value) if value else None


def _get_name(value) -> str:
    return str(value[1]) if isinstance(value, (list, tuple)) and len(value) > 1 else ""


def _batches(items: list[int], size: int = BATCH):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _rpc_read(api, database, uid, key, model, ids, fields):
    output = []
    for batch in _batches(ids):
        output.extend(api.execute_kw(database, uid, key, model, "read", [batch], {"fields": fields}))
    return output


def _map_row(product: dict, move: dict) -> tuple[str | None, Decimal | None, str]:
    """Admite exclusivamente SKUs y unidad validados en el diagnóstico real."""
    sku = str(product.get("default_code") or "").strip()
    unit = _get_name(move.get("product_uom"))
    if sku not in SACK_SKUS or unit.casefold().strip() not in {"saco", "sacos"}:
        return None, None, sku
    product_name, weight = SACK_SKUS[sku]
    return product_name, weight, sku


def build_odoo_snapshot(pickings: list[dict], moves: list[dict], products: list[dict]):
    """Agrega por (bodega, producto) con conjunto de operaciones PICK únicas."""
    product_lookup = {int(p["id"]): p for p in products}
    pick_type = {int(p["id"]): _get_id(p.get("picking_type_id")) for p in pickings}
    warehouse_for_id = {
        picking_id: wh
        for picking_id, typ in pick_type.items()
        for wh, wh_type in PICK_TYPES.items() if typ == wh_type
    }
    unique_by_warehouse = {warehouse: set() for warehouse in WAREHOUSE_USERS}
    for pid, wh in warehouse_for_id.items():
        unique_by_warehouse[wh].add(pid)

    by_product = defaultdict(lambda: {"picking_ids": set(), "tonnes": Decimal("0")})
    unmapped = set()
    for move in moves:
        pid = _get_id(move.get("picking_id"))
        wh = warehouse_for_id.get(pid)
        if not wh or move.get("state") == "cancel":
            continue
        product_data = product_lookup.get(_get_id(move.get("product_id")), {})
        prod, weight, sku = _map_row(product_data, move)
        if prod is None:
            unmapped.add((wh, sku or "SKU no informado", _get_name(move.get("product_uom")) or "Unidad desconocida"))
            continue
        try:
            demand = Decimal(str(move.get("product_uom_qty") or 0))
        except (TypeError, ValueError, ArithmeticError):
            unmapped.add((wh, sku, "Demanda no numérica"))
            continue
        if not demand.is_finite() or demand < 0:
            unmapped.add((wh, sku, "Demanda inválida"))
            continue
        row = by_product[(wh, prod)]
        row["picking_ids"].add(pid)
        row["tonnes"] += demand * weight / Decimal("1000")

    rows = {
        key: {"orders": len(value["picking_ids"]), "tonnes": value["tonnes"]}
        for key, value in by_product.items()
    }
    return {
        "rows": rows,
        "unique_by_warehouse": {wh: len(ids) for wh, ids in unique_by_warehouse.items()},
        "unique_total": sum(len(ids) for ids in unique_by_warehouse.values()),
        "unmapped": sorted(unmapped),
    }


def fetch_live_odoo(url: str, database: str, username: str, api_key: str):
    """Una conexión efímera, sin escribir en Odoo ni registrar secretos."""
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("ODOO_URL debe ser una URL HTTPS sin usuario, parámetros ni fragmentos.")
    root = url.rstrip("/")
    common = xmlrpc.client.ServerProxy(root + "/xmlrpc/2/common", allow_none=True, transport=_TimedHttpsTransport())
    uid = common.authenticate(database, username, api_key, {})
    if not uid:
        raise RuntimeError("Odoo rechazó las credenciales configuradas.")
    api = xmlrpc.client.ServerProxy(root + "/xmlrpc/2/object", allow_none=True, transport=_TimedHttpsTransport())
    ids = api.execute_kw(database, uid, api_key, "stock.picking", "search", [[
        ("picking_type_id", "in", list(PICK_TYPES.values())), ("state", "=", "assigned")
    ]], {"order": "id asc"})
    pickings = _rpc_read(api, database, uid, api_key, "stock.picking", ids, ["id", "picking_type_id", "move_ids"])
    move_ids = sorted({int(mid) for pick in pickings for mid in (pick.get("move_ids") or [])})
    moves = _rpc_read(api, database, uid, api_key, "stock.move", move_ids,
                      ["id", "picking_id", "product_id", "product_uom_qty", "product_uom", "state"])
    prod_ids = sorted({_get_id(move.get("product_id")) for move in moves if _get_id(move.get("product_id")) is not None})
    products = _rpc_read(api, database, uid, api_key, "product.product", prod_ids, ["id", "default_code"])
    snapshot = build_odoo_snapshot(pickings, moves, products)
    snapshot["as_of"] = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M:%S")
    return snapshot


def combine_report(report: dict, snapshot: dict | None, warehouse: str = "Todas") -> dict:
    """Une capturas del día con pedidos actuales: no inventa ceros si Odoo falla."""
    output = dict(report)
    existing = {(str(r["warehouse"]), str(r["product"])): dict(r) for r in report["rows"]}
    if snapshot is not None:
        for wh, product in snapshot["rows"]:
            if wh not in WAREHOUSE_USERS or product not in PRODUCTS or (warehouse != "Todas" and warehouse != wh):
                continue
            if (wh, product) not in existing:
                existing[(wh, product)] = {
                    "warehouse": wh, "product": product, "entries": 0, "sacks": 0,
                    **{band: Decimal("0") for band in ("verde", "amarillo", "naranja", "rojo")},
                }
    rows = []
    for wh in WAREHOUSE_USERS:
        if warehouse != "Todas" and warehouse != wh:
            continue
        for product in PRODUCTS:
            row = existing.get((wh, product))
            if row is None:
                continue
            live = snapshot["rows"].get((wh, product)) if snapshot is not None else None
            row["odoo_orders"] = int(live["orders"]) if live is not None else (0 if snapshot is not None else None)
            row["odoo_tonnes"] = Decimal(live["tonnes"]) if live is not None else (Decimal("0") if snapshot is not None else None)
            rows.append(row)
    output["rows"] = rows
    output["odoo_ok"] = snapshot is not None
    output["odoo_as_of"] = snapshot.get("as_of") if snapshot else None
    output["odoo_unique_by_warehouse"] = (
        {wh: int(snapshot["unique_by_warehouse"].get(wh, 0)) for wh in WAREHOUSE_USERS}
        if snapshot is not None else None
    )
    output["odoo_unique_total"] = (
        sum(int(snapshot["unique_by_warehouse"].get(wh, 0)) for wh in WAREHOUSE_USERS if warehouse in ("Todas", wh))
        if snapshot is not None else None
    )
    output["odoo_tonnes_total"] = (
        sum((row["odoo_tonnes"] for row in rows), Decimal("0")) if snapshot is not None else None
    )
    output["odoo_unmapped"] = snapshot["unmapped"] if snapshot else []
    return output


def product_totals(rows: list[dict]):
    """Pedidos POR PRODUCTO no son una métrica aditiva entre SKUs."""
    if not rows or rows[0].get("odoo_orders") is None:
        return None, None
    return sum(int(r["odoo_orders"]) for r in rows), sum((r["odoo_tonnes"] for r in rows), Decimal("0"))


def rounded_odoo_tonnes(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)):,}"
