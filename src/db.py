"""Supabase: captura de sacos con conversión a toneladas, histórico conservado."""
from __future__ import annotations
import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import streamlit as st
from supabase import Client, create_client
from src.report import day_bounds_utc

LOGGER = logging.getLogger(__name__)
TABLE = "inventory_records"


def get_secret(key: str, default: Any = None) -> Any:
    try:
        return st.secrets.get(key, default)
    except FileNotFoundError:
        return default


def is_configured() -> bool:
    return bool(get_secret("SUPABASE_URL") and get_secret("SUPABASE_SERVICE_ROLE_KEY"))


@st.cache_resource(show_spinner=False)
def _cached_client(url: str, api_key: str) -> Client:
    return create_client(url, api_key)


def get_client() -> Client:
    url, api_key = get_secret("SUPABASE_URL"), get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not api_key:
        raise RuntimeError("Falta configurar Supabase en Secrets de Streamlit.")
    return _cached_client(str(url), str(api_key))


def insert_entry(*, request_id: str, employee: str, home_warehouse: str, warehouse: str,
                 is_support: bool, product: str, sacks: int, tonnes: Decimal, production_date: date) -> dict[str, Any]:
    payload = {
        "request_id": str(uuid.UUID(request_id)), "employee_name": employee,
        "home_warehouse": home_warehouse, "warehouse": warehouse,
        "is_support": is_support, "product": product,
        "sacks": sacks, "tonnes": str(tonnes), "production_date": production_date.isoformat(),
    }
    client = get_client()
    try:
        result = client.table(TABLE).insert(payload).execute()
        if not result.data:
            raise RuntimeError("Supabase no devolvió el registro insertado.")
        return dict(result.data[0])
    except Exception:
        try:
            previous = client.table(TABLE).select("*").eq("request_id", payload["request_id"]).limit(1).execute()
            if previous.data:
                return dict(previous.data[0])
        except Exception:
            LOGGER.exception("No se pudo recuperar una inserción posiblemente duplicada")
        raise


def recent_entries(warehouse: str, limit: int = 12) -> list[dict[str, Any]]:
    result = (get_client().table(TABLE)
              .select("*")
              .eq("warehouse", warehouse).order("created_at", desc=True).limit(limit).execute())
    return list(result.data or [])


def entries_on_date(selected_date: date, *, page_size: int = 500) -> list[dict[str, Any]]:
    start, end = day_bounds_utc(selected_date)
    records: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (get_client().table(TABLE)
                    .select("*")
                    .gte("created_at", start).lt("created_at", end)
                    .order("created_at", desc=False)
                    .range(offset, offset + page_size - 1).execute())
        page = list(response.data or [])
        records.extend(page)
        if len(page) < page_size:
            return records
        offset += page_size


def safe_db_error(exc: Exception) -> str:
    """Muestra una pista de error segura, sin credenciales, SQL o URLs privadas."""
    code = str(getattr(exc, "code", "") or "")
    status = str(getattr(exc, "status_code", "") or "")
    # Supabase/PostgREST puede incorporar el código en un diccionario de args.
    for arg in getattr(exc, "args", ()):
        if isinstance(arg, dict):
            code = code or str(arg.get("code", "") or "")
            status = status or str(arg.get("status_code", "") or "")
    known = {
        "42P01": "La tabla inventory_records no existe en el proyecto configurado.",
        "42703": "Falta alguna columna esperada; revisa la migración SQL en el proyecto correcto.",
        "PGRST204": "El API no reconoce una columna. Recarga el esquema de PostgREST en Supabase.",
        "42501": "La clave de Supabase no tiene permiso para consultar la tabla.",
        "PGRST301": "Error de autenticación con Supabase; revisa la Service Role Key.",
    }
    if code in known:
        return f"[{code}] {known[code]}"
    if code and code.replace("_", "").isalnum() and len(code) <= 20:
        return f"Código de error: {code}. Revisa Manage app → Logs."
    if status.isdigit():
        return f"HTTP {status}. Revisa Manage app → Logs."
    return "Consulta los Logs de Streamlit para identificar la causa (sin compartir credenciales)."
