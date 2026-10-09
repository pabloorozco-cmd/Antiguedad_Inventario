"""Informe diario por bodega y producto, expresado exclusivamente en toneladas.

Los registros antiguos en sacos se migran a tonnes = sacks * 0.0425 en Supabase.
El reporte NO expresa existencias netas, únicamente capturas físicas del día.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

from src.config import PRODUCTS, TIMEZONE, WAREHOUSE_USERS

BUCKETS = ("verde", "amarillo", "naranja", "rojo")
TONS_PER_SACK = Decimal("0.0425")


def day_bounds_utc(selected_date: date) -> tuple[str, str]:
    tz = ZoneInfo(TIMEZONE)
    start = datetime.combine(selected_date, datetime.min.time(), tzinfo=tz)
    end = datetime.combine(selected_date + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    return start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()


def age_band(production: date, reference: date) -> str:
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


def record_tonnes(record: dict[str, Any]) -> Decimal:
    """Prefiere tonnes almacenadas. Soporta registros previos sin migrar para pruebas."""
    raw = record.get("tonnes")
    try:
        if raw is not None:
            ton = Decimal(str(raw))
        elif record.get("sacks") is not None:
            ton = Decimal(str(record["sacks"])) * TONS_PER_SACK
        else:
            raise ValueError("Falta cantidad")
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Cantidad inválida") from exc
    if not ton.is_finite() or ton <= 0:
        raise ValueError("Cantidad no positiva")
    return ton


def rounded_tonnes(value: object) -> int:
    """El parámetro YA está expresado en toneladas; redondeo sólo visual."""
    value = Decimal(str(value))
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_tonnes(value: object, *, places: int = 4) -> str:
    number = Decimal(str(value))
    return f"{number:,.{places}f}".rstrip("0").rstrip(".")


def build_daily_summary(
    records: list[dict[str, Any]], reference: date, *, warehouse: str = "Todas", **_ignored: Any
) -> dict[str, Any]:
    if warehouse != "Todas" and warehouse not in WAREHOUSE_USERS:
        raise ValueError("Bodega inválida.")
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    valid: list[dict[str, Any]] = []
    anomalous: list[dict[str, Any]] = []
    total_tonnes = Decimal("0")
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
            tonnes = record_tonnes(record)
        except (ValueError, KeyError, TypeError):
            anomalous.append(record)
            continue
        band = age_band(production, reference)
        if band == "inconsistente":
            anomalous.append(record)
            continue
        key = (depot, product)
        if key not in groups:
            groups[key] = {"warehouse": depot, "product": product, "tonnes": Decimal("0"), "entries": 0,
                           "bands": defaultdict(lambda: Decimal("0"))}
        groups[key]["tonnes"] += tonnes
        groups[key]["entries"] += 1
        groups[key]["bands"][band] += tonnes
        total_tonnes += tonnes
        valid.append(record)
    rows: list[dict[str, Any]] = []
    for depot in WAREHOUSE_USERS:
        if warehouse != "Todas" and depot != warehouse:
            continue
        for product in PRODUCTS:
            group = groups.get((depot, product))
            if group is None:
                continue
            rows.append({
                "warehouse": depot, "product": product, "entries": group["entries"],
                "tonnes": group["tonnes"],
                **{band: group["bands"].get(band, Decimal("0")) for band in BUCKETS},
            })
    totals = {band: sum((row[band] for row in rows), Decimal("0")) for band in BUCKETS}
    return {
        "rows": rows, "totals": totals, "tonnes": total_tonnes,
        "records": valid, "anomalous": anomalous, "count": len(valid), "unit": "ton",
    }
