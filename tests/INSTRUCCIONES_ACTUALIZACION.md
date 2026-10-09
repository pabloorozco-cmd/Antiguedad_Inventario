# ARGOS Guatemala — Ajuste del semáforo del supervisor

## Archivos que debes reemplazar en GitHub Web

- `app.py`
- `src/report.py`
- `src/style.py`
- `tests/test_report.py` (pruebas automatizadas; recomendable subirlo)

No se cambian formularios, usuarios, acceso, tablas SQL ni credenciales.

## Cambios

1. Tabla del supervisor con fuentes mayores, anchos equilibrados, encabezados en dos líneas y desplazamiento horizontal únicamente cuando hace falta. En teléfono se usan tarjetas.
2. Eliminada la tarjeta **Capturas del día** y la columna **Capturas** del reporte y del CSV.
3. Añadida **TOTAL (TON)** a la derecha de **TOTAL (SACOS)**.
4. Conversión **toneladas = sacos × 0.0425**, con redondeo comercial al entero más cercano (0.5 hacia arriba). Se aplica igual a todos los productos, incluidos PL. El total general se calcula desde la suma de sacos y después se redondea; puede no coincidir con la suma de cifras de filas ya redondeadas.
5. Añadidas las columnas **PEDIDOS** y **PEDIDOS (TON)**, vacías hasta que se implemente la integración con Odoo.
6. Reemplazada la tarjeta removida por **Toneladas registradas**, para mantener las tres métricas visuales.

**Alcance:** el reporte conserva la fecha de captura y muestra registros de ingresos, no inventario disponible neto (no existen movimientos de salida).

## Subir sin GitHub Desktop

1. Descomprime el ZIP.
2. En GitHub Web abre tu repositorio en la rama `main`.
3. En `app.py` y los archivos dentro de `src/` y `tests/`, reemplaza cada archivo manteniendo exactamente su ubicación. Puedes hacerlo con **Add file → Upload files** respetando las carpetas, o usando el editor web (ícono lápiz) en cada archivo.
4. Confirma el commit. Streamlit Community Cloud debería redesplegar automáticamente.
5. Entra como Rudy y revisa el semáforo y el CSV.

No ejecutes SQL ni cambies **Secrets** para esta actualización.
