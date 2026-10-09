# ARGOS Guatemala — Agrupar semáforo por bodega

## Archivos para reemplazar en GitHub Web

1. `app.py` — reemplazar el archivo de la raíz del repositorio.
2. `src/style.py` — reemplazar el archivo dentro de la carpeta `src`.

En GitHub Web abre cada archivo, pulsa Edit (lápiz), pega el contenido de su archivo nuevo y confirma el cambio en `main`. Puedes subir los archivos por el navegador conservando las carpetas respectivas. Streamlit desplegará el último commit automáticamente.

**No ejecutar SQL ni modificar Secrets.** El cambio solo afecta la representación del semáforo.

## Comportamiento

- Cada bodega aparece **una sola vez** en la tabla grande, centrada vertical y horizontalmente, en una celda que ocupa todas sus filas de producto.
- Los productos y sus cifras continúan en filas individuales.
- En smartphone, cada bodega aparece como un encabezado único sobre sus tarjetas de productos.
- Se mantiene la fila TOTAL GENERAL, sacos, toneladas y las columnas PEDIDOS/PEDIDOS (TON) vacías, pendientes de Odoo.
- El exportador CSV conserva una fila por bodega/producto, por lo que seguirá repitiendo BODEGA en el CSV para permitir filtrado en Excel. La combinación de celdas solo es visual en la tabla web.
