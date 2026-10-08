"""Reglas puras del formulario, sin dependencias de interfaz ni de BD."""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from src.config import MAX_SACKS_PER_ENTRY, PRODUCTS, SACKS_PER_PALLET, TIMEZONE, WAREHOUSE_USERS

GT_ZONE = ZoneInfo(TIMEZONE)


def today_guatemala() -> date:
    return datetime.now(GT_ZONE).date()


def now_guatemala() -> datetime:
    return datetime.now(GT_ZONE)


def format_timestamp(value: str | datetime) -> str:
    """Convierte un timestamptz UTC de Supabase a dd/mm/yyyy HH:MM:SS de Guatemala."""
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(GT_ZONE).strftime("%d/%m/%Y %H:%M:%S")


def format_date(value: date | str) -> str:
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime("%d/%m/%Y")


def age_in_days(production: date, reference: date | None = None) -> int:
    return ((reference or today_guatemala()) - production).days


def pallet_equivalent(sacks: int) -> tuple[int, int]:
    """Estibas completas y sacos restantes; solo equivalencia informativa."""
    return divmod(sacks, SACKS_PER_PALLET)


def validate_entry(
    *,
    employee: str,
    home_warehouse: str,
    active_warehouse: str,
    support: bool,
    product: str,
    sacks: int,
    production: date,
    reference: date | None = None,
) -> None:
    if home_warehouse not in WAREHOUSE_USERS:
        raise ValueError("La bodega de origen no es válida.")
    if employee not in WAREHOUSE_USERS[home_warehouse]:
        raise ValueError("El usuario no pertenece a la bodega de origen.")
    if active_warehouse not in WAREHOUSE_USERS:
        raise ValueError("La bodega de operación no es válida.")
    if bool(support) != (active_warehouse != home_warehouse):
        raise ValueError("El modo Apoyo debe coincidir con la bodega seleccionada.")
    if product not in PRODUCTS:
        raise ValueError("El producto seleccionado no es válido.")
    if isinstance(sacks, bool) or not isinstance(sacks, int) or not (1 <= sacks <= MAX_SACKS_PER_ENTRY):
        raise ValueError("La cantidad debe ser un entero positivo dentro del rango permitido.")
    if not isinstance(production, date) or isinstance(production, datetime):
        raise ValueError("La fecha de producción no es válida.")
    if production > (reference or today_guatemala()):
        raise ValueError("La fecha de producción no puede ser posterior a hoy.")
    if production < date(2000, 1, 1):
        raise ValueError("La fecha de producción está fuera del rango permitido.")
