"""Agregaciones puras del semáforo diario de CAPTURAS (no saldos de inventario)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.config import PRODUCTS, TIMEZONE, WAREHOUSE_USERS

BUCKETS = ("verde", "amarillo", "naranja", "rojo")


def day_bounds_utc(selected_date: date) -> tuple[str, str]:
    """Filtra por fecha GUATEMALA, no por el día UTC del servidor."""
    tz = ZoneInfo(TIMEZONE)
    start = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz)
    end = datetime.combine(selected_date + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    return start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()



def age_band(production: date, reference: date) -> str:
    """Rojo incluye edades superiores a 30 días; 0 días pertenece a verde."""
    days = (reference - production).days
    if days < 0:
        return "inconsistente"
    if days <= 10:
        return "verde"
    if days <= 15:
        return "amarillo"
    if days <= 20:
        return "naranja"
    return "rojo"


def configured_weights(raw: Any) -> dict[str, Decimal]:
    """Los kg/saco nunca se deducen; deben configurarse explícitamente."""
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValueError("PRODUCT_WEIGHT_KG debe ser una tabla de producto = kg por saco.")
    result: dict[str, Decimal] = {}
    for product, value in raw.items():
        if product not in PRODUCTS:
            raise ValueError(f"Producto inválido en PRODUCT_WEIGHT_KG: {product}")
        try:
            weight = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"Peso inválido para {product}.") from exc
        if not weight.is_finite() or not (0 < weight <= 1000):
            raise ValueError(f"El peso de {product} debe ser positivo (kg por saco).")
        result[str(product)] = weight
    return result


def build_daily_summary(
    records: list[dict[str, Any]],
    reference: date,
    *,
    warehouse: str = "Todas",
    weights_kg: Mapping[str, Decimal] | None = None,
) -> dict[str, Any]:
    """Agrupa CAPTURAS de la fecha seleccionada, prefiltradas en la consulta por created_at.

    No inventa salidas, pedidos, lotes ni existencias. Omite capturas anómalas del total,
    reportándolas para revisión sin convertirlas en inventario verde.
    """
    if warehouse != "Todas" and warehouse not in WAREHOUSE_USERS:
        raise ValueError("Bodega inválida.")
    weights = dict(weights_kg or {})
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    valid: list[dict[str, Any]] = []
    anomalous: list[dict[str, Any]] = []
    for record in records:
        depot = str(record.get("warehouse", ""))
        product = str(record.get("product", ""))
        if warehouse != "Todas" and depot != warehouse:
            continue
        if depot not in WAREHOUSE_USERS or product not in PRODUCTS:
            anomalous.append(record)
            continue
        try:
            production = date.fromisoformat(str(record["production_date"]))
            sacks = int(record["sacks"])
        except (ValueError, KeyError, TypeError):
            anomalous.append(record)
            continue
        if sacks <= 0 or age_band(production, reference) == "inconsistente":
            anomalous.append(record)
            continue
        bucket = age_band(production, reference)
        key = (depot, product)
        if key not in groups:
            groups[key] = {"warehouse": depot, "product": product, "sacks": 0, "entries": 0, "bands": defaultdict(int)}
        groups[key]["sacks"] += sacks
        groups[key]["entries"] += 1
        groups[key]["bands"][bucket] += sacks
        valid.append(record)
    used_products = {str(r["product"]) for r in valid}
    as_tonnes = bool(used_products) and used_products.issubset(weights.keys())

    def quantity(sacks: int, product: str) -> Decimal:
        return Decimal(sacks) * weights[product] / Decimal(1000) if as_tonnes else Decimal(sacks)

    rows: list[dict[str, Any]] = []
    for depot in WAREHOUSE_USERS:
        if warehouse != "Todas" and depot != warehouse:
            continue
        for product in PRODUCTS:
            group = groups.get((depot, product))
            if group is None:
                continue
            rows.append({
                "warehouse": depot,
                "product": product,
                "entries": group["entries"],
                "sacks": group["sacks"],
                "total": quantity(group["sacks"], product),
                **{key: quantity(group["bands"].get(key, 0), product) for key in BUCKETS},
            })
    totals = {key: sum((row[key] for row in rows), Decimal(0)) for key in (*BUCKETS, "total")}
    return {
        "rows": rows,
        "totals": totals,
        "records": valid,
        "anomalous": anomalous,
        "count": len(valid),
        "sacks": sum(int(r["sacks"]) for r in valid),
        "unit": "tn" if as_tonnes else "sacos",
        "weights_missing": tuple(product for product in PRODUCTS if product in used_products and product not in weights),
    }
