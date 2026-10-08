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
from src.report import BUCKETS, age_band, build_daily_summary, configured_weights
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
              <div class="hero-footer"><span class="hero-stat">03 Bodegas</span><span class="hero-stat">04 Productos</span><span class="hero-stat">Registro en tiempo real</span></div>
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


def _report_html(report: dict[str, object]) -> str:
    """Tabla panorámica para desktop/TV y tarjetas apiladas para teléfonos."""
    unit = str(report["unit"])
    headers = (
        '<th>BODEGA</th><th>PRODUCTO</th>'
        '<th class="th-verde">VERDE<br><span>0–10 días</span></th>'
        '<th class="th-amarillo">AMARILLO<br><span>11–15 días</span></th>'
        '<th class="th-naranja">NARANJA<br><span>16–20 días</span></th>'
        '<th class="th-rojo">ROJO<br><span>21+ días</span></th>'
        f'<th>TOTAL ({e(unit.upper())})</th><th>CAPTURAS</th>'
    )
    body = []
    cards = []
    for row in report["rows"]:
        assert isinstance(row, dict)
        depot, product = e(row["warehouse"]), e(row["product"])
        vals = [_quantity(row[key], unit) for key in BUCKETS]
        body.append(
            '<tr>' + f'<td class="depot-cell">{depot}</td><td>{product_chip(str(row["product"]))}</td>'
            + ''.join(f'<td class="band-cell band-{key}">{v}</td>' for key, v in zip(BUCKETS, vals))
            + f'<td class="total-cell">{_quantity(row["total"], unit)}</td>'
            + f'<td class="count-cell">{int(row["entries"]):,}</td></tr>'
        )
        parts = ''.join(
            f'<div class="mobile-band band-{key}"><span>{label}</span><b>{v}</b></div>'
            for key, label, v in zip(BUCKETS, ("Verde · 0–10", "Amarillo · 11–15", "Naranja · 16–20", "Rojo · 21+"), vals)
        )
        cards.append(
            '<article class="inv-mobile-card">'
            f'<div class="inv-card-head"><b>{depot}</b>{product_chip(str(row["product"]))}</div>'
            f'<div class="inv-card-total">{_quantity(row["total"], unit)} <span>{e(unit)} · {int(row["entries"])} capturas</span></div>'
            f'<div class="mobile-bands">{parts}</div></article>'
        )
    totals = report["totals"]
    assert isinstance(totals, dict)
    footer = (
        '<tr class="inv-grand-total"><th colspan="2">TOTAL GENERAL</th>'
        + ''.join(f'<td>{_quantity(totals[key], unit)}</td>' for key in BUCKETS)
        + f'<td>{_quantity(totals["total"], unit)}</td><td>{report["count"]}</td></tr>'
    )
    return (
        '<div class="inv-report-desktop"><div class="inv-report-scroll">'
        '<table class="inv-report"><thead><tr>' + headers + '</tr></thead><tbody>'
        + ''.join(body) + footer + '</tbody></table></div></div>'
        '<div class="inv-report-mobile">' + ''.join(cards)
        + f'<div class="inv-mobile-total"><span>TOTAL GENERAL</span><strong>{_quantity(totals["total"], unit)} {e(unit)}</strong></div></div>'
    )


def supervisor_dashboard() -> None:
    supervisor_welcome()
    header, logout_col = st.columns([5, 1], vertical_alignment="center")
    with header:
        st.caption("Supervisor · Rudy Anavisca · Acceso a las tres bodegas")
    with logout_col:
        if st.button("Salir", key="top_exit_supervisor", use_container_width=True):
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
        weights = configured_weights(get_secret("PRODUCT_WEIGHT_KG", {}))
        with st.spinner("Consultando capturas de Supabase…"):
            records = entries_on_date(selected_day)
        report = build_daily_summary(records, selected_day, warehouse=selected_depot, weights_kg=weights)
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

    unit = str(report["unit"])
    metric1, metric2, metric3 = st.columns(3, gap="medium")
    for col, label, value, description in (
        (metric1, "CAPTURAS DEL DÍA", str(report["count"]), "Registros ingresados"),
        (metric2, "SACOS REGISTRADOS", f"{report['sacks']:,}", "Volumen capturado (no saldo)"),
        (metric3, "MÁS DE 10 DÍAS", _quantity(sum((report["totals"][key] for key in ("amarillo", "naranja", "rojo")), Decimal(0)), unit) + f" {unit}", "Al momento de la captura"),
    ):
        with col:
            st.markdown(f'<div class="dash-card"><div class="dash-label">{e(label)}</div>'
                        f'<div class="dash-value">{e(value)}</div><div class="dash-helper">{e(description)}</div></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(_report_html(report), unsafe_allow_html=True)
    if report["weights_missing"]:
        st.info(
            "El semáforo se presenta en **sacos**. Para mostrarlo en toneladas, configura el peso "
            "kg/saco de cada producto en PRODUCT_WEIGHT_KG (Streamlit Secrets). "
            "Faltan: " + ", ".join(report["weights_missing"]) + "."
        )
    st.caption("Verde: 0–10 días · Amarillo: 11–15 · Naranja: 16–20 · Rojo: 21 o más días. No se muestran pedidos: la base aún no tiene movimientos de salida.")

    summary_rows = [["Bodega", "Producto", "Verde", "Amarillo", "Naranja", "Rojo", f"Total ({unit})", "Capturas"]]
    for row in report["rows"]:
        summary_rows.append([row["warehouse"], row["product"], *(_quantity(row[key], unit) for key in BUCKETS), _quantity(row["total"], unit), row["entries"]])
    summary_rows.append(["TOTAL GENERAL", "", *(_quantity(report["totals"][key], unit) for key in BUCKETS), _quantity(report["totals"]["total"], unit), report["count"]])
    st.download_button("Descargar semáforo (CSV)", data=_csv_text(summary_rows), file_name=f"semaforo_capturas_{selected_day.isoformat()}.csv", mime="text/csv", use_container_width=True)

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
        if st.button("Salir", key="top_exit_operator", use_container_width=True):
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
