"""ARGOS Guatemala | Registro de producción e inventario por bodega.

Ejecución: streamlit run app.py
"""

from __future__ import annotations

import csv
import html
import io
import logging
import uuid
from decimal import Decimal
from datetime import date

import streamlit as st

from src.auth import verify_pin
from src.config import (
    APP_TITLE, MAX_SACKS_PER_ENTRY, PRODUCTS, PRODUCT_STYLES,
    SUPERVISOR_ACCESS, SUPERVISOR_NAME, WAREHOUSE_USERS,
)
from src.db import entries_on_date, get_secret, insert_entry, is_configured, recent_entries
from src.domain import age_in_days, format_date, format_timestamp, now_guatemala, pallet_equivalent, today_guatemala, validate_entry
from src.report import BUCKETS, age_band, build_daily_summary, rounded_tonnes
from src.style import apply_style

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("argos")

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="assets/brand-mark.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_style()


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def brand() -> None:
    st.markdown(
        """
        <div class="brand-row">
          <div class="brand-left">
            <div class="brand-emblem">
              <svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 26h9l6-12 8 23 5-11h10" fill="none" stroke="#C4D600" stroke-width="4.1" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div><div class="brand-word">ARGOS</div><div class="brand-desc">Guatemala · Importaciones</div></div>
          </div>
          <div class="brand-chip"><span class="chip-dot"></span>Gestión inteligente de inventario</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def login() -> None:
    brand()
    hero, form_column = st.columns([1.15, 1], gap="large", vertical_alignment="center")
    with hero:
        st.markdown(
            """
            <div class="hero">
              <div class="hero-kicker">OPERACIÓN · GUATEMALA</div>
              <div class="hero-title">Control más claro.<br><em>Inventario más inteligente.</em></div>
              <div class="hero-sub">Una experiencia simple para capturar la producción del cemento, mantener la trazabilidad del registro y conectar a quienes operan nuestras bodegas.</div>
              <div class="hero-footer"><span class="hero-stat">03 Bodegas</span><span class="hero-stat">07 Productos</span><span class="hero-stat">Registro en tiempo real</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with form_column:
        st.markdown(
            """<div class="login-head"><div class="kicker">ACCESO OPERATIVO</div><div class="heading">Bienvenido de nuevo</div><div class="description">Selecciona tu bodega o el acceso de supervisión para comenzar.</div></div>""",
            unsafe_allow_html=True,
        )
        home = st.selectbox("Bodega habitual / tipo de acceso", options=[*WAREHOUSE_USERS, SUPERVISOR_ACCESS], key="login_home")
        is_supervisor = home == SUPERVISOR_ACCESS
        if is_supervisor:
            employee = SUPERVISOR_NAME
            active, support = "Todas", False
            st.markdown('<div class="supervisor-access">Supervisión · <b>Rudy Anavisca</b><br><small>Consulta de las tres bodegas</small></div>', unsafe_allow_html=True)
        else:
            employee = st.selectbox("Selecciona tu nombre", options=WAREHOUSE_USERS[home], key="login_employee")
            support = st.toggle("Apoyo · Voy a trabajar en otra bodega", key="login_support")
            active = home
            if support:
                destinations = [w for w in WAREHOUSE_USERS if w != home]
                active = st.selectbox("¿A qué bodega vas a apoyar?", destinations, key="login_destination")
                st.caption(f"Tus registros se guardarán en {active}, a nombre de {employee}.")

        auth_mode = str(get_secret("AUTH_MODE", "selector")).strip().lower()
        if auth_mode not in ("selector", "pin"):
            st.error("AUTH_MODE inválido. Utiliza 'selector' o 'pin' en Secrets.")
            return
        pin = ""
        if is_supervisor:
            pin = st.text_input("PIN de supervisor *", type="password", key="login_supervisor_pin")
            st.caption("Por seguridad, el acceso a los registros globales requiere PIN incluso si los operarios usan selector de nombre.")
        elif auth_mode == "pin":
            pin = st.text_input("PIN personal", type="password", help="PIN definido por el administrador.", key="login_pin")

        st.write("")
        if st.button("Ingresar a la plataforma  →", use_container_width=True, type="primary"):
            if is_supervisor:
                hashes = get_secret("PIN_HASHES", {})
                expected_hash = get_secret("SUPERVISOR_PIN_HASH") or (hashes.get(SUPERVISOR_NAME) if hashes else None)
                if not expected_hash:
                    st.error("Acceso de supervisor no configurado: agrega SUPERVISOR_PIN_HASH en Secrets (consulta ACTUALIZACION.md).")
                    return
                if not verify_pin(pin, str(expected_hash)):
                    st.error("PIN de supervisor incorrecto.")
                    return
            elif auth_mode == "pin":
                hashes = get_secret("PIN_HASHES", {})
                expected_hash = hashes.get(employee) if hashes else None
                if not expected_hash or not verify_pin(pin, str(expected_hash)):
                    st.error("PIN incorrecto o no configurado para este usuario.")
                    return
            st.session_state.identity = {
                "role": "supervisor" if is_supervisor else "operator",
                "employee": employee,
                "home": None if is_supervisor else home,
                "warehouse": active,
                "support": support,
            }
            st.session_state.pending_request_id = str(uuid.uuid4())
            st.rerun()
        if auth_mode == "selector" and not is_supervisor:
            st.caption("Acceso por selección de nombre. Para verificar identidad, el administrador puede activar PIN individual.")
    st.markdown('<div class="footer-mini">ARGOS GUATEMALA · CONTROL OPERATIVO DE BODEGAS</div>', unsafe_allow_html=True)


def logout() -> None:
    for key in ("identity", "pending_request_id", "login_pin", "login_supervisor_pin"):
        st.session_state.pop(key, None)
    st.rerun()


def sidebar(identity: dict[str, object]) -> None:
    supervisor = identity.get("role") == "supervisor"
    with st.sidebar:
        st.markdown('<div class="side-logo">ARGOS</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="side-card">'
            '<div class="side-k">' + ('Supervisor' if supervisor else 'Operador') + '</div>'
            f'<div class="side-v">{e(identity["employee"])}</div>'
            '<div class="side-k">' + ('Alcance' if supervisor else 'Bodega en operación') + '</div>'
            f'<div class="side-v">{("Todas las bodegas" if supervisor else e(identity["warehouse"]))}</div>'
            + ('' if supervisor else (
                '<div class="side-k">Modalidad</div>'
                f'<div class="side-v">{"Apoyo temporal" if identity["support"] else "Asignación habitual"}</div>'
            )) + '</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        if not supervisor and st.button("Cambiar bodega / Apoyo", use_container_width=True, key="sidebar_switch"):
            logout()
        if st.button("Salir", use_container_width=True, key="sidebar_logout"):
            logout()
        st.divider()
        st.caption("Fecha y hora en Guatemala (UTC−6). Las capturas permanecen guardadas en Supabase.")


def welcome(identity: dict[str, object]) -> None:
    brand()
    support = " · En apoyo" if identity["support"] else ""
    st.markdown(
        '<div class="welcome">'
        '<small>PORTAL DE CAPTURA · OPERACIÓN LOGÍSTICA</small>'
        f'<h2>Hola, {e(str(identity["employee"]).split()[0])}.</h2>'
        f'<p>Estás registrando información para <b>{e(identity["warehouse"])}</b>{e(support)}. '
        'Cada registro se almacena con su responsable y hora de captura.</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def supervisor_welcome() -> None:
    brand()
    st.markdown(
        '<div class="welcome supervisor-welcome">'
        '<small>PORTAL DE SUPERVISIÓN · IMPORTACIONES</small>'
        '<h2>Hola, Rudy.</h2>'
        '<p>Consolida los ingresos registrados en Morales, Morales 2 y Bárcenas. '
        'Filtra el día de captura y revisa la antigüedad del producto al momento del registro.</p>'
        '</div>', unsafe_allow_html=True,
    )


def product_chip(product: str) -> str:
    style = PRODUCT_STYLES[product]
    return (
        f'<span class="product-chip" style="background:{style["background"]};'
        f'color:{style["foreground"]}">{e(product)}</span>'
    )


def record_form(identity: dict[str, object]) -> None:
    st.markdown('<div class="section-title">Nuevo registro</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Captura el producto, la cantidad de sacos y su fecha de producción. Los datos de operador, bodega y hora se completan automáticamente.</div>',
        unsafe_allow_html=True,
    )
    with st.form("capture", clear_on_submit=False, border=True):
        left, right = st.columns(2, gap="large")
        with left:
            product = st.selectbox("Producto *", options=PRODUCTS, index=0)
            sacks = st.number_input(
                "Cantidad de sacos *",
                min_value=1,
                max_value=MAX_SACKS_PER_ENTRY,
                value=40,
                step=1,
                help="Cada estiba completa equivale a 40 sacos; puedes ingresar otra cantidad.",
            )
        with right:
            production = st.date_input(
                "Producción *",
                value=today_guatemala(),
                min_value=date(2000, 1, 1),
                max_value=today_guatemala(),
                format="DD/MM/YYYY",
                help="Selecciona la fecha real de fabricación que estás registrando.",
            )
            full, extra = pallet_equivalent(int(sacks))
            st.caption(f"Equivalencia: {full} estiba(s) completa(s) de 40 sacos" + (f" y {extra} saco(s) adicionales." if extra else "."))
        st.markdown(
            '<div class="form-note"><div class="note-icon">i</div>'
            '<div><b>Fecha y hora automáticas.</b> El servidor fija el momento exacto del guardado. '
            'Se muestra en formato DD/MM/AAAA HH:MM:SS, hora de Guatemala.</div></div>',
            unsafe_allow_html=True,
        )
        st.write("")
        submitted = st.form_submit_button("Guardar registro  →", type="primary", use_container_width=True)

    if submitted:
        try:
            validate_entry(
                employee=str(identity["employee"]),
                home_warehouse=str(identity["home"]),
                active_warehouse=str(identity["warehouse"]),
                support=bool(identity["support"]),
                product=product,
                sacks=int(sacks),
                production=production,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        if not is_configured():
            st.error("No se guardó: falta configurar SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en Secrets.")
            return
        request_id = st.session_state.setdefault("pending_request_id", str(uuid.uuid4()))
        try:
            with st.spinner("Guardando en Supabase…"):
                row = insert_entry(
                    request_id=request_id,
                    employee=str(identity["employee"]),
                    home_warehouse=str(identity["home"]),
                    warehouse=str(identity["warehouse"]),
                    is_support=bool(identity["support"]),
                    product=product,
                    sacks=int(sacks),
                    production_date=production,
                )
        except Exception:
            LOGGER.exception("Error de Supabase al guardar registro")
            st.error("No se pudo guardar. Revisa la conexión, los secretos y que hayas ejecutado sql/schema.sql en Supabase. Puedes reintentar sin crear un duplicado.")
            return
        st.session_state.pending_request_id = str(uuid.uuid4())
        stamp = format_timestamp(row["created_at"])
        st.markdown(
            f'<div class="status-ok">✓ Registro guardado · {e(product)} · {int(sacks)} sacos · Producción {format_date(production)} · {stamp}</div>',
            unsafe_allow_html=True,
        )
        st.toast("Registro guardado correctamente", icon="✅")


def summary_and_recent(identity: dict[str, object]) -> None:
    st.markdown('<div class="section-title">Actividad de la bodega</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Últimos registros de la bodega seleccionada, visibles para el personal de esa bodega.</div>', unsafe_allow_html=True)
    if not is_configured():
        st.info("Vista previa lista. Configura los secretos de Supabase para habilitar guardado e historial.")
        return
    try:
        records = recent_entries(str(identity["warehouse"]))
    except Exception:
        LOGGER.exception("Error consultando historial")
        st.warning("No fue posible cargar el historial. El formulario sigue disponible para registrar información.")
        return
    today = today_guatemala()
    current = [r for r in records if format_timestamp(r["created_at"]).startswith(today.strftime("%d/%m/%Y"))]
    counters = [
        ("Registros recientes", str(len(records)), "Últimos 12 movimientos"),
        ("Sacos en registros recientes", f"{sum(int(r['sacks']) for r in records):,}", "Capturas mostradas"),
        ("Registros de hoy", str(len(current)), "Entre los últimos 12 registros"),
    ]
    cols = st.columns(3, gap="medium")
    for col, (label, value, helper) in zip(cols, counters):
        with col:
            st.markdown(
                f'<div class="dash-card"><div class="dash-label">{e(label)}</div>'
                f'<div class="dash-value">{e(value)}</div><div class="dash-helper">{e(helper)}</div></div>',
                unsafe_allow_html=True,
            )
    st.write("")
    if not records:
        st.markdown('<div class="empty-state">Aún no hay registros para esta bodega. Guarda el primero desde el formulario.</div>', unsafe_allow_html=True)
        return
    headers = st.columns([2.0, 1.3, .8, 1.4, 1.15, 2.1], gap="small")
    for col, title in zip(headers, ("Fecha / hora", "Producto", "Sacos", "Producción", "Edad", "Responsable")):
        with col:
            st.caption(title)
    for r in records:
        cols = st.columns([2.0, 1.3, .8, 1.4, 1.15, 2.1], gap="small", vertical_alignment="center")
        with cols[0]: st.caption(format_timestamp(r["created_at"]))
        with cols[1]: st.markdown(product_chip(r["product"]), unsafe_allow_html=True)
        with cols[2]: st.write(f"**{r['sacks']}**")
        with cols[3]: st.caption(format_date(r["production_date"]))
        with cols[4]: st.caption(f"{age_in_days(date.fromisoformat(r['production_date']))} días")
        with cols[5]: st.caption(str(r["employee_name"]) + (" · Apoyo" if r.get("is_support") else ""))
    st.caption("La edad se calcula desde la fecha de producción. Los registros muestran capturas, no existencias netas: todavía no se descuentan salidas.")


def _quantity(value: Decimal, unit: str) -> str:
    return f"{value:,.2f}" if unit == "tn" else f"{int(value):,}"


def _csv_text(rows: list[list[object]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        # Evita fórmulas al abrir CSV en Excel si algún dato de texto resulta malicioso.
        writer.writerow([("'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value) for value in row])
    return "\ufeff" + output.getvalue()


def _warehouse_groups(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    """Agrupa productos en el orden recibido, sin duplicar bodegas."""
    groups: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        groups.setdefault(str(row["warehouse"]), []).append(row)
    return groups


def _warehouse_subtotal(rows: list[dict[str, object]]) -> dict[str, int]:
    """Suma sacos por rango y total, antes de redondear las toneladas."""
    return {
        **{band: sum(int(row[band]) for row in rows) for band in BUCKETS},
        "sacks": sum(int(row["sacks"]) for row in rows),
    }



def _summary_csv_rows(report: dict[str, object]) -> list[list[object]]:
    """Exporta productos y un subtotal por bodega, seguido del total general."""
    summary_rows: list[list[object]] = [[
        "Bodega", "Producto", "Verde", "Amarillo", "Naranja", "Rojo",
        "Total (sacos)", "Total (ton)", "Pedidos", "Pedidos (ton)",
    ]]
    for warehouse, products in _warehouse_groups(report["rows"]).items():
        for row in products:
            summary_rows.append([
                warehouse, row["product"], *(int(row[key]) for key in BUCKETS),
                int(row["sacks"]), rounded_tonnes(row["sacks"]), "", "",
            ])
        subtotal = _warehouse_subtotal(products)
        summary_rows.append([
            warehouse, "SUBTOTAL", *(subtotal[key] for key in BUCKETS),
            subtotal["sacks"], rounded_tonnes(subtotal["sacks"]), "", "",
        ])
    summary_rows.append([
        "TOTAL GENERAL", "", *(int(report["totals"][key]) for key in BUCKETS),
        int(report["sacks"]), rounded_tonnes(report["sacks"]), "", "",
    ])
    return summary_rows


def _report_html(report: dict[str, object]) -> str:
    """Semáforo en sacos, toneladas redondeadas y columnas Odoo reservadas.

    Mantiene la tabla en pantallas grandes y ofrece tarjetas para smartphones.
    Nunca presenta capturas como inventario neto ni simula pedidos.
    """
    headers = (
        '<th scope="col">BODEGA</th><th scope="col">PRODUCTO</th>'
        '<th scope="col" class="th-verde">VERDE<br><span>0–10 días</span></th>'
        '<th scope="col" class="th-amarillo">AMARILLO<br><span>11–15 días</span></th>'
        '<th scope="col" class="th-naranja">NARANJA<br><span>16–20 días</span></th>'
        '<th scope="col" class="th-rojo">ROJO<br><span>21+ días</span></th>'
        '<th scope="col">TOTAL<br><span>(SACOS)</span></th>'
        '<th scope="col">TOTAL<br><span>(TON)</span></th>'
        '<th scope="col" class="th-odoo th-odoo-start">PEDIDOS</th>'
        '<th scope="col" class="th-odoo">PEDIDOS<br><span>(TON)</span></th>'
    )
    # Cada bodega comparte una celda vertical, incluidos sus subtotales.
    grouped = _warehouse_groups(report["rows"])

    body: list[str] = []
    cards: list[str] = []
    for warehouse, warehouse_products in grouped.items():
        depot = e(warehouse)
        subtotal = _warehouse_subtotal(warehouse_products)
        subtotal_sacks = subtotal["sacks"]
        subtotal_tonnes = rounded_tonnes(subtotal_sacks)
        body.append(f'<tbody class="inv-warehouse-group" aria-label="Bodega {depot}">')
        mobile_cards: list[str] = []
        for index, row in enumerate(warehouse_products):
            total_sacks = int(row["sacks"])
            total_tonnes = rounded_tonnes(total_sacks)
            bands = [f'{int(row[key]):,}' for key in BUCKETS]
            # Un único nombre de bodega, centrado horizontal y verticalmente.
            # Cada tbody representa un grupo real, accesible con scope=rowgroup.
            body.append('<tr class="inv-group-start">' if index == 0 else '<tr>')
            if index == 0:
                body.append(
                    f'<th scope="rowgroup" class="depot-cell" rowspan="{len(warehouse_products) + 1}">'
                    f'<span>{depot}</span></th>'
                )
            body.append(
                f'<td class="product-cell">{product_chip(str(row["product"]))}</td>'
                + ''.join(
                    f'<td class="band-cell band-{key}">{value}</td>'
                    for key, value in zip(BUCKETS, bands)
                )
                + f'<td class="total-cell">{total_sacks:,}</td>'
                + f'<td class="tonnes-cell">{total_tonnes:,}</td>'
                + '<td class="odoo-cell odoo-start"></td><td class="odoo-cell"></td></tr>'
            )
            band_cards = ''.join(
                f'<div class="mobile-band band-{key}"><span>{label}</span><b>{value}</b></div>'
                for key, label, value in zip(
                    BUCKETS,
                    ("Verde · 0–10", "Amarillo · 11–15", "Naranja · 16–20", "Rojo · 21+"),
                    bands,
                )
            )
            mobile_cards.append(
                '<article class="inv-mobile-card">'
                f'<div class="inv-card-head">{product_chip(str(row["product"]))}</div>'
                f'<div class="inv-card-total">{total_sacks:,} <span>sacos · {total_tonnes:,} ton</span></div>'
                f'<div class="mobile-bands">{band_cards}</div>'
                '<div class="inv-card-orders"><span>PEDIDOS <b></b></span><span>PEDIDOS (TON) <b></b></span></div>'
                '</article>'
            )
        # Subtotal del grupo: BODEGA sigue siendo una celda única y centrada.
        # Las columnas de Odoo se mantienen vacías hasta conectar el ERP.
        body.append(
            '<tr class="inv-warehouse-subtotal-row">'
            '<th scope="row" class="inv-subtotal-label">SUBTOTAL</th>'
            + ''.join(f'<td>{subtotal[key]:,}</td>' for key in BUCKETS)
            + f'<td>{subtotal_sacks:,}</td><td>{subtotal_tonnes:,}</td>'
            + '<td class="odoo-cell odoo-start"></td><td class="odoo-cell"></td></tr>'
        )
        body.append('</tbody>')
        # En móviles se resume también cada bodega tras sus productos.
        subtotal_bands = ''.join(
            f'<div class="mobile-band band-{key}"><span>{label}</span><b>{subtotal[key]:,}</b></div>'
            for key, label in zip(BUCKETS, ("Verde · 0–10", "Amarillo · 11–15", "Naranja · 16–20", "Rojo · 21+"))
        )
        mobile_cards.append(
            '<div class="inv-mobile-warehouse-subtotal">'
            '<div class="inv-mobile-warehouse-subtotal-head">'
            '<strong>SUBTOTAL DE BODEGA</strong>'
            f'<span>{subtotal_sacks:,} sacos · {subtotal_tonnes:,} ton</span></div>'
            f'<div class="mobile-bands">{subtotal_bands}</div>'
            '<div class="inv-card-orders"><span>PEDIDOS <b></b></span><span>PEDIDOS (TON) <b></b></span></div>'
            '</div>'
        )
        # En móviles el nombre de la bodega también aparece solo una vez.
        cards.append(
            f'<section class="inv-mobile-warehouse" aria-label="Bodega {depot}">'
            f'<div class="inv-mobile-warehouse-title">{depot}</div>'
            '<div class="inv-mobile-products">' + ''.join(mobile_cards) + '</div>'
            '</section>'
        )
    totals = report["totals"]
    assert isinstance(totals, dict)
    overall_sacks = int(report["sacks"])
    footer = (
        '<tr class="inv-grand-total"><th scope="row" colspan="2">TOTAL GENERAL</th>'
        + ''.join(f'<td>{int(totals[key]):,}</td>' for key in BUCKETS)
        + f'<td>{overall_sacks:,}</td><td>{rounded_tonnes(overall_sacks):,}</td>'
        + '<td class="odoo-cell odoo-start"></td><td class="odoo-cell"></td></tr>'
    )
    return (
        '<div class="inv-report-desktop"><div class="inv-report-scroll" role="region" aria-label="Semáforo de inventario" tabindex="0">'
        '<table class="inv-report"><colgroup>'
        '<col class="col-depot"><col class="col-product">'
        '<col class="col-band" span="4"><col class="col-sacks"><col class="col-tonnes">'
        '<col class="col-orders"><col class="col-orders-tonnes">'
        '</colgroup><thead><tr>' + headers + '</tr></thead>'
        + ''.join(body) + '<tbody class="inv-summary-group">' + footer + '</tbody></table></div></div>'
        '<div class="inv-report-mobile">' + ''.join(cards)
        + f'<div class="inv-mobile-total"><span>TOTAL GENERAL</span><strong>{overall_sacks:,} sacos · {rounded_tonnes(overall_sacks):,} ton</strong></div></div>'
    )


def supervisor_dashboard() -> None:
    supervisor_welcome()
    header, logout_col = st.columns([5, 1], vertical_alignment="center")
    with header:
        st.caption("Supervisor · Rudy Anavisca · Acceso a las tres bodegas")
    with logout_col:
        if st.button("⏻  Salir", type="primary", key="top_exit_supervisor", use_container_width=True):
            logout()

    st.markdown('<div class="section-title">Semáforo diario de capturas</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Selecciona la fecha de <b>registro</b>. La antigüedad se compara contra la fecha de '
        'producción informada por el operario. Este reporte consolida capturas del día, no existencias netas.</div>',
        unsafe_allow_html=True,
    )
    filter_day, filter_depot = st.columns([1, 1], gap="medium")
    with filter_day:
        selected_day = st.date_input(
            "Día de registro", value=today_guatemala(), min_value=date(2020, 1, 1),
            max_value=today_guatemala(), format="DD/MM/YYYY", key="report_day",
        )
    with filter_depot:
        selected_depot = st.selectbox("Bodega", ["Todas", *WAREHOUSE_USERS], key="report_warehouse")

    if not is_configured():
        st.warning("Configura Supabase para consultar capturas reales. No hay datos de demostración.")
        return
    try:
        with st.spinner("Consultando capturas de Supabase…"):
            records = entries_on_date(selected_day)
        report = build_daily_summary(records, selected_day, warehouse=selected_depot)
    except ValueError as exc:
        st.error(f"Configuración incorrecta: {exc}")
        return
    except Exception:
        LOGGER.exception("Error consultando los registros del supervisor")
        st.error("No fue posible consultar Supabase. Revisa Secrets y la conexión.")
        return

    if report["anomalous"]:
        st.warning(f"Hay {len(report['anomalous'])} registros con fechas o datos inconsistentes que fueron excluidos del semáforo. Revisa la fuente.")
    if not report["rows"]:
        st.info("No hay capturas para la fecha y bodega seleccionadas.")
        return

    # Estas cifras representan SACOS CAPTURADOS, no saldo disponible en bodega.
    metric1, metric2, metric3 = st.columns(3, gap="medium")
    ageing_sacks = sum(int(report["totals"][key]) for key in ("amarillo", "naranja", "rojo"))
    for col, label, value, description in (
        (metric1, "SACOS REGISTRADOS", f"{report['sacks']:,}", ""),
        (metric2, "TONELADAS REGISTRADAS", f"{rounded_tonnes(report['sacks']):,}", ""),
        (metric3, "MÁS DE 10 DÍAS", f"{ageing_sacks:,} sacos", "Antigüedad al día de registro"),
    ):
        with col:
            helper_html = f'<div class="dash-helper">{e(description)}</div>' if description else ''
            st.markdown(f'<div class="dash-card"><div class="dash-label">{e(label)}</div>'
                        f'<div class="dash-value">{e(value)}</div>{helper_html}</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(_report_html(report), unsafe_allow_html=True)
    st.caption(
        "Verde: 0–10 días · Amarillo: 11–15 · Naranja: 16–20 · Rojo: 21 o más días. "
        "TOTAL (TON) = sacos × 0.0425, redondeado al entero más cercano. "
        "PEDIDOS y PEDIDOS (TON) están pendientes de integración con Odoo. "
        "Son registros capturados, no existencias netas."
    )

    summary_rows = _summary_csv_rows(report)
    st.download_button(
        "Descargar semáforo (CSV)", data=_csv_text(summary_rows),
        file_name=f"semaforo_capturas_{selected_day.isoformat()}.csv", mime="text/csv",
        use_container_width=True,
    )

    with st.expander(f"Ver detalle de {report['count']} registros", expanded=False):
        st.caption("Hora de Guatemala · Incluye nombre del operador y registros de Apoyo")
        detail = []
        for record in sorted(report["records"], key=lambda r: r["created_at"], reverse=True):
            production = date.fromisoformat(record["production_date"])
            detail.append({
                "Registro": format_timestamp(record["created_at"]),
                "Bodega": record["warehouse"],
                "Producto": record["product"],
                "Sacos": record["sacks"],
                "Producción": format_date(production),
                "Edad (días)": age_in_days(production, selected_day),
                "Semáforo": age_band(production, selected_day).capitalize(),
                "Responsable": record["employee_name"],
                "Apoyo": "Sí" if record.get("is_support") else "No",
            })
        st.dataframe(detail, hide_index=True, use_container_width=True, height=min(590, 92 + 36 * len(detail)))
        st.download_button(
            "Descargar detalle (CSV)",
            data=_csv_text([list(detail[0])] + [list(row.values()) for row in detail]),
            file_name=f"detalle_capturas_{selected_day.isoformat()}.csv", mime="text/csv",
            use_container_width=True,
        )


def main() -> None:
    identity = st.session_state.get("identity")
    if identity is None:
        login()
        return
    sidebar(identity)
    if identity.get("role") == "supervisor":
        supervisor_dashboard()
        st.markdown('<div class="footer-mini">ARGOS · IMPORTACIONES · GUATEMALA</div>', unsafe_allow_html=True)
        return
    welcome(identity)
    toolbar_info, toolbar_action, toolbar_exit = st.columns([3.2, 1.6, .8], vertical_alignment="center")
    with toolbar_info:
        st.caption(f"Bodega activa: {identity['warehouse']} · {'Apoyo temporal' if identity['support'] else 'Asignación habitual'}")
    with toolbar_action:
        if st.button("Cambiar bodega / Apoyo", key="quick_switch", use_container_width=True):
            logout()
    with toolbar_exit:
        if st.button("⏻  Salir", type="primary", key="top_exit_operator", use_container_width=True):
            logout()
    st.write("")
    if not is_configured():
        st.warning("Modo de configuración: Supabase todavía no está conectado. Puedes revisar la interfaz, pero el guardado está deshabilitado.")
    record_form(identity)
    st.write("")
    summary_and_recent(identity)
    st.markdown('<div class="footer-mini">ARGOS · PLATAFORMA DE OPERACIÓN Y ABASTECIMIENTO · GUATEMALA</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
