"""Acceso a Supabase: solamente del lado servidor de Streamlit."""

from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Any

import streamlit as st
from supabase import Client, create_client

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
    url = get_secret("SUPABASE_URL")
    api_key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not api_key:
        raise RuntimeError("Falta configurar Supabase en los secretos de Streamlit.")
    return _cached_client(str(url), str(api_key))


def insert_entry(
    *,
    request_id: str,
    employee: str,
    home_warehouse: str,
    warehouse: str,
    is_support: bool,
    product: str,
    sacks: int,
    production_date: date,
) -> dict[str, Any]:
    """Inserta una sola vez. request_id evita duplicados por reintentos."""
    payload = {
        "request_id": str(uuid.UUID(request_id)),
        "employee_name": employee,
        "home_warehouse": home_warehouse,
        "warehouse": warehouse,
        "is_support": is_support,
        "product": product,
        "sacks": sacks,
        "production_date": production_date.isoformat(),
    }
    client = get_client()
    try:
        result = client.table(TABLE).insert(payload).execute()
        if not result.data:
            raise RuntimeError("Supabase no devolvió el registro insertado.")
        return dict(result.data[0])
    except Exception:
        # Si se guardó pero la respuesta se perdió, un reintento con el mismo
        # request_id recupera el registro, sin insertarlo dos veces.
        try:
            previous = client.table(TABLE).select("*").eq("request_id", payload["request_id"]).limit(1).execute()
            if previous.data:
                return dict(previous.data[0])
        except Exception:
            LOGGER.exception("No se pudo recuperar una inserción potencialmente duplicada")
        raise


def recent_entries(warehouse: str, limit: int = 12) -> list[dict[str, Any]]:
    result = (
        get_client()
        .table(TABLE)
        .select("id,created_at,employee_name,warehouse,is_support,product,sacks,production_date")
        .eq("warehouse", warehouse)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(result.data or [])
