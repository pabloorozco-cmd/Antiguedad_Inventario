[LEEME_ACTUALIZACION.md](https://github.com/user-attachments/files/33229760/LEEME_ACTUALIZACION.md)
# ARGOS Guatemala — Colores Odoo en el semáforo

## Archivos modificados

1. `app.py` — reemplaza el archivo principal en la raíz del repositorio.
2. `src/style.py` — reemplaza el archivo ubicado en la carpeta `src`.

## Qué cambia

- Encabezados **PEDIDOS** y **PEDIDOS (TON)** con fondo morado Odoo `#A24689` (extraído de la imagen de referencia) y texto blanco.
- Celdas de ambas columnas con fondo lavanda suave y separación morada respecto a TOTAL (TON).
- Las celdas Odoo de **SUBTOTAL** y **TOTAL GENERAL** mantienen la identificación morada con tonos adecuados a cada fila.
- En smartphones y tabletas pequeñas, las fichas Odoo muestran el mismo lenguaje visual, incluyendo subtotales por bodega.
- Las celdas permanecen en blanco hasta la futura integración de pedidos y toneladas de Odoo.
- Sin cambios en los cálculos de sacos/toneladas, clasificación por antigüedad, captura, bodega, CSV ni consultas Supabase.

## Cómo subirlo desde GitHub Web

1. Descomprime el ZIP.
2. Abre tu repositorio `pabloorozco-cmd/Antiguedad_Inventario` en GitHub Web, rama `main`.
3. En `app.py`, pulsa **Edit this file** y reemplaza todo su contenido por el archivo `app.py` del ZIP; haz commit.
4. Repite en `src/style.py` con el archivo `src/style.py` del ZIP; haz commit.
5. Streamlit Community Cloud debería redesplegar. Refresca la página, de ser necesario con `Ctrl+F5`.

No hace falta actualizar SQL, modificar las tablas Supabase ni los Streamlit Secrets.

**Nota de alcance:** `PEDIDOS` y `PEDIDOS (TON)` son campos futuros de Odoo y se muestran vacíos; no se han conectado datos del ERP.
